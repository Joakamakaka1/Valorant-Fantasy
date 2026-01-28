from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, Literal
import datetime

# ============================================================================
# SCHEMAS BÁSICOS (sin relaciones) - Para usar dentro de otros schemas
# ============================================================================

class UserBasic(BaseModel):
    """Schema básico de usuario para usar en relaciones"""
    id: int
    email: EmailStr
    username: str
    
    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# SCHEMAS DE ENTRADA (Create/Update/Login)
# ============================================================================

class UserBase(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: Literal["user", "admin"] = "user"

class User(UserBase):
    """Schema completo de usuario para uso interno"""
    created_at: Optional[datetime.datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)
    role: Optional[Literal["user", "admin"]] = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=72)

class RoleUpdate(BaseModel):
    """Schema para cambiar el role de un usuario (solo admin)"""
    role: Literal["user", "admin"]

# ============================================================================
# SCHEMAS DE SALIDA (Out)
# ============================================================================

class UserBasicOut(BaseModel):
    """Schema simplificado de usuario para respuestas (sin relaciones)"""
    id: int
    email: EmailStr
    username: str
    role: str
    
    model_config = ConfigDict(from_attributes=True)

class UserOut(BaseModel):
    """Schema completo de usuario con relaciones para respuestas"""
    id: int
    email: EmailStr
    username: str
    role: str
    
    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# SCHEMA PARA TOKEN JWT
# ============================================================================

class Token(BaseModel):
    """Schema para la respuesta de login con token JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserBasicOut  # Información básica del usuario sin relaciones

class TokenRefresh(BaseModel):
    """Schema para solicitud de refresco de token"""
    refresh_token: str

class TokenData(BaseModel):
    """Schema para los datos dentro del token JWT"""
    user_id: int
    username: str
    role: str