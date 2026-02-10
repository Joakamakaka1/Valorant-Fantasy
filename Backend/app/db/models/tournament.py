from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base import Base

class TournamentStatus(str, enum.Enum):
    """Estados posibles de un torneo."""
    UPCOMING = "UPCOMING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"

class Tournament(Base):
    """
    Modelo para torneos VCT (Masters, Champions, etc.).
    
    Scrapea automáticamente desde https://www.vlr.gg/events/?tier=60
    para detectar estado (Ongoing/Completed).
    """
    __tablename__ = "tournaments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)  # "Valorant Masters Santiago 2026"
    vlr_event_id = Column(Integer, nullable=False, unique=True)  # e.g., 2760
    vlr_event_path = Column(String(512), nullable=False)  # "/event/2760/valorant-masters-santiago-2026"
    vlr_series_id = Column(Integer, nullable=True)  # Para construir URL de matches (e.g., 5359)
    
    # Estado del torneo
    status = Column(Enum(TournamentStatus), default=TournamentStatus.UPCOMING, nullable=False, index=True)
    
    # Fechas
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_scraped_at = Column(DateTime, nullable=True)  # Última sincronización de estado
    
    # Relationships
    matches = relationship("Match", back_populates="tournament")
    participating_teams = relationship("TournamentTeam", back_populates="tournament", cascade="all, delete-orphan")
    
    # Performance Indexes
    __table_args__ = (
        Index('idx_tournament_status', 'status'),
        Index('idx_tournament_start_date', 'start_date'),
    )
    
    def __repr__(self):
        return f"<Tournament(id={self.id}, name='{self.name}', status='{self.status}')>"


class TournamentTeam(Base):
    """
    Tabla intermedia (many-to-many) entre Tournament y Team.
    
    Indica qué equipos participan en cada torneo.
    Los jugadores de estos equipos se marcan como activos (current_tournament_id).
    """
    __tablename__ = "tournament_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationships
    tournament = relationship("Tournament", back_populates="participating_teams")
    team = relationship("Team")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tournament_id', 'team_id', name='uq_tournament_team'),
        Index('idx_tournament_team', 'tournament_id', 'team_id'),
    )
    
    def __repr__(self):
        return f"<TournamentTeam(tournament_id={self.tournament_id}, team_id={self.team_id})>"
