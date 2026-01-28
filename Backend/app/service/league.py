from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
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
            budget=200.0, 
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
