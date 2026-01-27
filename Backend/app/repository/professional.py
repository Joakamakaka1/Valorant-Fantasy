from sqlalchemy.orm import Session, joinedload
from app.db.models.professional import Team, Player, PriceHistoryPlayer
from typing import List, Optional

class TeamRepository:
    '''
    Repositorio de equipos profesionales - Capa de acceso a datos.
    '''
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Team]:
        return (
            self.db.query(Team)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, team_id: int) -> Optional[Team]:
        return (
            self.db.query(Team)
            .filter(Team.id == team_id)
            .first()
        )

    def get_by_name(self, name: str) -> Optional[Team]:
        return (
            self.db.query(Team)
            .filter(Team.name == name)
            .first()
        )

    def get_by_region(self, region: str) -> List[Team]:
        return (
            self.db.query(Team)
            .filter(Team.region == region)
            .all()
        )

    def create(self, team: Team) -> Team:
        self.db.add(team)
        self.db.flush()
        return team

    def update(self, team_id: int, team_data: dict) -> Team:
        team = self.get_by_id(team_id)
        
        for key, value in team_data.items():
            if value is not None:
                setattr(team, key, value)
        
        return team

    def delete(self, team: Team) -> None:
        self.db.delete(team)


class PlayerRepository:
    '''
    Repositorio de jugadores - Capa de acceso a datos.
    '''
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100, sort_by: str = None) -> List[Player]:
        query = self.db.query(Player)
        
        if sort_by == "points":
            query = query.order_by(Player.points.desc())
        elif sort_by == "price_asc":
            query = query.order_by(Player.current_price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(Player.current_price.desc())
            
        return query.offset(skip).limit(limit).all()

    def get_by_id(self, player_id: int) -> Optional[Player]:
        return (
            self.db.query(Player)
            .filter(Player.id == player_id)
            .first()
        )

    def get_by_name(self, name: str) -> Optional[Player]:
        return (
            self.db.query(Player)
            .filter(Player.name == name)
            .first()
        )

    def get_by_team(self, team_id: int) -> List[Player]:
        """Obtener todos los jugadores de un equipo"""
        return (
            self.db.query(Player)
            .filter(Player.team_id == team_id)
            .all()
        )

    def get_by_role(self, role: str) -> List[Player]:
        """Obtener todos los jugadores de un rol específico"""
        return (
            self.db.query(Player)
            .filter(Player.role == role)
            .all()
        )

    def get_by_region(self, region: str) -> List[Player]:
        """Obtener todos los jugadores de una región"""
        return (
            self.db.query(Player)
            .filter(Player.region == region)
            .all()
        )

    def get_by_price_range(self, min_price: float, max_price: float) -> List[Player]:
        """Obtener jugadores en un rango de precio (útil para armado de equipos)"""
        return (
            self.db.query(Player)
            .filter(Player.current_price >= min_price)
            .filter(Player.current_price <= max_price)
            .all()
        )

    def get_top_by_points(self, limit: int = 10) -> List[Player]:
        """Obtener top jugadores por puntos"""
        return (
            self.db.query(Player)
            .order_by(Player.points.desc())
            .limit(limit)
            .all()
        )

    def create(self, player: Player) -> Player:
        self.db.add(player)
        self.db.flush()
        return player

    def update(self, player_id: int, player_data: dict) -> Player:
        player = self.get_by_id(player_id)
        
        for key, value in player_data.items():
            if value is not None:
                setattr(player, key, value)
        
        return player

    def delete(self, player: Player) -> None:
        self.db.delete(player)


class PriceHistoryRepository:
    '''
    Repositorio de historial de precios - Capa de acceso a datos.
    '''
    def __init__(self, db: Session):
        self.db = db

    def get_by_player(self, player_id: int) -> List[PriceHistoryPlayer]:
        """Obtener historial de precios de un jugador"""
        return (
            self.db.query(PriceHistoryPlayer)
            .filter(PriceHistoryPlayer.player_id == player_id)
            .order_by(PriceHistoryPlayer.date.desc())
            .all()
        )

    def create(self, price_history: PriceHistoryPlayer) -> PriceHistoryPlayer:
        self.db.add(price_history)
        self.db.flush()
        return price_history
