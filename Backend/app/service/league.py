from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models.league import League, LeagueMember, Roster
from app.db.models.professional import Player
from app.core.exceptions import AppError
from app.core.constants import ErrorCode
from app.core.decorators import transactional
from app.repository.league import LeagueRepository, LeagueMemberRepository, RosterRepository
from app.repository.professional import PlayerRepository
import uuid

class LeagueService:
    '''
    Servicio que maneja la lógica de negocio de ligas.
    
    Responsabilidades:
    - Generación de códigos de invitación únicos
    - Validación de límites de equipos
    - CRUD con validaciones de negocio
    '''
    def __init__(self, db: Session):
        self.db = db
        self.repo = LeagueRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[League]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, league_id: int) -> Optional[League]:
        league = self.repo.get_by_id(league_id)
        if not league:
            raise AppError(404, ErrorCode.NOT_FOUND, "La liga no existe")
        return league

    def get_by_invite_code(self, invite_code: str) -> Optional[League]:
        league = self.repo.get_by_invite_code(invite_code)
        if not league:
            raise AppError(404, ErrorCode.NOT_FOUND, "Código de invitación inválido")
        return league

    def get_by_admin(self, admin_user_id: int) -> List[League]:
        return self.repo.get_by_admin(admin_user_id)

    @transactional
    def create(self, *, name: str, admin_user_id: int, max_teams: int = 10) -> League:
        '''
        Crea una nueva liga con código de invitación único.
        Añade automáticamente al creador como el primer miembro (Admin de la liga).
        '''
        # Generar código único
        invite_code = str(uuid.uuid4())[:8].upper()
        
        # Verificar que el código sea único
        while self.repo.get_by_invite_code(invite_code):
            invite_code = str(uuid.uuid4())[:8].upper()
        
        # 1. Crear liga
        league = League(
            name=name,
            admin_user_id=admin_user_id,
            invite_code=invite_code,
            max_teams=max_teams
        )
        created_league = self.repo.create(league)
        
        # 2. Añadir al creador como miembro automáticamente
        # No usamos el member_service para evitar dependencias circulares complejas
        # lo hacemos directo con el repositorio o una instancia interna
        # Pero mejor, usemos una instancia de LeagueMemberRepository aquí
        member_repo = LeagueMemberRepository(self.db)
        member = LeagueMember(
            league_id=created_league.id,
            user_id=admin_user_id,
            team_name=f"Equipo de {name}", # Nombre por defecto
            budget=200.0,
            is_admin=True # El creador es admin de la liga
        )
        member_repo.create(member)
        
        return created_league

    @transactional
    def update(self, league_id: int, league_data: dict) -> League:
        '''
        Actualiza una liga.
        '''
        league = self.repo.get_by_id(league_id)
        if not league:
            raise AppError(404, ErrorCode.NOT_FOUND, "La liga no existe")
        
        return self.repo.update(league_id, league_data)

    @transactional
    def delete(self, league_id: int) -> None:
        league = self.repo.get_by_id(league_id)
        if not league:
            raise AppError(404, ErrorCode.NOT_FOUND, "La liga no existe")
        
        self.repo.delete(league)


class LeagueMemberService:
    '''
    Servicio que maneja la lógica de negocio de miembros de liga.
    
    Responsabilidades:
    - Validación de límites de equipos en liga
    - Validación de duplicados (usuario ya en liga)
    - Gestión de presupuesto
    - CRUD con validaciones de negocio
    '''
    def __init__(self, db: Session):
        self.db = db
        self.repo = LeagueMemberRepository(db)
        self.league_repo = LeagueRepository(db)

    def get_by_id(self, member_id: int) -> Optional[LeagueMember]:
        member = self.repo.get_by_id(member_id)
        if not member:
            raise AppError(404, ErrorCode.NOT_FOUND, "Miembro no encontrado")
        return member

    def get_by_league(self, league_id: int) -> List[LeagueMember]:
        return self.repo.get_by_league(league_id)

    def get_by_user(self, user_id: int) -> List[LeagueMember]:
        return self.repo.get_by_user_with_league(user_id)

    def get_league_rankings(self, league_id: int) -> List[LeagueMember]:
        '''Obtiene el ranking de una liga ordenado por puntos totales incluyendo el valor del equipo'''
        members = self.repo.get_league_rankings_with_user(league_id)
        
        # Calcular el valor del equipo para cada miembro
        for member in members:
            # Sumar el precio actual de todos los jugadores en su roster
            total_value = sum(entry.player.current_price for entry in member.roster if entry.player)
            member.team_value = total_value

        # Ordenar por total_points descendente
        return sorted(members, key=lambda m: m.total_points, reverse=True)

    @transactional
    def join_league(self, *, league_id: int, user_id: int, team_name: str, 
                   selected_team_id: Optional[int] = None) -> LeagueMember:
        '''
        Añade un usuario a una liga validando límites y duplicados.
        '''
        # Verificar que la liga existe
        league = self.league_repo.get_by_id(league_id)
        if not league:
            raise AppError(404, ErrorCode.NOT_FOUND, "La liga no existe")
        
        # Verificar que el usuario no esté ya en la liga
        existing = self.repo.get_by_league_and_user(league_id, user_id)
        if existing:
            raise AppError(409, ErrorCode.ALREADY_IN_LEAGUE, "Ya eres miembro de esta liga")
        
        # Verificar límite de equipos
        current_members = self.repo.get_by_league(league_id)
        if len(current_members) >= league.max_teams:
            raise AppError(400, ErrorCode.LEAGUE_FULL, "La liga está llena")
        
        # Crear miembro
        member = LeagueMember(
            league_id=league_id,
            user_id=user_id,
            team_name=team_name,
            selected_team_id=selected_team_id,
            budget=150.0,  # Presupuesto inicial consistente
            is_admin=False
        )
        return self.repo.create(member)

    @transactional
    def update(self, member_id: int, member_data: dict) -> LeagueMember:
        '''
        Actualiza un miembro de liga (cambiar nombre de equipo, equipo profesional, etc).
        '''
        member = self.repo.get_by_id(member_id)
        if not member:
            raise AppError(404, ErrorCode.NOT_FOUND, "Miembro no encontrado")
        
        # Validar que el presupuesto no sea negativo
        if 'budget' in member_data and member_data['budget'] is not None:
            if member_data['budget'] < 0:
                raise AppError(400, ErrorCode.INVALID_INPUT, "El presupuesto no puede ser negativo")
        
        return self.repo.update(member_id, member_data)

    @transactional
    def leave_league(self, member_id: int) -> None:
        '''Elimina un miembro de una liga'''
        member = self.repo.get_by_id(member_id)
        if not member:
            raise AppError(404, ErrorCode.NOT_FOUND, "Miembro no encontrado")
        
        self.repo.delete(member)


class RosterService:
    '''
    Servicio que maneja la lógica de negocio de rosters (equipos de usuarios).
    
    Responsabilidades:
    - Validación de límites (8 titulares, 3 suplentes)
    - Validación de presupuesto
    - Validación de duplicados (mismo jugador)
    - CRUD con validaciones de negocio
    '''
    def __init__(self, db: Session):
        self.db = db
        self.repo = RosterRepository(db)
        self.member_repo = LeagueMemberRepository(db)
        self.player_repo = PlayerRepository(db)

    def get_by_league_member(self, league_member_id: int) -> List[Roster]:
        return self.repo.get_by_league_member(league_member_id)

    def get_starters(self, league_member_id: int) -> List[Roster]:
        return self.repo.get_starters_by_league_member(league_member_id)

    def get_bench(self, league_member_id: int) -> List[Roster]:
        return self.repo.get_bench_by_league_member(league_member_id)

    @transactional
    def add_player(self, *, league_member_id: int, player_id: int, 
                   is_starter: bool = False, is_bench: bool = False,
                   role_position: Optional[str] = None) -> Roster:
        '''
        Añade un jugador al roster validando límites y presupuesto.
        '''
        # Verificar que el miembro existe
        member = self.member_repo.get_by_id(league_member_id)
        if not member:
            raise AppError(404, ErrorCode.NOT_FOUND, "Miembro no encontrado")
        
        # Verificar que el jugador existe
        player = self.player_repo.get_by_id(player_id)
        if not player:
            raise AppError(404, ErrorCode.NOT_FOUND, "Jugador no encontrado")
        
        # Verificar que el jugador no esté ya en el roster
        existing = self.repo.get_by_player_and_member(league_member_id, player_id)
        if existing:
            raise AppError(409, ErrorCode.PLAYER_ALREADY_IN_ROSTER, "El jugador ya está en tu roster")
        
        # Validar límites de titulares y suplentes
        current_roster = self.repo.get_by_league_member(league_member_id)
        starters_count = sum(1 for r in current_roster if r.is_starter)
        bench_count = sum(1 for r in current_roster if r.is_bench)
        
        if is_starter and starters_count >= 8:
            raise AppError(400, ErrorCode.ROSTER_LIMIT_REACHED, "Ya tienes 8 titulares")
        
        if is_bench and bench_count >= 3:
            raise AppError(400, ErrorCode.ROSTER_LIMIT_REACHED, "Ya tienes 3 suplentes")

        # 1. Validar Límite por Equipo (Max 2 del mismo equipo real)
        same_team_count = sum(1 for r in current_roster if self.player_repo.get_by_id(r.player_id).team_id == player.team_id)
        if same_team_count >= 2:
            team_name = player.team.name if player.team else "Independiente"
            raise AppError(400, ErrorCode.SAME_TEAM_LIMIT_REACHED, 
                          f"No puedes tener más de 2 jugadores del mismo equipo ({team_name})")

        # 2. Validar Límite por Rol para titulares
        if is_starter:
            # Contar jugadores actuales por rol en el equipo titular
            role_counts = {"Duelist": 0, "Sentinel": 0, "Initiator": 0, "Controller": 0}
            for entry in current_roster:
                if entry.is_starter:
                    p = self.player_repo.get_by_id(entry.player_id)
                    if p.role in role_counts:
                        role_counts[p.role] += 1
            
            # Verificar si el nuevo jugador cabe en su rol (Max 2)
            if player.role in role_counts and role_counts[player.role] >= 2:
                raise AppError(400, ErrorCode.ROLE_LIMIT_REACHED, 
                              f"Ya tienes el máximo de 2 {player.role}s en el equipo titular")

        # 3. Validar presupuesto y persistir gasto
        if player.current_price > member.budget:
            raise AppError(400, ErrorCode.INSUFFICIENT_BUDGET, 
                          f"No tienes suficiente presupuesto. Coste: {player.current_price}, Disponible: {member.budget}")
        
        # Descontar presupuesto del miembro
        self.member_repo.update(league_member_id, {"budget": member.budget - player.current_price})
        
        # Calcular valor total del equipo para registro
        current_total_value = sum(self.player_repo.get_by_id(r.player_id).current_price for r in current_roster)
        new_total_value = current_total_value + player.current_price

        # Crear entrada en roster
        roster = Roster(
            league_member_id=league_member_id,
            player_id=player_id,
            is_starter=is_starter,
            is_bench=is_bench,
            role_position=role_position or player.role,
            total_value_team=new_total_value
        )
        return self.repo.create(roster)

    @transactional
    def remove_player(self, roster_id: int) -> None:
        '''Elimina un jugador del roster y devuelve el dinero al presupuesto'''
        roster = self.repo.get_by_id(roster_id)
        if not roster:
            raise AppError(404, ErrorCode.NOT_FOUND, "Jugador no encontrado en roster")
        
        # Obtener datos del miembro y el jugador
        member = self.member_repo.get_by_id(roster.league_member_id)
        player = self.player_repo.get_by_id(roster.player_id)
        
        # Reembolsar precio al presupuesto
        self.member_repo.update(member.id, {"budget": member.budget + player.current_price})
        
        self.repo.delete(roster)

    @transactional
    def update_roster_entry(self, roster_id: int, roster_data: dict) -> Roster:
        '''Actualiza una entrada del roster (cambiar titular/suplente, etc)'''
        roster = self.repo.get_by_id(roster_id)
        if not roster:
            raise AppError(404, ErrorCode.NOT_FOUND, "Jugador no encontrado en roster")
        
        return self.repo.update(roster_id, roster_data)
