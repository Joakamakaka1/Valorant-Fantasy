from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from app.schemas.professional import TeamBasic

# ============================================================================
# SCHEMAS BÁSICOS (sin relaciones) - Para usar dentro de otros schemas
# ============================================================================

class MatchBasic(BaseModel):
    """Schema básico de partido para usar en relaciones"""
    id: int
    vlr_match_id: str
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class PlayerMatchStatsBasic(BaseModel):
    """Schema básico de estadísticas para usar en relaciones"""
    id: int
    match_id: int
    player_id: int
    fantasy_points_earned: float
    
    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# SCHEMAS DE SALIDA (Out)
# ============================================================================

class PlayerMatchStatsOut(BaseModel):
    """Schema completo de estadísticas para respuestas"""
    id: int
    match_id: int
    player_id: int
    agent: Optional[str] = None
    kills: int
    death: int
    assists: int
    acs: float
    adr: float
    kast: float
    hs_percent: float
    rating: float
    first_kills: int
    first_deaths: int
    clutches_won: int
    fantasy_points_earned: float
    
    # Relación con Player
    player: Optional["PlayerBasic"] = None  # type: ignore

    model_config = ConfigDict(from_attributes=True)

class MatchOut(BaseModel):
    """Schema completo de partido para respuestas"""
    id: int
    vlr_match_id: str
    date: Optional[datetime] = None
    status: str
    tournament_name: Optional[str] = None
    stage: Optional[str] = None
    vlr_url: Optional[str] = None
    is_processed: bool
    format: Optional[str] = None
    team_a_id: Optional[int] = None
    team_b_id: Optional[int] = None
    score_team_a: int
    score_team_b: int
    
    # Relaciones para conveniencia del frontend
    team_a: Optional[TeamBasic] = None
    team_b: Optional[TeamBasic] = None
    player_stats: List[PlayerMatchStatsOut] = []
    
    model_config = ConfigDict(from_attributes=True)

# Import at module level but use string if needed, or update if PlayerBasic is available
from app.schemas.professional import PlayerBasic
PlayerMatchStatsOut.model_rebuild()
MatchOut.model_rebuild()
