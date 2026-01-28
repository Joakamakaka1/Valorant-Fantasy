from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.professional import Team, Player, PriceHistoryPlayer
from typing import List, Optional
from app.repository.base import BaseRepository

class TeamRepository(BaseRepository[Team]):
    '''
    Repositorio de equipos profesionales - Capa de acceso a datos (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        super().__init__(Team, db)

    async def get_by_name(self, name: str) -> Optional[Team]:
        query = select(Team).where(Team.name == name)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_region(self, region: str) -> List[Team]:
        query = select(Team).where(Team.region == region)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class PlayerRepository(BaseRepository[Player]):
    '''
    Repositorio de jugadores - Capa de acceso a datos (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        super().__init__(Player, db)

    async def get_all(self, skip: int = 0, limit: int = 100, sort_by: str = None, options: Optional[List] = None) -> List[Player]:
        query = select(Player).offset(skip).limit(limit)
        
        if options:
            query = query.options(*options)
        else:
             # Restore default eager loading
             query = query.options(joinedload(Player.team))

        if sort_by == "points":
            query = query.order_by(Player.points.desc())
        elif sort_by == "price_asc":
            query = query.order_by(Player.current_price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Player.current_price.desc())
            
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, id: int, options: Optional[List] = None) -> Optional[Player]:
         # Restore default eager loading
         if options is None:
             options = [joinedload(Player.team)]
         return await self.get(id, options=options)

    async def get_by_name(self, name: str, options: Optional[List] = None) -> Optional[Player]:
        query = select(Player).where(Player.name == name)
        if options:
            query = query.options(*options)
        else:
            query = query.options(joinedload(Player.team))
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_team(self, team_id: int, options: Optional[List] = None) -> List[Player]:
        query = select(Player).where(Player.team_id == team_id)
        if options:
            query = query.options(*options)
        else:
            query = query.options(joinedload(Player.team))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_role(self, role: str, options: Optional[List] = None) -> List[Player]:
        query = select(Player).where(Player.role == role)
        if options:
            query = query.options(*options)
        else:
            query = query.options(joinedload(Player.team))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_region(self, region: str, options: Optional[List] = None) -> List[Player]:
        query = select(Player).where(Player.region == region)
        if options:
            query = query.options(*options)
        else:
            query = query.options(joinedload(Player.team))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_price_range(self, min_price: float, max_price: float, options: Optional[List] = None) -> List[Player]:
        query = select(Player).where(Player.current_price >= min_price, Player.current_price <= max_price)
        if options:
            query = query.options(*options)
        else:
            query = query.options(joinedload(Player.team))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_top_by_points(self, limit: int = 10, options: Optional[List] = None) -> List[Player]:
        query = select(Player).order_by(Player.points.desc()).limit(limit)
        if options:
            query = query.options(*options)
        else:
            query = query.options(joinedload(Player.team))
        result = await self.db.execute(query)
        return list(result.scalars().all())


class PriceHistoryRepository(BaseRepository[PriceHistoryPlayer]):
    '''
    Repositorio de historial de precios - Capa de acceso a datos (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        super().__init__(PriceHistoryPlayer, db)

    async def get_by_player(self, player_id: int) -> List[PriceHistoryPlayer]:
        query = select(PriceHistoryPlayer).where(PriceHistoryPlayer.player_id == player_id).order_by(PriceHistoryPlayer.date.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
