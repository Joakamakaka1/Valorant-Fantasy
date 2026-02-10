from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import datetime

# ============================================================================
# SCHEMAS DE ENTRADA (Create/Update)
# ============================================================================

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    region: Literal["EMEA", "Americas", "Pacific", "CN"]
    logo_url: Optional[str] = None

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    region: Optional[Literal["EMEA", "Americas", "Pacific", "CN"]] = None
    logo_url: Optional[str] = None

class PlayerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    team_id: Optional[int] = None
    role: Literal["Duelist", "Initiator", "Controller", "Sentinel", "Flex"]
    region: Literal["EMEA", "Americas", "Pacific", "CN"]
    current_price: float = Field(..., gt=0, le=85.0)  # Cap: 85M
    base_price: float = Field(..., gt=0, le=85.0)
    points: float = Field(default=0.0, ge=0, le=20.0)  # Max: 20pts

class PlayerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    team_id: Optional[int] = None
    role: Optional[Literal["Duelist", "Initiator", "Controller", "Sentinel", "Flex"]] = None
    current_price: Optional[float] = Field(None, gt=0, le=85.0)  # Cap: 85M
    points: Optional[float] = Field(None, ge=0, le=20.0)  # Max: 20pts
    photo_url: Optional[str] = None

# ============================================================================
# SCHEMAS BÁSICOS (sin relaciones) - Para usar dentro de otros schemas
# ============================================================================

class TeamBasic(BaseModel):
    """Schema básico de equipo para usar en relaciones"""
    id: int
    name: str
    region: Literal["EMEA", "Americas", "Pacific", "CN"]
    
    model_config = ConfigDict(from_attributes=True)

class PlayerBasic(BaseModel):
    """Schema básico de jugador para usar en relaciones"""
    id: int
    name: str
    team_id: Optional[int] = None
    role: Literal["Duelist", "Initiator", "Controller", "Sentinel", "Flex"]
    photo_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# SCHEMAS DE SALIDA (Out)
# ============================================================================

class TeamOut(BaseModel):
    """Schema completo de equipo para respuestas"""
    id: int
    name: str
    region: str
    logo_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class PlayerOut(BaseModel):
    """Schema completo de jugador para respuestas"""
    id: int
    name: str
    role: str
    region: str
    team_id: Optional[int] = None
    current_price: float
    base_price: float
    points: float
    matches_played: int
    photo_url: Optional[str] = None
    
    # Relaciones para conveniencia del frontend
    team: Optional[TeamBasic] = None
    
    model_config = ConfigDict(from_attributes=True)

class PriceHistoryOut(BaseModel):
    """Schema de historial de precios para respuestas"""
    id: int
    player_id: int
    date: datetime
    price: float
    
    model_config = ConfigDict(from_attributes=True)
