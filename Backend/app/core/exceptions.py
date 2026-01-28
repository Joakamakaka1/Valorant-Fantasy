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
# EXCEPCIONES DE NEGOCIO
# ============================================================================

class AlreadyExistsException(AppError):
    """
    Excepción para cuando se intenta crear un registro duplicado.
    
    Se lanza cuando una restricción UNIQUE es violada en la base de datos.
    Esto permite que los controladores FastAPI devuelvan 400 en lugar de 500.
    """
    def __init__(self, resource: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="ALREADY_EXISTS",
            message=f"El {resource} ya existe. No se permiten duplicados.",
            details=details or {}
        )

# ============================================================================
# MANEJADORES DE ERRORES PERSONALIZADOS
# ============================================================================

async def app_error_handler(request: Request, exc: AppError):
    """Maneja errores personalizados de AppError"""
    logger.warning(f"AppError: {exc.code} - {exc.message} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "type": "application_error",
                "details": exc.details if exc.details else None
            },
            "path": str(request.url.path)
        }
    )

async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Maneja errores de validación de Pydantic (422 -> 400)
    """
    errors = exc.errors()
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
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Los datos enviados no son válidos. Revisa los campos marcados como erróneos.",
                "type": "validation_error",
                "details": {
                    "errors": formatted_errors,
                    "total_errors": len(formatted_errors)
                }
            },
            "path": str(request.url.path)
        }
    )

async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Maneja errores de integridad de base de datos"""
    error_msg = str(exc.orig)
    
    if "UNIQUE constraint failed" in error_msg or "Duplicate entry" in error_msg:
        code = "DUPLICATE_ENTRY"
        message = "El registro que intentas crear ya existe."
    elif "FOREIGN KEY constraint failed" in error_msg or "foreign key constraint" in error_msg.lower():
        code = "INVALID_REFERENCE"
        message = "Estás intentando hacer referencia a un registro que no existe."
    elif "NOT NULL constraint failed" in error_msg:
        code = "MISSING_REQUIRED_FIELD"
        message = "Falta un campo obligatorio."
    else:
        code = "DATABASE_INTEGRITY_ERROR"
        message = "Error de integridad en la base de datos."
    
    logger.error(f"IntegrityError: {error_msg} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "type": "database_integrity_error",
                "details": {"database_message": error_msg}
            },
            "path": str(request.url.path)
        }
    )

async def operational_error_handler(request: Request, exc: OperationalError):
    """Maneja errores operacionales de base de datos"""
    error_msg = str(exc.orig)
    logger.error(f"OperationalError: {error_msg} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "DATABASE_UNAVAILABLE",
                "message": "No se pudo conectar con la base de datos.",
                "type": "database_operational_error",
                "details": {"database_message": error_msg}
            },
            "path": str(request.url.path)
        }
    )

async def data_error_handler(request: Request, exc: DataError):
    """Maneja errores de datos en la base de datos"""
    error_msg = str(exc.orig)
    logger.error(f"DataError: {error_msg} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INVALID_DATA_TYPE",
                "message": "Los datos enviados tienen un formato incorrecto.",
                "type": "database_data_error",
                "details": {"database_message": error_msg}
            },
            "path": str(request.url.path)
        }
    )

from starlette.exceptions import HTTPException as StarletteHTTPException

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Maneja excepciones HTTP estándar (401, 403, etc.)"""
    logger.warning(f"HTTPException {exc.status_code}: {exc.detail} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": f"HTTP_ERROR_{exc.status_code}",
                "message": exc.detail,
                "type": "http_exception"
            },
            "path": str(request.url.path)
        }
    )

async def not_found_handler(request: Request, exc: Exception):
    """Maneja rutas no encontradas (404)"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "ROUTE_NOT_FOUND",
                "message": f"La ruta '{request.url.path}' no existe.",
                "type": "not_found_error"
            },
            "path": str(request.url.path)
        }
    )

async def method_not_allowed_handler(request: Request, exc: Exception):
    """Maneja métodos HTTP no permitidos (405)"""
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": f"El método '{request.method}' no está permitido.",
                "type": "method_not_allowed_error"
            },
            "path": str(request.url.path)
        }
    )

async def unhandled_error_handler(request: Request, exc: Exception):
    """Maneja errores no controlados (500)"""
    logger.error(f"UnhandledException: {type(exc).__name__} - {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Ocurrió un error inesperado.",
                "type": "server_error",
                "details": {"error_type": type(exc).__name__, "error_message": str(exc)}
            },
            "path": str(request.url.path)
        }
    )
