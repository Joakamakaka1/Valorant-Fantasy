from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Literal
from datetime import datetime

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
