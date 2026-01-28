from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.deps import get_async_db, get_current_user
from app.service.professional import TeamService, PlayerService
from app.schemas.professional import (
    TeamOut,
    PlayerOut,
    PriceHistoryOut
)

router = APIRouter(prefix="/professional", tags=["Professional"])

# ============================================================================
# TEAMS ENDPOINTS
# ============================================================================

@router.get("/teams", response_model=List[TeamOut], status_code=status.HTTP_200_OK)
async def get_all_teams(
    skip: int = 0,
    limit: int = 100,
    region: str = Query(None, description="Filter by region"),
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    service = TeamService(db)
    if region:
        return await service.get_by_region(region)
    return await service.get_all(skip=skip, limit=limit)

@router.get("/teams/{team_id}", response_model=TeamOut, status_code=status.HTTP_200_OK)
async def get_team_by_id(
    team_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    service = TeamService(db)
    return await service.get_by_id(team_id)

# ============================================================================
# PLAYERS ENDPOINTS
# ============================================================================

@router.get("/players", response_model=List[PlayerOut], status_code=status.HTTP_200_OK)
async def get_all_players(
    skip: int = 0,
    limit: int = 100,
    team_id: int = Query(None, description="Filter by team"),
    role: str = Query(None, description="Filter by role"),
    region: str = Query(None, description="Filter by region"),
    min_price: float = Query(None, description="Minimum price"),
    max_price: float = Query(None, description="Maximum price"),
    top: int = Query(None, description="Get top N players by points"),
    sort_by: str = Query(None, description="Sort by: points, price_asc, price_desc"),
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    service = PlayerService(db)
    
    if top:
        return await service.get_top_by_points(limit=top)
    if team_id:
        return await service.get_by_team(team_id)
    if role:
        return await service.get_by_role(role)
    if region:
        return await service.get_by_region(region)
    if min_price is not None and max_price is not None:
        return await service.get_by_price_range(min_price, max_price)
    
    return await service.get_all(skip=skip, limit=limit, sort_by=sort_by)

@router.get("/players/{player_id}", response_model=PlayerOut, status_code=status.HTTP_200_OK)
async def get_player_by_id(
    player_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    service = PlayerService(db)
    return await service.get_by_id(player_id)

@router.get("/players/{player_id}/price-history", response_model=List[PriceHistoryOut], status_code=status.HTTP_200_OK)
async def get_player_price_history(
    player_id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user = Depends(get_current_user)
):
    service = PlayerService(db)
    return await service.get_price_history(player_id)
