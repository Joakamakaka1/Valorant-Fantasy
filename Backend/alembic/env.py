"""
Alembic Environment Configuration for Valorant Fantasy API

Este archivo configura el entorno de migraciones de Alembic:
- Importa automáticamente todos los modelos de SQLAlchemy
- Obtiene la URL de base de datos dinámicamente desde app.core.config
- Usa driver síncrono (mysql+mysqlconnector) para las migraciones
- Configura render_as_batch=True para compatibilidad con MySQL
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

# Agregar el directorio raíz al PYTHONPATH para importar módulos de la app
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# ============================================================================
# IMPORTAR BASE Y MODELOS
# ============================================================================
from app.db.base import Base

# Importar TODOS los modelos para que Alembic los detecte con --autogenerate
from app.db.models import (
    User, UserRole,
    Team, Player, PriceHistoryPlayer, PlayerRole, Region,
    League, LeagueMember, Roster, LeagueStatus,
    Match, PlayerMatchStats,
    UserPointsHistory
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ============================================================================
# CONFIGURAR URL DE BASE DE DATOS DINÁMICAMENTE
# ============================================================================
from app.core.config import settings

# Sobrescribir la URL del .ini con la URL de settings (síncrona)
config.set_main_option('sqlalchemy.url', settings.database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Configuración para MySQL: usar batch mode
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Configuración para MySQL: usar batch mode
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
