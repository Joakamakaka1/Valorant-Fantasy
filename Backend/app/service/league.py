from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional, Tuple
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
    Servicio que maneja la lógica de negocio de ligas (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LeagueRepository(db)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[League]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_by_id(self, league_id: int) -> Optional[League]:
        league = await self.repo.get(league_id)
        if not league:
            raise AppError(404, ErrorCode.NOT_FOUND, "La liga no existe")
        return league

    async def get_by_invite_code(self, invite_code: str) -> Optional[League]:
        league = await self.repo.get_by_invite_code(invite_code)
        if not league:
            raise AppError(404, ErrorCode.NOT_FOUND, "Código de invitación inválido")
        return league

    async def get_by_admin(self, admin_user_id: int) -> List[League]:
        return await self.repo.get_by_admin(admin_user_id)

    @transactional
    async def create(self, *, name: str, admin_user_id: int, max_teams: int = 10) -> League:
        invite_code = str(uuid.uuid4())[:8].upper()
        while await self.repo.get_by_invite_code(invite_code):
            invite_code = str(uuid.uuid4())[:8].upper()

        league = League(
            name=name, 
            admin_user_id=admin_user_id,
            invite_code=invite_code, 
            max_teams=max_teams
        )
        
        created_league = await self.repo.create(league, options=[joinedload(League.admin_user)])
        
        member_repo = LeagueMemberRepository(self.db)
        member = LeagueMember(
            league_id=created_league.id, 
            user_id=admin_user_id,
            team_name=f"Equipo de {name}", 
            budget=50.0, 
            is_admin=True
        )
        await member_repo.create(member)
        
        return created_league

    @transactional
    async def update(self, league_id: int, league_data: dict) -> League:
        if not await self.repo.get(league_id):
            raise AppError(404, ErrorCode.NOT_FOUND, "La liga no existe")
        return await self.repo.update(league_id, league_data)

    @transactional
    async def delete(self, league_id: int) -> None:
        if not await self.repo.delete(league_id):
             raise AppError(404, ErrorCode.NOT_FOUND, "La liga no existe")


class LeagueMemberService:
    '''
    Servicio que maneja la lógica de negocio de miembros de liga (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LeagueMemberRepository(db)
        self.league_repo = LeagueRepository(db)

    async def get_by_id(self, member_id: int) -> Optional[LeagueMember]:
        # Inject eager loading here
        member = await self.repo.get(member_id, options=[joinedload(LeagueMember.user)])
        if not member:
            raise AppError(404, ErrorCode.NOT_FOUND, "Miembro no encontrado")
        return member

    async def get_by_league(self, league_id: int) -> List[LeagueMember]:
        # Inject eager loading here
        return await self.repo.get_by_league(league_id, options=[joinedload(LeagueMember.user)])

    async def get_by_user(self, user_id: int) -> List[LeagueMember]:
        return await self.repo.get_by_user_with_league(user_id)

    async def get_league_rankings(self, league_id: int) -> List[LeagueMember]:
        members = await self.repo.get_league_rankings_with_user(league_id)
        for member in members:
            total_value = sum(entry.player.current_price for entry in member.roster if entry.player)
            member.team_value = total_value
        return sorted(members, key=lambda m: m.total_points, reverse=True)

    @transactional
    async def join_league(self, *, league_id: int, user_id: int, team_name: str, 
                         selected_team_id: Optional[int] = None) -> LeagueMember:
        league = await self.league_repo.get(league_id)
        if not league:
            raise AppError(404, ErrorCode.NOT_FOUND, "La liga no existe")
        
        if await self.repo.get_by_league_and_user(league_id, user_id):
            raise AppError(409, ErrorCode.ALREADY_IN_LEAGUE, "Ya eres miembro de esta liga")
        
        current_members = await self.repo.get_by_league(league_id)
        if len(current_members) >= league.max_teams:
            raise AppError(400, ErrorCode.LEAGUE_FULL, "La liga está llena")
        
        member = LeagueMember(
            league_id=league_id, user_id=user_id, team_name=team_name,
            selected_team_id=selected_team_id, budget=150.0, is_admin=False
        )
        
        return await self.repo.create(member, options=[joinedload(LeagueMember.user)])
    
    @transactional
    async def create_member_with_draft(
        self, 
        league_id: int, 
        user_id: int, 
        team_name: str,
        selected_team_id: Optional[int] = None
    ) -> LeagueMember:
        """
        Crea un miembro de liga y le asigna 11 jugadores aleatorios con balance de roles.
        
        Proceso:
        1. Validar que la liga existe y no está llena
        2. Validar que el usuario no es ya miembro
        3. Crear LeagueMember con budget=50.0
        4. Obtener pool de jugadores disponibles
        5. Asignar 11 jugadores aleatorios (valor: 185-210M)
           - 2 Duelists, 2 Initiators, 2 Controllers, 2 Sentinels, 3 Flex
        6. Crear Roster entries
        """
        import random
        from app.db.models.professional import Player
        from app.core.logging_config import logger
        
        # 1. Validar liga
        league = await self.league_repo.get(league_id)
        if not league:
            raise AppError(404, ErrorCode.NOT_FOUND, "La liga no existe")
        
        # 2. Validar que usuario no es ya miembro
        if await self.repo.get_by_league_and_user(league_id, user_id):
            raise AppError(409, ErrorCode.ALREADY_IN_LEAGUE, "Ya eres miembro de esta liga")
        
        # 3. Validar que la liga no está llena
        current_members = await self.repo.get_by_league(league_id)
        if len(current_members) >= league.max_teams:
            raise AppError(400, ErrorCode.LEAGUE_FULL, "La liga está llena")
        
        # 4. Crear LeagueMember
        member = LeagueMember(
            league_id=league_id,
            user_id=user_id,
            team_name=team_name,
            selected_team_id=selected_team_id,
            budget=50.0,  # Budget inicial: 50M
            total_points=0.0,
            is_admin=False
        )
        self.db.add(member)
        await self.db.flush()  # Para obtener member.id
        
        # 5. Obtener pool de jugadores disponibles
        query = select(Player).where(
            Player.current_price > 0,
            Player.matches_played > 0
        )
        result = await self.db.execute(query)
        available_players = list(result.scalars().all())
        
        if len(available_players) < 11:
            raise AppError(
                500, 
                ErrorCode.INTERNAL_ERROR, 
                f"No hay suficientes jugadores para draft (encontrados {len(available_players)})"
            )
        
        # 6. Ejecutar draft aleatorio con balance de roles
        starters, bench = await self._assign_random_team_with_roles(
            available_players, 
            target_value=197.5  # Rango objetivo: 185-210M
        )
        
        # 7. Crear Roster entries con separación starter/bench y labels únicos
        total_team_value = 0.0
        roster_repo = RosterRepository(self.db)
        
        # Mapeo de slots del frontend (debe coincidir con roster-view.tsx)
        SLOT_LABELS = {
            "Duelist": ["Duelist 1", "Duelist 2"],
            "Initiator": ["Initiator 1", "Initiator 2"],
            "Controller": ["Controller 1", "Controller 2"],
            "Sentinel": ["Sentinel 1", "Sentinel 2"],
            "Flex": ["Bench 1", "Bench 2", "Bench 3"]
        }
        
        # Contador para asignar labels únicos por rol
        role_counters = {
            "Duelist": 0,
            "Initiator": 0,
            "Controller": 0,
            "Sentinel": 0,
            "Flex": 0
        }
        
        # Crear entries para STARTERS (8 jugadores con roles específicos)
        for player in starters:
            role = player.role
            label = SLOT_LABELS[role][role_counters[role]]
            role_counters[role] += 1
            
            roster_entry = Roster(
                league_member_id=member.id,
                player_id=player.id,
                is_starter=True,
                is_bench=False,
                role_position=label,  # Asignar label único: "Duelist 1", "Duelist 2", etc.
                total_value_team=0.0
            )
            self.db.add(roster_entry)
            total_team_value += player.current_price
        
        # Crear entries para BENCH (3 jugadores Flex)
        for player in bench:
            label = SLOT_LABELS["Flex"][role_counters["Flex"]]
            role_counters["Flex"] += 1
            
            roster_entry = Roster(
                league_member_id=member.id,
                player_id=player.id,
                is_starter=False,
                is_bench=True,
                role_position=label,  # Asignar label: "Bench 1", "Bench 2", "Bench 3"
                total_value_team=0.0
            )
            self.db.add(roster_entry)
            total_team_value += player.current_price
        
        logger.info(
            f"Draft completado para '{team_name}': 8 titulares + 3 suplentes, "
            f"{total_team_value:.2f}M valor, 50M budget"
        )
        
        # Refrescar member para incluir relaciones
        await self.db.refresh(member, ["user"])
        return member
    
    async def _assign_random_team_with_roles(
        self,
        available_players: List[Player],
        target_value: float = 197.5
    ) -> Tuple[List[Player], List[Player]]:
        """
        Asigna 11 jugadores con balance de roles:
        
        STARTERS (8 jugadores):
        - 2 Duelists
        - 2 Initiators
        - 2 Controllers
        - 2 Sentinels
        
        BENCH (3 jugadores):
        - 3 Flex (cualquier rol)
        
        Valor total: 185-210M
        
        Returns:
            Tuple[starters, bench] donde starters son 8 jugadores y bench son 3
        """
        import random
        from app.core.logging_config import logger
        
        MAX_ITERATIONS = 100
        
        # Clasificar jugadores por rol Y precio
        players_by_role = {
            "Duelist": [p for p in available_players if p.role == "Duelist"],
            "Initiator": [p for p in available_players if p.role == "Initiator"],
            "Controller": [p for p in available_players if p.role == "Controller"],
            "Sentinel": [p for p in available_players if p.role == "Sentinel"],
        }
        
        for attempt in range(MAX_ITERATIONS):
            starters = []
            bench = []
            total_value = 0.0
            
            try:
                # PASO 1: Seleccionar 2 de cada rol (8 STARTERS)
                for role, count in [("Duelist", 2), ("Initiator", 2), ("Controller", 2), ("Sentinel", 2)]:
                    role_pool = players_by_role.get(role, [])
                    if len(role_pool) < count:
                        # No hay suficientes jugadores de este rol, saltar iteración
                        raise ValueError(f"No hay suficientes {role}")
                    
                    # Ordenar por precio y tomar mix de caros/baratos
                    role_pool_sorted = sorted(role_pool, key=lambda p: p.current_price, reverse=True)
                    
                    # Seleccionar 2: 1 del top 30% y 1 aleatorio del resto
                    top_30_percent = max(1, len(role_pool_sorted) // 3)
                    
                    # Primer jugador del top
                    pick1 = random.choice(role_pool_sorted[:top_30_percent])
                    starters.append(pick1)
                    total_value += pick1.current_price
                    
                    # Segundo jugador del resto (excluyendo el ya elegido)
                    remaining = [p for p in role_pool if p.id != pick1.id]
                    if remaining:
                        pick2 = random.choice(remaining)
                        starters.append(pick2)
                        total_value += pick2.current_price
                
                # PASO 2: Seleccionar 3 FLEX para BENCH (cualquier rol, priorizando acercarse al target)
                remaining_pool = [p for p in available_players if p not in starters]
                if len(remaining_pool) < 3:
                    raise ValueError("No hay suficientes jugadores para bench")
                
                # Calcular cuánto presupuesto queda para los 3 flex
                remaining_budget = target_value - total_value
                target_per_flex = remaining_budget / 3
                
                # Ordenar por cercanía al target_per_flex
                remaining_sorted = sorted(
                    remaining_pool,
                    key=lambda p: abs(p.current_price - target_per_flex)
                )
                
                # Tomar los 3 mejores matches para bench
                for i in range(3):
                    if i < len(remaining_sorted):
                        bench.append(remaining_sorted[i])
                        total_value += remaining_sorted[i].current_price
                
                # PASO 3: Validar restricciones (rango 185-210M)
                if len(starters) == 8 and len(bench) == 3 and 185.0 <= total_value <= 210.0:
                    logger.debug(
                        f"Equipo ensamblado en {attempt+1} intentos: {total_value:.2f}M, "
                        f"8 starters + 3 bench"
                    )
                    return (starters, bench)
            
            except ValueError:
                # No se pudo con esta combinación, intentar de nuevo
                continue
        
        # FALLBACK: Estrategia greedy sin balance de roles
        logger.warning(f"No se pudo ensamblar con balance de roles en {MAX_ITERATIONS} intentos. Usando fallback.")
        return await self._greedy_team_assembly(available_players, target_value)
    
    async def _greedy_team_assembly(
        self, 
        available_players: List[Player], 
        target_value: float
    ) -> Tuple[List[Player], List[Player]]:
        """
        Estrategia greedy de fallback sin balance de roles.
        Retorna: (starters, bench) donde starters son los primeros 8 y bench los últimos 3.
        """
        import random
        from app.core.logging_config import logger
        
        sorted_players = sorted(available_players, key=lambda p: p.current_price, reverse=True)
        
        selected = []
        total_value = 0.0
        
        # 1. Tomar 1-2 jugadores TOP (>= 45M) máximo
        top_count = 0
        max_tops = random.choice([1, 2])  # Aleatorio entre 1 y 2 tops
        
        for player in sorted_players[:]:
            if player.current_price >= 45.0 and top_count < max_tops:
                selected.append(player)
                total_value += player.current_price
                sorted_players = [p for p in sorted_players if p.id != player.id]
                top_count += 1
                if top_count >= max_tops:
                    break
        
        # 2. Llenar por cercanía al promedio objetivo
        remaining_slots = 11 - len(selected)
        if remaining_slots > 0:
            target_per_player = (target_value - total_value) / remaining_slots
            sorted_by_fit = sorted(sorted_players, key=lambda p: abs(p.current_price - target_per_player))
            
            for player in sorted_by_fit:
                if len(selected) >= 11:
                    break
                if total_value + player.current_price <= target_value + 15:
                    selected.append(player)
                    total_value += player.current_price
        
        # 3. Rellenar con baratos si faltan
        if len(selected) < 11:
            remaining = [p for p in available_players if p not in selected]
            remaining_sorted = sorted(remaining, key=lambda p: p.current_price)
            for player in remaining_sorted:
                if len(selected) >= 11:
                    break
                selected.append(player)
                total_value += player.current_price
        
        logger.info(f"Greedy fallback: {total_value:.2f}M ({len(selected)} jugadores)")
        
        # Dividir en starters (primeros 8) y bench (últimos 3)
        final_team = selected[:11]
        starters = final_team[:8]
        bench = final_team[8:11]
        
        return (starters, bench)


    @transactional
    async def update(self, member_id: int, member_data: dict) -> LeagueMember:
        if not await self.repo.get(member_id):
            raise AppError(404, ErrorCode.NOT_FOUND, "Miembro no encontrado")
        
        if 'budget' in member_data and member_data['budget'] is not None:
            if member_data['budget'] < 0:
                raise AppError(400, ErrorCode.INVALID_INPUT, "El presupuesto no puede ser negativo")
        
        # We generally want to return the full object with user for consistency, OR caller re-fetches. 
        # But update returns the object. Let's include options.
        return await self.repo.update(member_id, member_data, options=[joinedload(LeagueMember.user)])

    @transactional
    async def leave_league(self, member_id: int) -> None:
        if not await self.repo.delete(member_id):
             raise AppError(404, ErrorCode.NOT_FOUND, "Miembro no encontrado")


class RosterService:
    '''
    Servicio que maneja la lógica de negocio de rosters (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = RosterRepository(db)
        self.member_repo = LeagueMemberRepository(db)
        self.player_repo = PlayerRepository(db)

    async def get_by_league_member(self, league_member_id: int) -> List[Roster]:
        return await self.repo.get_by_league_member(league_member_id)

    async def get_starters(self, league_member_id: int) -> List[Roster]:
        return await self.repo.get_starters_by_league_member(league_member_id)

    async def get_bench(self, league_member_id: int) -> List[Roster]:
        return await self.repo.get_bench_by_league_member(league_member_id)

    @transactional
    async def add_player(self, *, league_member_id: int, player_id: int, 
                   is_starter: bool = False, is_bench: bool = False,
                   role_position: Optional[str] = None) -> Roster:
        member = await self.member_repo.get(league_member_id)
        if not member:
            raise AppError(404, ErrorCode.NOT_FOUND, "Miembro no encontrado")
        
        player = await self.player_repo.get_by_id(player_id)
        if not player:
            raise AppError(404, ErrorCode.NOT_FOUND, "Jugador no encontrado")
        
        if await self.repo.get_by_player_and_member(league_member_id, player_id):
            raise AppError(409, ErrorCode.PLAYER_ALREADY_IN_ROSTER, "El jugador ya está en tu roster")
        
        current_roster = await self.repo.get_by_league_member(league_member_id)
        starters_count = sum(1 for r in current_roster if r.is_starter)
        bench_count = sum(1 for r in current_roster if r.is_bench)
        
        if is_starter and starters_count >= 8:
            raise AppError(400, ErrorCode.ROSTER_LIMIT_REACHED, "Ya tienes 8 titulares")
        if is_bench and bench_count >= 3:
            raise AppError(400, ErrorCode.ROSTER_LIMIT_REACHED, "Ya tienes 3 suplentes")

        # 1. Validar Límite por Equipo
        same_team_count = 0
        for r in current_roster:
            p = await self.player_repo.get_by_id(r.player_id)
            if p and p.team_id == player.team_id:
                same_team_count += 1
        
        if same_team_count >= 2:
            team_name = player.team.name if player.team else "Independiente"
            raise AppError(400, ErrorCode.SAME_TEAM_LIMIT_REACHED, 
                          f"No puedes tener más de 2 jugadores del mismo equipo ({team_name})")

        # 2. Validar Límite por Rol
        if is_starter:
            role_counts = {"Duelist": 0, "Sentinel": 0, "Initiator": 0, "Controller": 0}
            for entry in current_roster:
                if entry.is_starter:
                    p = await self.player_repo.get_by_id(entry.player_id)
                    if p and p.role in role_counts:
                        role_counts[p.role] += 1
            
            if player.role in role_counts and role_counts[player.role] >= 2:
                raise AppError(400, ErrorCode.ROLE_LIMIT_REACHED, 
                              f"Ya tienes el máximo de 2 {player.role}s en el equipo titular")

        # 3. Validar presupuesto
        if player.current_price > member.budget:
            raise AppError(400, ErrorCode.INSUFFICIENT_BUDGET, 
                          f"No tienes suficiente presupuesto. Coste: {player.current_price}, Disponible: {member.budget}")
        
        await self.member_repo.update(league_member_id, {"budget": member.budget - player.current_price})
        
        current_total_value = 0
        for r in current_roster:
            p = await self.player_repo.get_by_id(r.player_id)
            if p: current_total_value += p.current_price
            
        new_total_value = current_total_value + player.current_price

        roster = Roster(
            league_member_id=league_member_id, player_id=player_id,
            is_starter=is_starter, is_bench=is_bench,
            role_position=role_position or player.role, total_value_team=new_total_value
        )
        return await self.repo.create(roster)

    @transactional
    async def remove_player(self, roster_id: int) -> None:
        roster = await self.repo.get(roster_id)
        if not roster:
            raise AppError(404, ErrorCode.NOT_FOUND, "Jugador no encontrado en roster")
        
        member = await self.member_repo.get(roster.league_member_id)
        player = await self.player_repo.get_by_id(roster.player_id)
        
        await self.member_repo.update(member.id, {"budget": member.budget + player.current_price})
        await self.repo.delete(roster.id)

    @transactional
    async def update_roster_entry(self, roster_id: int, roster_data: dict) -> Roster:
        if not await self.repo.get(roster_id):
            raise AppError(404, ErrorCode.NOT_FOUND, "Jugador no encontrado en roster")
        return await self.repo.update(roster_id, roster_data)
