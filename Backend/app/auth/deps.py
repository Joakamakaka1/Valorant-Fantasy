from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.db.session import SessionLocal
from app.auth.jwt import decode_access_token
import jwt
from app.schemas.user import TokenData
from app.core.exceptions import AppError

# ============================================================================
# DATABASE DEPENDENCY
# ============================================================================

from app.db.session import SessionLocal, AsyncSessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================

# Define la URL donde se obtiene el token (para la documentación Swagger)
# Apunta al endpoint de login: /v1/auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Valida el token JWT y retorna los datos del usuario (id, username, role).
    Si el token es inválido o expirado, lanza una excepción 401.
    
    NOTA IMPORTANTE - Trade-offs de verificación de existencia en BD:
    ----------------------------------------------------------------
    Esta función NO verifica que el usuario aún exista en la base de datos.
    Solo valida que el token JWT sea válido y no haya expirado.
    
    PROS de NO verificar en BD:
    - ✅ Mejor rendimiento (sin query adicional en cada request)
    - ✅ Menor carga en la base de datos
    - ✅ Escalabilidad mejorada (útil con APIs de alto tráfico)
    
    CONTRAS de NO verificar en BD:
    - ⚠️ Usuarios eliminados pueden usar tokens hasta que expiren
    - ⚠️ Cambios de permisos no se reflejan hasta renovar token
    
    ALTERNATIVAS CONSIDERADAS:
    1. Verificar en TODOS los requests: Seguro pero lento (1 query extra/request)
    2. Caché con Redis/Memcached: Rápido pero requiere infraestructura adicional
    3. Verificar solo en endpoints críticos: Balance entre seguridad y rendimiento
    
    DECISIÓN ACTUAL:
    Para APIs de alto rendimiento, se usa validación solo de token. Los endpoints
    críticos (delete user, change role) verifican existencia explícitamente.
    La duración corta del access token (configurada en settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    minimiza el riesgo de tokens huérfanos.
    minimiza el riesgo de tokens huérfanos.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
    )
    try:
        payload = decode_access_token(token)
        
        user_id: Optional[int] = payload.get("user_id")
        username: Optional[str] = payload.get("username")
        role: Optional[str] = payload.get("role")
        
        if user_id is None or username is None or role is None:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_TOKEN_PAYLOAD",
                message="Token inválido: Faltan datos del usuario (id, username, role)"
            )
            
        return TokenData(user_id=user_id, username=username, role=role)
        
    except jwt.ExpiredSignatureError:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="TOKEN_EXPIRED",
            message="El token ha expirado. Por favor, inicia sesión de nuevo."
        )
    except jwt.InvalidTokenError as e:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_TOKEN",
            message=f"Token inválido: {str(e)}"
        )
    except Exception as e:
        # Capturar cualquier otro error inesperado en la decodificación
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="TOKEN_VALIDATION_ERROR",
            message="No se pudo validar el token",
            details={"error_original": str(e)}
        )

# ============================================================================
# ROLE BASED ACCESS CONTROL (RBAC)
# ============================================================================

# Jerarquía de roles: cada rol hereda permisos de los roles anteriores
ROLE_HIERARCHY = {
    "user": ["user"],
    "admin": ["user", "admin"]
}

class RoleChecker:
    """
    Dependencia para verificar si el usuario tiene uno de los roles permitidos.
    Usa jerarquía de roles: admin tiene permisos de user automáticamente.
    Uso: Depends(RoleChecker(["admin"]))
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: TokenData = Depends(get_current_user)) -> TokenData:
        # Obtener todos los permisos del usuario según su rol
        user_permissions = ROLE_HIERARCHY.get(user.role, [])
        
        # Verificar si el usuario tiene alguno de los roles permitidos
        if not any(role in self.allowed_roles for role in user_permissions):
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                code="INSUFFICIENT_PERMISSIONS",
                message=f"Operación no permitida. Se requiere uno de los siguientes roles: {', '.join(self.allowed_roles)}",
                details={"user_role": user.role, "required_roles": self.allowed_roles}
            )
        return user

# Dependencias listas para usar
allow_admin = RoleChecker(["admin"])

def check_self_or_admin(current_user: TokenData, resource_owner_id: int):
    """Permite el acceso si es Admin o si el usuario es dueño del recurso"""
    if current_user.role != "admin" and current_user.user_id != resource_owner_id:
        raise AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", "No tienes permiso para realizar esta acción")