from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean, Float, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base import Base

class LeagueStatus(str, enum.Enum):
    DRAFTING = "drafting"
    ACTIVE = "active"
    FINISHED = "finished"

class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invite_code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    max_teams = Column(Integer, default=10)
    status = Column(Enum(LeagueStatus), default=LeagueStatus.DRAFTING)

    admin_user = relationship("User", back_populates="created_leagues")
    members = relationship("LeagueMember", back_populates="members_league")

    # Fix relationship back_populates names to match LeagueMember
    
class LeagueMember(Base):
    __tablename__ = "leagues_members"

    id = Column(Integer, primary_key=True, index=True)
    league_id = Column(Integer, ForeignKey("leagues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_name = Column(String(255), nullable=False)
    budget = Column(Float, default=100.0)
    selected_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # Equipo profesional elegido
    total_points = Column(Float, default=0.0)  # Puntos totales acumulados en la liga
    is_admin = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    members_league = relationship("League", back_populates="members") 
    user = relationship("User", back_populates="leagues")
    roster = relationship("Roster", back_populates="league_member")
    selected_team = relationship("Team", foreign_keys=[selected_team_id])  # Relación con Team

    # Constraints y Performance Indexes
    __table_args__ = (
        # UniqueConstraint: Un usuario solo puede estar una vez en cada liga
        UniqueConstraint('league_id', 'user_id', name='uq_league_user'),
        # Performance Index: Búsqueda rápida por nombre de equipo
        Index('idx_team_name', 'team_name'),
    )


class Roster(Base):
    __tablename__ = "rosters"

    id = Column(Integer, primary_key=True, index=True)
    league_member_id = Column(Integer, ForeignKey("leagues_members.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    is_starter = Column(Boolean, default=False)
    is_bench = Column(Boolean, default=False)
    role_position = Column(String(50), nullable=True) # e.g., "Flex", "Duelist" slot
    total_value_team = Column(Float, default=0.0) 

    league_member = relationship("LeagueMember", back_populates="roster")
    player = relationship("Player", back_populates="roster_entries")

    # Constraints y Performance Indexes
    __table_args__ = (
        # UniqueConstraint: Un jugador solo puede estar una vez en cada roster de equipo
        UniqueConstraint('league_member_id', 'player_id', name='uq_roster_player'),
    )
