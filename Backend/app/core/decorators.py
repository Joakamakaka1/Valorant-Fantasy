from functools import wraps
from sqlalchemy.orm import Session
from app.core.exceptions import AppError
from app.core.constants import ErrorCode

def transactional(func):
    '''
    Decorador para manejar transacciones de base de datos automáticamente.
    
    Funcionalidad:
    1. Busca automáticamente el objeto Session (db) en los argumentos de la función
    2. Ejecuta la función decorada
    3. Si todo va bien: hace commit y refresh del resultado
    4. Si hay error: hace rollback y re-lanza la excepción
    
    Uso:
        @transactional
        def create_user(self, user_data):
            # código que modifica la BD
            return user
    '''
    import inspect
    import logging

    logger = logging.getLogger(__name__)

    def get_db_session(*args, **kwargs):
        # 1. Buscar directamente Session en args
        for arg in args:
            if isinstance(arg, Session):
                return arg
        
        # 2. Buscar en kwargs
        if 'db' in kwargs:
            return kwargs['db']
            
        # 3. Buscar en el primer argumento (self) si tiene atributo .db
        # Esto es necesario para los métodos de servicios (Service.method)
        # RELAXED CHECK: No usamos isinstance por si hay problemas de importación
        if args and hasattr(args[0], 'db'):
            return args[0].db
            
        return None

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        db = get_db_session(*args, **kwargs)
        
        if not db:
            logger.warning(f"TRANSACTION SKIPPED: No DB session found for {func.__name__}")
            return await func(*args, **kwargs)
            
        try:
            result = await func(*args, **kwargs)
            db.commit()
            if hasattr(result, "__dict__"):
                db.refresh(result)
            return result
        except AppError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed in {func.__name__}: {str(e)}")
            raise AppError(500, ErrorCode.INTERNAL_SERVER_ERROR, str(e))

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        db = get_db_session(*args, **kwargs)
        
        if not db:
            return func(*args, **kwargs)
            
        try:
            result = func(*args, **kwargs)
            db.commit()
            if hasattr(result, "__dict__"):
                db.refresh(result)
            return result
        except AppError:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise AppError(500, ErrorCode.INTERNAL_SERVER_ERROR, str(e))

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper