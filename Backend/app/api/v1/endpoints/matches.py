from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.deps import get_async_db, get_current_user
from app.service.match import MatchService, PlayerMatchStatsService
from app.schemas.match import (
    MatchOut,
    PlayerMatchStatsOut
)

router = APIRouter(prefix="/matches", tags=["Matches"])

# ============================================================================
# MATCHES ENDPOINTS
# ============================================================================

@router.get("/", response_model=List[MatchOut], status_code=status.HTTP_200_OK)
async def get_all_matches(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = Query(None, description="Filter by status: upcoming, live, completed"),
    team_id: int = Query(None, description="Filter by team"),
    unprocessed: bool = Query(False, description="Get only unprocessed completed matches"),
    recent_days: int = Query(None, description="Get matches from last N days"),
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    service = MatchService(db)
    
    if unprocessed:
        return await service.get_unprocessed()
    if status_filter:
        return await service.get_by_status(status_filter)
    if team_id:
        return await service.get_by_team(team_id)
    if recent_days:
        return await service.get_recent(days=recent_days)
    
    return await service.get_all(skip=skip, limit=limit)

@router.get("/{match_id}", response_model=MatchOut, status_code=status.HTTP_200_OK)
async def get_match_by_id(
    match_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    service = MatchService(db)
    return await service.get_by_id(match_id)

@router.get("/{match_id}/stats", response_model=List[PlayerMatchStatsOut], status_code=status.HTTP_200_OK)
async def get_match_stats(
    match_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    service = PlayerMatchStatsService(db)
    return await service.get_by_match(match_id)

@router.get("/players/{player_id}/stats", response_model=List[PlayerMatchStatsOut], status_code=status.HTTP_200_OK)
async def get_player_stats(
    player_id: int,
    recent: int = Query(None, description="Get only N most recent matches"),
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    service = PlayerMatchStatsService(db)
    
    if recent:
        return await service.get_recent_by_player(player_id, limit=recent)
    
    return await service.get_by_player(player_id)
