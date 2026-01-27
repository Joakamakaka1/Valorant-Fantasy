from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional, Literal

import string
import datetime

# ============================================================================
# SCHEMAS BÁSICOS (sin relaciones) - Para usar dentro de otros schemas
# ============================================================================

class UserBasic(BaseModel):
    """Schema básico de usuario para usar en relaciones"""
    id: int
    email: EmailStr
    username: str
    username: str
    
    model_config = ConfigDict(from_attributes=True)

# ============================================================================
# SCHEMAS DE ENTRADA (Create/Update/Login)
# ============================================================================

class UserBase(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: Optional[Literal["user", "admin"]] = "user"  # Role opcional, por defecto "user"

class User(UserBase):
    """Schema completo de usuario para uso interno"""
    created_at: Optional[datetime.datetime] = None  # Use datetime from import or just datetime if imported
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str  # El cliente envía la contraseña en texto plano, se hashea en el servidor
    role: Optional[Literal["user", "admin"]] = "user"  # Role opcional, por defecto "user"
    
    @field_validator('username')
    @classmethod
    def validate_username_length(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('El nombre de usuario debe tener al menos 3 caracteres')
        if len(v) > 50:
            raise ValueError('El nombre de usuario no puede tener más de 50 caracteres')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        # Validar que solo contenga caracteres alfanuméricos y símbolos comunes
        # Rechazar emojis y caracteres no-ASCII
        allowed_chars = string.ascii_letters + string.digits + string.punctuation + ' '
        
        for char in v:
            if char not in allowed_chars:
                raise ValueError(
                    'La contraseña solo puede contener letras (a-z, A-Z), números (0-9), '
                    'y símbolos estándar (!@#$%^&*, etc.). No se permiten emojis ni caracteres especiales.'
                )
        
        password_bytes = len(v.encode('utf-8'))
        
        if password_bytes < 8:
            raise ValueError('La contraseña debe tener al menos 8 bytes')
        if password_bytes > 72:  # Límite de bcrypt
            raise ValueError('La contraseña no puede exceder 72 bytes (límite de bcrypt)')
        
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str  # El cliente envía la contraseña en texto plano

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None  # El cliente envía la contraseña en texto plano
    # role removido de aquí por seguridad - usar endpoint /change-role
    
    @field_validator('username')
    @classmethod
    def validate_username_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v) < 3:
                raise ValueError('El nombre de usuario debe tener al menos 3 caracteres')
            if len(v) > 50:
                raise ValueError('El nombre de usuario no puede tener más de 50 caracteres')
        return v

class RoleUpdate(BaseModel):
    """Schema para cambiar el role de un usuario (solo admin)"""
    role: Literal["user", "admin"]

# ============================================================================
# SCHEMAS DE SALIDA (Out)
# ============================================================================

class UserBasicOut(BaseModel):
    """Schema simplificado de usuario para respuestas de token (sin relaciones)"""
    id: int
    email: EmailStr
    username: str
    role: str
    role: str
    
    model_config = ConfigDict(from_attributes=True)

class UserOut(BaseModel):
    """Schema completo de usuario con relaciones para respuestas"""
    id: int
    email: EmailStr
    username: str
    role: str  # Incluir role en la respuesta
    role: str  # Incluir role en la respuesta
    
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