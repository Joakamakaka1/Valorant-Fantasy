from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    vlr_match_id = Column(String(255), unique=True, index=True)
    date = Column(DateTime, nullable=True)
    status = Column(String(50), default="upcoming") # upcoming, live, completed
    tournament_name = Column(String(255), nullable=True)
    stage = Column(String(255), nullable=True)
    vlr_url = Column(String(512), nullable=True)
    is_processed = Column(Boolean, default=False)
    format = Column(String(50), nullable=True) # Bo3, Bo5
    
    team_a_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True) 
    team_b_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    score_team_a = Column(Integer, default=0)
    score_team_b = Column(Integer, default=0)
    
    # Tournament association
    tournament_id = Column(Integer, ForeignKey("tournaments.id", ondelete="SET NULL"), nullable=True, index=True)

    team_a = relationship("Team", foreign_keys=[team_a_id])
    team_b = relationship("Team", foreign_keys=[team_b_id])
    tournament = relationship("Tournament", back_populates="matches")
    player_stats = relationship("PlayerMatchStats", back_populates="match")

    # Performance Indexes
    __table_args__ = (
        # Performance Index: Búsqueda rápida por fecha (rankings, filtros temporales)
        Index('idx_match_date', 'date'),
        # Performance Index: Filtrado por estado (upcoming, live, completed)
        Index('idx_match_status', 'status'),
        # Performance Index (Compuesto): Worker busca completed + no procesados
        Index('idx_match_status_processed', 'status', 'is_processed'),
    )

class PlayerMatchStats(Base):
    __tablename__ = "player_match_stats"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    agent = Column(String(50), nullable=True)
    kills = Column(Integer, default=0)
    death = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    acs = Column(Float, default=0.0)
    adr = Column(Float, default=0.0)
    kast = Column(Float, default=0.0)
    hs_percent = Column(Float, default=0.0)
    rating = Column(Float, default=0.0) # VLR Rating
    first_kills = Column(Integer, default=0)
    first_deaths = Column(Integer, default=0)
    clutches_won = Column(Integer, default=0)
    fantasy_points_earned = Column(Float, default=0.0)

    match = relationship("Match", back_populates="player_stats")
    player = relationship("Player", back_populates="match_stats")

    # Constraints y Performance Indexes
    __table_args__ = (
        # UniqueConstraint: Evitar duplicados de stats por scraper (previene race conditions)
        UniqueConstraint('player_id', 'match_id', name='uq_player_match_stats'),
    )
