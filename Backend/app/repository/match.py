from sqlalchemy.orm import Session, joinedload
from app.db.models.match import Match, PlayerMatchStats
from typing import List, Optional
from datetime import datetime

class MatchRepository:
    '''
    Repositorio de partidos - Capa de acceso a datos.
    '''
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Match]:
        return (
            self.db.query(Match)
            .options(
                joinedload(Match.team_a),
                joinedload(Match.team_b),
                joinedload(Match.player_stats).joinedload(PlayerMatchStats.player)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, match_id: int) -> Optional[Match]:
        return (
            self.db.query(Match)
            .options(
                joinedload(Match.team_a),
                joinedload(Match.team_b),
                joinedload(Match.player_stats).joinedload(PlayerMatchStats.player)
            )
            .filter(Match.id == match_id)
            .first()
        )

    def get_by_vlr_match_id(self, vlr_match_id: str) -> Optional[Match]:
        """Obtener partido por ID de VLR (útil para evitar duplicados)"""
        return (
            self.db.query(Match)
            .filter(Match.vlr_match_id == vlr_match_id)
            .first()
        )

    def get_by_status(self, status: str) -> List[Match]:
        """Obtener partidos por estado (upcoming, live, completed)"""
        return (
            self.db.query(Match)
            .filter(Match.status == status)
            .all()
        )

    def get_unprocessed(self) -> List[Match]:
        """Obtener partidos completados pero no procesados (para actualizar puntos)"""
        return (
            self.db.query(Match)
            .filter(Match.status == "completed")
            .filter(Match.is_processed == False)
            .all()
        )

    def get_by_team(self, team_id: int) -> List[Match]:
        """Obtener todos los partidos de un equipo"""
        return (
            self.db.query(Match)
            .filter((Match.team_a_id == team_id) | (Match.team_b_id == team_id))
            .all()
        )

    def get_by_tournament(self, tournament_name: str) -> List[Match]:
        """Obtener partidos de un torneo"""
        return (
            self.db.query(Match)
            .filter(Match.tournament_name == tournament_name)
            .all()
        )

    def get_recent(self, days: int = 7) -> List[Match]:
        """Obtener partidos recientes (últimos X días)"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return (
            self.db.query(Match)
            .options(
                joinedload(Match.team_a),
                joinedload(Match.team_b),
                joinedload(Match.player_stats).joinedload(PlayerMatchStats.player)
            )
            .filter(Match.date >= cutoff_date)
            .order_by(Match.date.desc())
            .all()
        )

    def create(self, match: Match) -> Match:
        self.db.add(match)
        self.db.flush()
        return match

    def update(self, match_id: int, match_data: dict) -> Match:
        match = self.get_by_id(match_id)
        
        for key, value in match_data.items():
            if value is not None:
                setattr(match, key, value)
        
        return match

    def delete(self, match: Match) -> None:
        self.db.delete(match)


class PlayerMatchStatsRepository:
    '''
    Repositorio de estadísticas de jugadores en partidos - Capa de acceso a datos.
    '''
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[PlayerMatchStats]:
        return (
            self.db.query(PlayerMatchStats)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, stats_id: int) -> Optional[PlayerMatchStats]:
        return (
            self.db.query(PlayerMatchStats)
            .filter(PlayerMatchStats.id == stats_id)
            .first()
        )

    def get_by_match(self, match_id: int) -> List[PlayerMatchStats]:
        """Obtener todas las estadísticas de un partido"""
        return (
            self.db.query(PlayerMatchStats)
            .filter(PlayerMatchStats.match_id == match_id)
            .all()
        )

    def get_by_player(self, player_id: int) -> List[PlayerMatchStats]:
        """Obtener todas las estadísticas de un jugador"""
        return (
            self.db.query(PlayerMatchStats)
            .filter(PlayerMatchStats.player_id == player_id)
            .order_by(PlayerMatchStats.match_id.desc())
            .all()
        )

    def get_by_player_recent(self, player_id: int, limit: int = 5) -> List[PlayerMatchStats]:
        """Obtener estadísticas recientes de un jugador"""
        return (
            self.db.query(PlayerMatchStats)
            .filter(PlayerMatchStats.player_id == player_id)
            .order_by(PlayerMatchStats.match_id.desc())
            .limit(limit)
            .all()
        )

    def get_by_match_and_player(self, match_id: int, player_id: int) -> Optional[PlayerMatchStats]:
        """Obtener estadísticas específicas de un jugador en un partido"""
        return (
            self.db.query(PlayerMatchStats)
            .filter(PlayerMatchStats.match_id == match_id)
            .filter(PlayerMatchStats.player_id == player_id)
            .first()
        )

    def create(self, stats: PlayerMatchStats) -> PlayerMatchStats:
        self.db.add(stats)
        self.db.flush()
        return stats

    def update(self, stats_id: int, stats_data: dict) -> PlayerMatchStats:
        stats = self.get_by_id(stats_id)
        
        for key, value in stats_data.items():
            if value is not None:
                setattr(stats, key, value)
        
        return stats

    def delete(self, stats: PlayerMatchStats) -> None:
        self.db.delete(stats)
