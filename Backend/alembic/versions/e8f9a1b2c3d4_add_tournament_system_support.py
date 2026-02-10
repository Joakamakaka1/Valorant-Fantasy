"""add_tournament_system_support

Revision ID: e8f9a1b2c3d4
Revises: 5ccb68ebcfcf
Create Date: 2026-02-10 16:51:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e8f9a1b2c3d4'
down_revision = '5ccb68ebcfcf'
branch_labels = None
depends_on = None


def upgrade():
    """
    Añade soporte para sistema de torneos:
    - Tabla tournaments
    - Tabla tournament_teams (many-to-many)
    - Campo current_tournament_id en players
    - Campo tournament_id en matches
    
    IMPORTANTE: Sin pérdida de datos para usuarios existentes.
    """
    
    # 1. Crear tabla tournaments
    op.create_table(
        'tournaments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('vlr_event_id', sa.Integer(), nullable=False),
        sa.Column('vlr_event_path', sa.String(512), nullable=False),
        sa.Column('vlr_series_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('upcoming', 'ongoing', 'completed', name='tournamentstatus'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_scraped_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_tournament_name'),
        sa.UniqueConstraint('vlr_event_id', name='uq_tournament_vlr_event_id')
    )
    op.create_index('idx_tournament_status', 'tournaments', ['status'])
    op.create_index('idx_tournament_start_date', 'tournaments', ['start_date'])
    
    # 2. Crear tabla tournament_teams (many-to-many)
    op.create_table(
        'tournament_teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tournament_id', 'team_id', name='uq_tournament_team')
    )
    op.create_index('idx_tournament_team_tournament_id', 'tournament_teams', ['tournament_id'])
    op.create_index('idx_tournament_team_team_id', 'tournament_teams', ['team_id'])
    op.create_index('idx_tournament_team', 'tournament_teams', ['tournament_id', 'team_id'])
    
    # 3. Añadir current_tournament_id a players
    op.add_column('players', sa.Column('current_tournament_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_players_current_tournament',
        'players',
        'tournaments',
        ['current_tournament_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_player_current_tournament', 'players', ['current_tournament_id'])
    
    # 4. Añadir tournament_id a matches
    op.add_column('matches', sa.Column('tournament_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_matches_tournament',
        'matches',
        'tournaments',
        ['tournament_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('idx_match_tournament', 'matches', ['tournament_id'])


def downgrade():
    """
    Revierte los cambios del sistema de torneos.
    
    ADVERTENCIA: Elimina datos de torneos pero NO borra jugadores/partidos/usuarios.
    """
    
    # 4. Eliminar campos de matches
    op.drop_index('idx_match_tournament', 'matches')
    op.drop_constraint('fk_matches_tournament', 'matches', type_='foreignkey')
    op.drop_column('matches', 'tournament_id')
    
    # 3. Eliminar campos de players
    op.drop_index('idx_player_current_tournament', 'players')
    op.drop_constraint('fk_players_current_tournament', 'players', type_='foreignkey')
    op.drop_column('players', 'current_tournament_id')
    
    # 2. Eliminar tabla tournament_teams
    op.drop_index('idx_tournament_team', 'tournament_teams')
    op.drop_index('idx_tournament_team_team_id', 'tournament_teams')
    op.drop_index('idx_tournament_team_tournament_id', 'tournament_teams')
    op.drop_table('tournament_teams')
    
    # 1. Eliminar tabla tournaments
    op.drop_index('idx_tournament_start_date', 'tournaments')
    op.drop_index('idx_tournament_status', 'tournaments')
    op.drop_table('tournaments')
    
    # Eliminar enum de MySQL
    op.execute("DROP TYPE IF EXISTS tournamentstatus")
