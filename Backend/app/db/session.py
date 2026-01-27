'''
Configuración de la sesión de base de datos SQLAlchemy

Crea el engine y el sessionmaker para interactuar con MySQL.
- engine: Conexión a la base de datos con echo=True para debug
- SessionLocal: Factoría para crear sesiones de BD
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Usar DATABASE_URL desde la configuración
DATABASE_URL = settings.database_url

# Echo=True muestra las queries SQL en consola (útil para debug)
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)