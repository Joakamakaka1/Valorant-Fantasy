from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.match import Match, PlayerMatchStats
from typing import List, Optional
from datetime import datetime

from app.repository.base import BaseRepository

class MatchRepository(BaseRepository[Match]):
    '''
    Repositorio de partidos - Capa de acceso a datos (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        super().__init__(Match, db)

    async def get_all(self, skip: int = 0, limit: int = 100, options: Optional[List] = None) -> List[Match]:
        query = select(Match).offset(skip).limit(limit)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_by_id(self, match_id: int, options: Optional[List] = None) -> Optional[Match]:
        query = select(Match).where(Match.id == match_id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return result.scalars().unique().first()

    async def get_by_vlr_match_id(self, vlr_match_id: str) -> Optional[Match]:
        query = select(Match).where(Match.vlr_match_id == vlr_match_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_status(self, status: str, options: Optional[List] = None) -> List[Match]:
        query = select(Match).where(Match.status == status)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_unprocessed(self) -> List[Match]:
        query = select(Match).where(Match.status == "completed", Match.is_processed == False)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_team(self, team_id: int, options: Optional[List] = None) -> List[Match]:
        query = select(Match).where(or_(Match.team_a_id == team_id, Match.team_b_id == team_id))
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def get_by_tournament(self, tournament_name: str) -> List[Match]:
        query = select(Match).where(Match.tournament_name == tournament_name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent(self, days: int = 7, options: Optional[List] = None) -> List[Match]:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = (
            select(Match)
            .where(Match.date >= cutoff_date)
            .order_by(Match.date.desc())
        )
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())


class PlayerMatchStatsRepository(BaseRepository[PlayerMatchStats]):
    '''
    Repositorio de estadísticas de jugadores en partidos - Capa de acceso a datos (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        super().__init__(PlayerMatchStats, db)

    async def get_all(self, skip: int = 0, limit: int = 100, options: Optional[List] = None) -> List[PlayerMatchStats]:
        query = select(PlayerMatchStats).offset(skip).limit(limit)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, stats_id: int, options: Optional[List] = None) -> Optional[PlayerMatchStats]:
        query = select(PlayerMatchStats).where(PlayerMatchStats.id == stats_id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_match(self, match_id: int, options: Optional[List] = None) -> List[PlayerMatchStats]:
        query = select(PlayerMatchStats).where(PlayerMatchStats.match_id == match_id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_player(self, player_id: int, options: Optional[List] = None) -> List[PlayerMatchStats]:
        query = select(PlayerMatchStats).where(PlayerMatchStats.player_id == player_id).order_by(PlayerMatchStats.match_id.desc())
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_player_recent(self, player_id: int, limit: int = 5, options: Optional[List] = None) -> List[PlayerMatchStats]:
        query = select(PlayerMatchStats).where(PlayerMatchStats.player_id == player_id).order_by(PlayerMatchStats.match_id.desc()).limit(limit)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_match_and_player(self, match_id: int, player_id: int, options: Optional[List] = None) -> Optional[PlayerMatchStats]:
        query = select(PlayerMatchStats).where(PlayerMatchStats.match_id == match_id, PlayerMatchStats.player_id == player_id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return result.scalars().first()
