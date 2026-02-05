from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base import Base

class PlayerRole(str, enum.Enum):
    DUELIST = "Duelist"
    INITIATOR = "Initiator"
    CONTROLLER = "Controller"
    SENTINEL = "Sentinel"
    FLEX = "Flex"

class Region(str, enum.Enum):
    EMEA = "EMEA"
    AMERICAS = "Americas"
    PACIFIC = "Pacific"
    CN = "CN"

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    region = Column(Enum(Region), nullable=False)
    logo_url = Column(String(512), nullable=True)

    players = relationship("Player", back_populates="team")

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    role = Column(Enum(PlayerRole), nullable=False)
    region = Column(Enum(Region), nullable=False)
    current_price = Column(Float, default=0.0)
    base_price = Column(Float, default=0.0)
    points = Column(Float, default=0.0)
    matches_played = Column(Integer, default=0)
    photo_url = Column(String(512), nullable=True)  # Player photo from Liquipedia

    team = relationship("Team", back_populates="players")
    price_history = relationship("PriceHistoryPlayer", back_populates="player")
    match_stats = relationship("PlayerMatchStats", back_populates="player")
    roster_entries = relationship("Roster", back_populates="player")

    # Performance Indexes
    __table_args__ = (
        # Performance Index: Búsqueda rápida por nombre de jugador
        Index('idx_player_name', 'name'),
    )

class PriceHistoryPlayer(Base):
    __tablename__ = "price_history_player"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    price = Column(Float, nullable=False)

    player = relationship("Player", back_populates="price_history")

    # Performance Indexes
    __table_args__ = (
        # Performance Index: Consultas de historial ordenadas por fecha
        Index('idx_price_history_date', 'date'),
    )
