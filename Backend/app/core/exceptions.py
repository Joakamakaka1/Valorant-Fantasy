from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
from pydantic import ValidationError
import logging

# Configurar logger
logger = logging.getLogger(__name__)

class AppError(Exception):
    """Excepción personalizada para errores de la aplicación"""
    
    def __init__(self, status_code: int, code: str, message: str, details: dict = None) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

# ============================================================================
# MANEJADORES DE ERRORES PERSONALIZADOS
# ============================================================================

async def app_error_handler(request: Request, exc: AppError):
    """Maneja errores personalizados de AppError"""
    logger.warning(f"AppError: {exc.code} - {exc.message} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "type": "application_error"
            },
            "details": exc.details if exc.details else None,
            "path": str(request.url.path)
        }
    )

# ============================================================================
# ERRORES DE VALIDACIÓN (Pydantic)
# ============================================================================

async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Maneja errores de validación de Pydantic (422 -> 400)
    Proporciona mensajes claros sobre qué campos fallaron
    """
    errors = exc.errors()
    
    # Formatear errores para que sean más legibles
    formatted_errors = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error: {formatted_errors} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Los datos enviados no son válidos. Revisa los campos marcados como erróneos.",
                "type": "validation_error"
            },
            "details": {
                "errors": formatted_errors,
                "total_errors": len(formatted_errors)
            },
            "path": str(request.url.path)
        }
    )

# ============================================================================
# ERRORES DE BASE DE DATOS (SQLAlchemy)
# ============================================================================

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Maneja errores de integridad de base de datos
    - Claves duplicadas
    - Violaciones de foreign key
    - Violaciones de unique constraint
    """
    error_msg = str(exc.orig)
    
    # Detectar tipo específico de error de integridad
    if "UNIQUE constraint failed" in error_msg or "Duplicate entry" in error_msg:
        code = "DUPLICATE_ENTRY"
        message = "El registro que intentas crear ya existe. Verifica que no estés duplicando información única como emails, nombres de usuario, etc."
    elif "FOREIGN KEY constraint failed" in error_msg or "foreign key constraint" in error_msg.lower():
        code = "INVALID_REFERENCE"
        message = "Estás intentando hacer referencia a un registro que no existe. Verifica que los IDs de relaciones (user_id, trip_id, etc.) sean correctos."
    elif "NOT NULL constraint failed" in error_msg:
        code = "MISSING_REQUIRED_FIELD"
        message = "Falta un campo obligatorio. Asegúrate de enviar todos los datos requeridos."
    else:
        code = "DATABASE_INTEGRITY_ERROR"
        message = "Error de integridad en la base de datos. Los datos no cumplen con las restricciones definidas."
    
    logger.error(f"IntegrityError: {error_msg} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": code,
                "message": message,
                "type": "database_integrity_error"
            },
            "details": {
                "database_message": error_msg
            },
            "path": str(request.url.path)
        }
    )

async def operational_error_handler(request: Request, exc: OperationalError):
    """
    Maneja errores operacionales de base de datos
    - Conexión perdida
    - Timeout
    - Base de datos no disponible
    """
    error_msg = str(exc.orig)
    
    logger.error(f"OperationalError: {error_msg} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "code": "DATABASE_UNAVAILABLE",
                "message": "No se pudo conectar con la base de datos. Intenta nuevamente en unos momentos.",
                "type": "database_operational_error"
            },
            "details": {
                "database_message": error_msg
            },
            "path": str(request.url.path)
        }
    )

async def data_error_handler(request: Request, exc: DataError):
    """
    Maneja errores de datos en la base de datos
    - Tipo de dato incorrecto
    - Valor fuera de rango
    """
    error_msg = str(exc.orig)
    
    logger.error(f"DataError: {error_msg} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "INVALID_DATA_TYPE",
                "message": "Los datos enviados tienen un formato incorrecto. Verifica que los tipos de datos sean correctos (números, texto, fechas, etc.).",
                "type": "database_data_error"
            },
            "details": {
                "database_message": error_msg
            },
            "path": str(request.url.path)
        }
    )

# ============================================================================
# ERROR 404 - NOT FOUND
# ============================================================================

async def not_found_handler(request: Request, exc: Exception):
    """Maneja rutas no encontradas (404)"""
    logger.warning(f"NotFound: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "ROUTE_NOT_FOUND",
                "message": f"La ruta '{request.url.path}' no existe en esta API. Verifica la URL.",
                "type": "not_found_error"
            },
            "details": {
                "available_docs": "/docs",
                "requested_path": str(request.url.path)
            },
            "path": str(request.url.path)
        }
    )

# ============================================================================
# ERROR 405 - METHOD NOT ALLOWED
# ============================================================================

async def method_not_allowed_handler(request: Request, exc: Exception):
    """Maneja métodos HTTP no permitidos (405)"""
    logger.warning(f"MethodNotAllowed: {request.method} on {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": f"El método HTTP '{request.method}' no está permitido para esta ruta. Verifica la documentación.",
                "type": "method_not_allowed_error"
            },
            "details": {
                "method_used": request.method,
                "available_docs": "/docs"
            },
            "path": str(request.url.path)
        }
    )

# ============================================================================
# ERROR GENÉRICO (500)
# ============================================================================

async def unhandled_error_handler(request: Request, exc: Exception):
    """Maneja errores no controlados (500)"""
    logger.error(f"UnhandledException: {type(exc).__name__} - {str(exc)} | Path: {request.url.path}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Ocurrió un error inesperado en el servidor. El equipo técnico ha sido notificado.",
                "type": "server_error"
            },
            "details": {
                "error_type": type(exc).__name__,
                "error_message": str(exc)
            },
            "path": str(request.url.path)
        }
    )