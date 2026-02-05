'''
Configuración de la sesión de base de datos SQLAlchemy

Crea el engine y el sessionmaker para interactuar con MySQL.
- engine: Conexión a la base de datos con echo=True para debug
- SessionLocal: Factoría para crear sesiones de BD
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# 1. Configuración SÍNCRONA (Para scripts simples o worker actual)
DATABASE_URL = settings.database_url
engine = create_engine(
    DATABASE_URL, 
    echo=settings.DEBUG  # Echo SQL en desarrollo, silencioso en producción
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

ASYNC_DATABASE_URL = settings.async_database_url.replace("asyncmy", "aiomysql")
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,  # Consistente con engine síncrono
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False # Importante en async para evitar errores de sesión cerrada
)