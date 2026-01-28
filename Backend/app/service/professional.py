from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy.orm import joinedload
from app.db.models.professional import Team, Player, PriceHistoryPlayer
from app.core.exceptions import AppError
from app.core.constants import ErrorCode
from app.core.decorators import transactional
from app.repository.professional import TeamRepository, PlayerRepository, PriceHistoryRepository

class TeamService:
    '''
    Servicio que maneja la lógica de negocio de equipos profesionales (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TeamRepository(db)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Team]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_by_id(self, team_id: int) -> Optional[Team]:
        team = await self.repo.get(team_id)
        if not team:
            raise AppError(404, ErrorCode.NOT_FOUND, "El equipo no existe")
        return team

    async def get_by_region(self, region: str) -> List[Team]:
        return await self.repo.get_by_region(region)

    @transactional
    async def create(self, *, name: str, region: str, logo_url: Optional[str] = None) -> Team:
        if await self.repo.get_by_name(name):
            raise AppError(409, ErrorCode.DUPLICATED, f"El equipo '{name}' ya existe")
        
        team = Team(name=name, region=region, logo_url=logo_url)
        return await self.repo.create(team)

    @transactional
    async def update(self, team_id: int, team_data: dict) -> Team:
        team = await self.repo.get(team_id)
        if not team:
            raise AppError(404, ErrorCode.NOT_FOUND, "El equipo no existe")
        
        if 'name' in team_data and team_data['name'] is not None:
            existing_team = await self.repo.get_by_name(team_data['name'])
            if existing_team and existing_team.id != team_id:
                raise AppError(409, ErrorCode.DUPLICATED, "El nombre del equipo ya está en uso")
        
        return await self.repo.update(team_id, team_data)

    @transactional
    async def delete(self, team_id: int) -> None:
        if not await self.repo.delete(team_id):
            raise AppError(404, ErrorCode.NOT_FOUND, "El equipo no existe")


class PlayerService:
    '''
    Servicio que maneja la lógica de negocio de jugadores (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlayerRepository(db)
        self.price_history_repo = PriceHistoryRepository(db)

    async def get_all(self, skip: int = 0, limit: int = 100, sort_by: str = None) -> List[Player]:
        # Inject eager loading
        return await self.repo.get_all(skip=skip, limit=limit, sort_by=sort_by, options=[joinedload(Player.team)])

    async def get_by_id(self, player_id: int) -> Optional[Player]:
        # Inject eager loading
        player = await self.repo.get(player_id, options=[joinedload(Player.team)])
        if not player:
            raise AppError(404, ErrorCode.NOT_FOUND, "El jugador no existe")
        return player

    async def get_by_team(self, team_id: int) -> List[Player]:
        return await self.repo.get_by_team(team_id, options=[joinedload(Player.team)])

    async def get_by_role(self, role: str) -> List[Player]:
        return await self.repo.get_by_role(role, options=[joinedload(Player.team)])

    async def get_by_price_range(self, min_price: float, max_price: float) -> List[Player]:
        return await self.repo.get_by_price_range(min_price, max_price, options=[joinedload(Player.team)])

    async def get_top_by_points(self, limit: int = 10) -> List[Player]:
        return await self.repo.get_top_by_points(limit, options=[joinedload(Player.team)])

    @transactional
    async def create(self, *, name: str, role: str, region: str, team_id: Optional[int] = None,
               current_price: float = 0.0, base_price: float = 0.0, points: float = 0.0) -> Player:
        if current_price < 0 or base_price < 0:
            raise AppError(400, ErrorCode.INVALID_INPUT, "Los precios no pueden ser negativos")
        
        player = Player(
            name=name, role=role, region=region, team_id=team_id,
            current_price=current_price, base_price=base_price, points=points
        )
        
        # We need options mainly if we return the full player object with team in response
        created_player = await self.repo.create(player, options=[joinedload(Player.team)])
        
        if current_price > 0:
            price_history = PriceHistoryPlayer(player_id=created_player.id, price=current_price)
            await self.price_history_repo.create(price_history)
        
        return created_player

    @transactional
    async def update(self, player_id: int, player_data: dict) -> Player:
        player = await self.repo.get(player_id)
        if not player:
            raise AppError(404, ErrorCode.NOT_FOUND, "El jugador no existe")
        
        if 'current_price' in player_data and player_data['current_price'] is not None:
            if player_data['current_price'] < 0:
                raise AppError(400, ErrorCode.INVALID_INPUT, "El precio no puede ser negativo")
            
            if player_data['current_price'] != player.current_price:
                price_history = PriceHistoryPlayer(player_id=player_id, price=player_data['current_price'])
                await self.price_history_repo.create(price_history)
        
        return await self.repo.update(player_id, player_data, options=[joinedload(Player.team)])

    @transactional
    async def delete(self, player_id: int) -> None:
        if not await self.repo.delete(player_id):
             raise AppError(404, ErrorCode.NOT_FOUND, "El jugador no existe")

    async def get_price_history(self, player_id: int) -> List[PriceHistoryPlayer]:
        player = await self.repo.get(player_id)
        if not player:
            raise AppError(404, ErrorCode.NOT_FOUND, "El jugador no existe")
        
        return await self.price_history_repo.get_by_player(player_id)
