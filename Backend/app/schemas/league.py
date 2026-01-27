from pydantic import BaseModel, ConfigDict, field_validator
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
    name: str
    max_teams: int = 10
    
    @field_validator('name')
    @classmethod
    def validate_name_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('El nombre de la liga debe tener al menos 3 caracteres')
        if len(v) > 100:
            raise ValueError('El nombre de la liga no puede tener más de 100 caracteres')
        return v
    
    @field_validator('max_teams')
    @classmethod
    def validate_max_teams(cls, v: int) -> int:
        if v < 2:
            raise ValueError('La liga debe permitir al menos 2 equipos')
        if v > 50:
            raise ValueError('La liga no puede tener más de 50 equipos')
        return v

class LeagueUpdate(BaseModel):
    name: Optional[str] = None
    max_teams: Optional[int] = None
    status: Optional[Literal["drafting", "active", "finished"]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) < 3:
                raise ValueError('El nombre de la liga debe tener al menos 3 caracteres')
            if len(v) > 100:
                raise ValueError('El nombre de la liga no puede tener más de 100 caracteres')
        return v
    
    @field_validator('max_teams')
    @classmethod
    def validate_max_teams(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 2:
                raise ValueError('La liga debe permitir al menos 2 equipos')
            if v > 50:
                raise ValueError('La liga no puede tener más de 50 equipos')
        return v

class LeagueMemberCreate(BaseModel):
    league_id: int
    user_id: int
    team_name: str
    selected_team_id: Optional[int] = None  # Equipo profesional elegido (da puntos extras)
    
    @field_validator('team_name')
    @classmethod
    def validate_team_name_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('El nombre del equipo debe tener al menos 3 caracteres')
        if len(v) > 100:
            raise ValueError('El nombre del equipo no puede tener más de 100 caracteres')
        return v

class LeagueMemberUpdate(BaseModel):
    team_name: Optional[str] = None
    budget: Optional[float] = None
    selected_team_id: Optional[int] = None  # Cambiar equipo profesional elegido
    
    @field_validator('team_name')
    @classmethod
    def validate_team_name_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) < 3:
                raise ValueError('El nombre del equipo debe tener al menos 3 caracteres')
            if len(v) > 100:
                raise ValueError('El nombre del equipo no puede tener más de 100 caracteres')
        return v
    
    @field_validator('budget')
    @classmethod
    def validate_budget(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError('El presupuesto no puede ser negativo')
        return v

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
    total_value_team: Optional[float] = None
    
    @field_validator('total_value_team')
    @classmethod
    def validate_total_value(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError('El valor total no puede ser negativo')
        return v

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
