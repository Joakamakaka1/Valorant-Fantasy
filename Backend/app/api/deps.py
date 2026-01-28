'''
Dependencias para inyección de servicios en endpoints.

Cada función crea una instancia del servicio con su sesión de BD.
Se usan como dependencias de FastAPI con Depends().
'''

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.deps import get_async_db

# Importar todos los servicios
from app.service.user import UserService
from app.service.league import LeagueService, LeagueMemberService, RosterService
from app.service.match import MatchService, PlayerMatchStatsService
from app.service.professional import TeamService, PlayerService

# ============================================================================
# USER SERVICE
# ============================================================================

def get_user_service(db: AsyncSession = Depends(get_async_db)) -> UserService:
    return UserService(db)

# ============================================================================
# LEAGUE SERVICES
# ============================================================================

def get_league_service(db: AsyncSession = Depends(get_async_db)) -> LeagueService:
    return LeagueService(db)

def get_league_member_service(db: AsyncSession = Depends(get_async_db)) -> LeagueMemberService:
    return LeagueMemberService(db)

def get_roster_service(db: AsyncSession = Depends(get_async_db)) -> RosterService:
    return RosterService(db)

# ============================================================================
# MATCH SERVICES
# ============================================================================

def get_match_service(db: AsyncSession = Depends(get_async_db)) -> MatchService:
    return MatchService(db)

def get_player_match_stats_service(db: AsyncSession = Depends(get_async_db)) -> PlayerMatchStatsService:
    return PlayerMatchStatsService(db)

# ============================================================================
# PROFESSIONAL SERVICES
# ============================================================================

def get_team_service(db: AsyncSession = Depends(get_async_db)) -> TeamService:
    return TeamService(db)

def get_player_service(db: AsyncSession = Depends(get_async_db)) -> PlayerService:
    return PlayerService(db)
