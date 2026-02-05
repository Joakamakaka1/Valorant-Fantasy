from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.deps import get_async_db
from app.core.redis import RedisCache
from app.core.config import settings

# Importar todos los servicios
from app.service.user import UserService
from app.service.league import LeagueService, LeagueMemberService, RosterService
from app.service.match import MatchService, PlayerMatchStatsService
from app.service.professional import TeamService, PlayerService

# ============================================================================
# REDIS CACHE
# ============================================================================

async def get_redis_cache() -> RedisCache:
    """
    Dependencia para obtener instancia de RedisCache.
    
    Se cierra automáticamente al finalizar el request.
    """
    redis = RedisCache(settings.redis_url)
    try:
        yield redis
    finally:
        await redis.close()

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

def get_match_service(db: AsyncSession = Depends(get_async_db), redis: RedisCache = Depends(get_redis_cache)) -> MatchService:
    return MatchService(db, redis=redis)

def get_player_match_stats_service(db: AsyncSession = Depends(get_async_db), redis: RedisCache = Depends(get_redis_cache)) -> PlayerMatchStatsService:
    return PlayerMatchStatsService(db, redis=redis)

# ============================================================================
# PROFESSIONAL SERVICES
# ============================================================================

def get_team_service(db: AsyncSession = Depends(get_async_db), redis: RedisCache = Depends(get_redis_cache)) -> TeamService:
    return TeamService(db, redis=redis)

def get_player_service(db: AsyncSession = Depends(get_async_db), redis: RedisCache = Depends(get_redis_cache)) -> PlayerService:
    return PlayerService(db, redis=redis)
