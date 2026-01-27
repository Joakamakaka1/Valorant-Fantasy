from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models.professional import Team, Player, PriceHistoryPlayer
from app.core.exceptions import AppError
from app.core.constants import ErrorCode
from app.core.decorators import transactional
from app.repository.professional import TeamRepository, PlayerRepository, PriceHistoryRepository

class TeamService:
    '''
    Servicio que maneja la lógica de negocio de equipos profesionales.
    
    Responsabilidades:
    - Validación de duplicados (nombre de equipo)
    - CRUD con validaciones de negocio
    '''
    def __init__(self, db: Session):
        self.db = db
        self.repo = TeamRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Team]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, team_id: int) -> Optional[Team]:
        team = self.repo.get_by_id(team_id)
        if not team:
            raise AppError(404, ErrorCode.NOT_FOUND, "El equipo no existe")
        return team

    def get_by_region(self, region: str) -> List[Team]:
        return self.repo.get_by_region(region)

    @transactional
    def create(self, *, name: str, region: str, logo_url: Optional[str] = None) -> Team:
        '''
        Crea un nuevo equipo validando que el nombre no esté duplicado.
        '''
        # Validar duplicados
        if self.repo.get_by_name(name):
            raise AppError(409, ErrorCode.DUPLICATED, f"El equipo '{name}' ya existe")
        
        # Crear equipo
        team = Team(name=name, region=region, logo_url=logo_url)
        return self.repo.create(team)

    @transactional
    def update(self, team_id: int, team_data: dict) -> Team:
        '''
        Actualiza un equipo validando duplicados en nombre.
        '''
        team = self.repo.get_by_id(team_id)
        if not team:
            raise AppError(404, ErrorCode.NOT_FOUND, "El equipo no existe")
        
        # Validar nombre duplicado
        if 'name' in team_data and team_data['name'] is not None:
            existing_team = self.repo.get_by_name(team_data['name'])
            if existing_team and existing_team.id != team_id:
                raise AppError(409, ErrorCode.DUPLICATED, "El nombre del equipo ya está en uso")
        
        return self.repo.update(team_id, team_data)

    @transactional
    def delete(self, team_id: int) -> None:
        team = self.repo.get_by_id(team_id)
        if not team:
            raise AppError(404, ErrorCode.NOT_FOUND, "El equipo no existe")
        
        self.repo.delete(team)


class PlayerService:
    '''
    Servicio que maneja la lógica de negocio de jugadores.
    
    Responsabilidades:
    - Validaciones de precios (no negativos, current >= base)
    - Gestión de historial de precios
    - CRUD con validaciones de negocio
    '''
    def __init__(self, db: Session):
        self.db = db
        self.repo = PlayerRepository(db)
        self.price_history_repo = PriceHistoryRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100, sort_by: str = None) -> List[Player]:
        return self.repo.get_all(skip=skip, limit=limit, sort_by=sort_by)

    def get_by_id(self, player_id: int) -> Optional[Player]:
        player = self.repo.get_by_id(player_id)
        if not player:
            raise AppError(404, ErrorCode.NOT_FOUND, "El jugador no existe")
        return player

    def get_by_team(self, team_id: int) -> List[Player]:
        return self.repo.get_by_team(team_id)

    def get_by_role(self, role: str) -> List[Player]:
        return self.repo.get_by_role(role)

    def get_by_price_range(self, min_price: float, max_price: float) -> List[Player]:
        return self.repo.get_by_price_range(min_price, max_price)

    def get_top_by_points(self, limit: int = 10) -> List[Player]:
        return self.repo.get_top_by_points(limit)

    @transactional
    def create(self, *, name: str, role: str, region: str, team_id: Optional[int] = None,
               current_price: float = 0.0, base_price: float = 0.0, points: float = 0.0) -> Player:
        '''
        Crea un nuevo jugador validando precios.
        '''
        # Validaciones de precios
        if current_price < 0 or base_price < 0:
            raise AppError(400, ErrorCode.INVALID_INPUT, "Los precios no pueden ser negativos")
        
        # Crear jugador
        player = Player(
            name=name,
            role=role,
            region=region,
            team_id=team_id,
            current_price=current_price,
            base_price=base_price,
            points=points
        )
        created_player = self.repo.create(player)
        
        # Crear entrada inicial en historial de precios
        if current_price > 0:
            price_history = PriceHistoryPlayer(
                player_id=created_player.id,
                price=current_price
            )
            self.price_history_repo.create(price_history)
        
        return created_player

    @transactional
    def update(self, player_id: int, player_data: dict) -> Player:
        '''
        Actualiza un jugador. Si se cambia el precio, registra en historial.
        '''
        player = self.repo.get_by_id(player_id)
        if not player:
            raise AppError(404, ErrorCode.NOT_FOUND, "El jugador no existe")
        
        # Validar precios si se están actualizando
        if 'current_price' in player_data and player_data['current_price'] is not None:
            if player_data['current_price'] < 0:
                raise AppError(400, ErrorCode.INVALID_INPUT, "El precio no puede ser negativo")
            
            # Si el precio cambió, guardar en historial
            if player_data['current_price'] != player.current_price:
                price_history = PriceHistoryPlayer(
                    player_id=player_id,
                    price=player_data['current_price']
                )
                self.price_history_repo.create(price_history)
        
        return self.repo.update(player_id, player_data)

    @transactional
    def delete(self, player_id: int) -> None:
        player = self.repo.get_by_id(player_id)
        if not player:
            raise AppError(404, ErrorCode.NOT_FOUND, "El jugador no existe")
        
        self.repo.delete(player)

    def get_price_history(self, player_id: int) -> List[PriceHistoryPlayer]:
        '''Obtiene el historial de precios de un jugador'''
        player = self.repo.get_by_id(player_id)
        if not player:
            raise AppError(404, ErrorCode.NOT_FOUND, "El jugador no existe")
        
        return self.price_history_repo.get_by_player(player_id)
