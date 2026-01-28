from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.league import League, LeagueMember, Roster
from typing import List, Optional
from app.repository.base import BaseRepository

class LeagueRepository(BaseRepository[League]):
    '''
    Repositorio de ligas - Capa de acceso a datos (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        super().__init__(League, db)

    async def get_by_invite_code(self, invite_code: str) -> Optional[League]:
        query = select(League).where(League.invite_code == invite_code)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_admin(self, admin_user_id: int) -> List[League]:
        query = select(League).where(League.admin_user_id == admin_user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> List[League]:
        query = select(League).where(League.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class LeagueMemberRepository(BaseRepository[LeagueMember]):
    '''
    Repositorio de miembros de liga - Capa de acceso a datos (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        super().__init__(LeagueMember, db)

    async def get_by_league(self, league_id: int, options: Optional[List] = None) -> List[LeagueMember]:
        query = select(LeagueMember).where(LeagueMember.league_id == league_id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_by_user(self, user_id: int, options: Optional[List] = None) -> List[LeagueMember]:
        query = select(LeagueMember).where(LeagueMember.user_id == user_id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_by_user_with_league(self, user_id: int) -> List[LeagueMember]:
        query = (
            select(LeagueMember)
            .options(
                joinedload(LeagueMember.members_league),
                joinedload(LeagueMember.user)
            )
            .where(LeagueMember.user_id == user_id)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_league_and_user(self, league_id: int, user_id: int, options: Optional[List] = None) -> Optional[LeagueMember]:
        query = select(LeagueMember).where(LeagueMember.league_id == league_id, LeagueMember.user_id == user_id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_league_rankings(self, league_id: int) -> List[LeagueMember]:
        query = select(LeagueMember).where(LeagueMember.league_id == league_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_league_rankings_with_user(self, league_id: int) -> List[LeagueMember]:
        query = (
            select(LeagueMember)
            .options(
                joinedload(LeagueMember.user),
                joinedload(LeagueMember.roster).joinedload(Roster.player)
            )
            .where(LeagueMember.league_id == league_id)
            .order_by(LeagueMember.total_points.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())


class RosterRepository(BaseRepository[Roster]):
    '''
    Repositorio de rosters - Capa de acceso a datos (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        super().__init__(Roster, db)

    async def get_by_league_member(self, league_member_id: int, options: Optional[List] = None) -> List[Roster]:
        query = select(Roster).where(Roster.league_member_id == league_member_id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_starters_by_league_member(self, league_member_id: int, options: Optional[List] = None) -> List[Roster]:
        query = select(Roster).where(Roster.league_member_id == league_member_id, Roster.is_starter == True)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_bench_by_league_member(self, league_member_id: int, options: Optional[List] = None) -> List[Roster]:
        query = select(Roster).where(Roster.league_member_id == league_member_id, Roster.is_bench == True)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_player_and_member(self, league_member_id: int, player_id: int, options: Optional[List] = None) -> Optional[Roster]:
        query = select(Roster).where(Roster.league_member_id == league_member_id, Roster.player_id == player_id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def delete_all_by_league_member(self, league_member_id: int) -> None:
        query = delete(Roster).where(Roster.league_member_id == league_member_id)
        await self.db.execute(query)
