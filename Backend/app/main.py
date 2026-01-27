'''
Valorant Fantasy API - Aplicación Principal

Configuración de la aplicación FastAPI:
- Creación de tablas en base de datos
- Seeding de datos iniciales (solo si la BD está vacía)
- Registro de routers de API
- Configuración de exception handlers (orden importante)
- Configuración de CORS
'''

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, DataError
import asyncio
from app.core.background import sync_vlr_task

from app.api.v1 import api_router
from app.db.session import engine
from app.db.base import Base
from app.db import models # Register models
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

from app.core.exceptions import (
    AppError, 
    app_error_handler, 
    validation_error_handler, 
    unhandled_error_handler,
    integrity_error_handler,
    operational_error_handler,
    data_error_handler,
    not_found_handler,
    method_not_allowed_handler
)

app = FastAPI(
    title="Valorant Fantasy API",
    description="API para gestión de valorant fantasy",
    version="1.0.0"
)

# Crear tablas automáticamente
Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup_event():
    # Iniciar sincronización periódica en segundo plano
    asyncio.create_task(sync_vlr_task())

# ============================================================================
# SEED DATABASE (Development/Testing)
# Solo se ejecuta si la base de datos está vacía
# ============================================================================
# from app.db.seed import seed_db
# from app.db.session import SessionLocal

# try:
#     db = SessionLocal()
#     seed_db(db)
# finally:
#     db.close()  # Siempre cerrar la sesión

# Incluir routers de API
app.include_router(api_router, prefix="/api")

# ============================================================================
# MANEJADORES DE EXCEPCIONES
# IMPORTANTE: El orden importa - los más específicos primero
# ============================================================================

# Errores personalizados de la aplicación
app.add_exception_handler(AppError, app_error_handler)

# Errores de validación de Pydantic
app.add_exception_handler(RequestValidationError, validation_error_handler)

# Errores de base de datos SQLAlchemy
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(OperationalError, operational_error_handler)
app.add_exception_handler(DataError, data_error_handler)

# Errores HTTP de Starlette (404, 405, etc.)
app.add_exception_handler(404, not_found_handler)
app.add_exception_handler(405, method_not_allowed_handler)

# Error genérico para cualquier otra excepción
app.add_exception_handler(Exception, unhandled_error_handler)

# ============================================================================
# CORS - Configurado desde variables de entorno
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # Usar configuración desde .env
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
    
)