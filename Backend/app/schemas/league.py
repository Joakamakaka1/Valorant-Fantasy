from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime
from .user import UserBasicOut

# ============================================================================
# SCHEMAS BÁSICOS (sin relaciones) - Para usar dentro de otros schemas
# ============================================================================

class LeagueBasic(BaseModel):
    """Schema básico de liga para usar en relaciones"""
    id: int
    name: str
    status: Literal["drafting", "active", "finished"]
    
    model_config = ConfigDict(from_attributes=True)

class LeagueMemberBasic(BaseModel):
    """Schema básico de miembro de liga para usar en relaciones"""
    id: int
    league_id: int
    user_id: int
    team_name: str
    total_points: float  # Puntos acumulados en la liga
    
    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# SCHEMAS DE ENTRADA (Create/Update)
# ============================================================================

class LeagueCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    max_teams: int = Field(10, ge=2, le=50)

class LeagueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    max_teams: Optional[int] = Field(None, ge=2, le=50)
    status: Optional[Literal["drafting", "active", "finished"]] = None

class LeagueMemberCreate(BaseModel):
    league_id: int
    user_id: int
    team_name: str = Field(..., min_length=3, max_length=100)
    selected_team_id: Optional[int] = None  # Equipo profesional elegido (da puntos extras)

class LeagueMemberUpdate(BaseModel):
    team_name: Optional[str] = Field(None, min_length=3, max_length=100)
    budget: Optional[float] = Field(None, ge=0)
    selected_team_id: Optional[int] = None  # Cambiar equipo profesional elegido

class RosterCreate(BaseModel):
    league_member_id: int
    player_id: int
    is_starter: bool = False
    is_bench: bool = False
    role_position: Optional[str] = None

class RosterUpdate(BaseModel):
    is_starter: Optional[bool] = None
    is_bench: Optional[bool] = None
    role_position: Optional[str] = None
    total_value_team: Optional[float] = Field(None, ge=0)

# ============================================================================
# SCHEMAS DE SALIDA (Out)
# ============================================================================

class LeagueOut(BaseModel):
    """Schema completo de liga para respuestas"""
    id: int
    name: str
    admin_user_id: int
    invite_code: str
    created_at: datetime
    max_teams: int
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class LeagueMemberOut(BaseModel):
    """Schema completo de miembro de liga para respuestas"""
    id: int
    league_id: int
    user_id: int
    team_name: str
    budget: float
    selected_team_id: Optional[int] = None  # Equipo profesional elegido
    is_admin: bool
    joined_at: datetime
    total_points: float = 0.0  # Puntos totales acumulados
    team_value: float = 0.0  # Valor total del roster actual
    user: Optional[UserBasicOut] = None # Información del usuario
    
    model_config = ConfigDict(from_attributes=True)

class RosterOut(BaseModel):
    """Schema completo de roster para respuestas"""
    id: int
    league_member_id: int
    player_id: int
    is_starter: bool
    is_bench: bool
    role_position: Optional[str] = None
    total_value_team: float
    
    model_config = ConfigDict(from_attributes=True)
