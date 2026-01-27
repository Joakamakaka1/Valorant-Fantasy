from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from app.core.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT de acceso (Access Token).
    Duración corta (ej. minutos).
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.PRIVATE_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT de refresco (Refresh Token).
    Duración larga (ej. días).
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.PRIVATE_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def _decode_token(token: str, expected_type: str) -> dict:
    """
    Función helper interna para decodificar y validar el tipo de token.
    """
    payload = jwt.decode(token, settings.PUBLIC_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"El token no es de tipo '{expected_type}'")
    return payload

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un Access Token.
    Retorna None si es inválido, expirado o no es de tipo 'access'.
    """
    return _decode_token(token, "access")

def decode_refresh_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida un Refresh Token.
    Retorna None si es inválido, expirado o no es de tipo 'refresh'.
    """
    return _decode_token(token, "refresh")