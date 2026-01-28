from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from app.auth.deps import get_current_user
from app.api.deps import get_team_service, get_player_service
from app.service.professional import TeamService, PlayerService
from app.schemas.professional import (
    TeamOut,
    PlayerOut,
    PriceHistoryOut
)
from app.schemas.responses import StandardResponse

router = APIRouter(prefix="/professional", tags=["Professional"])

# ============================================================================
# TEAMS ENDPOINTS
# ============================================================================

@router.get("/teams", response_model=StandardResponse[List[TeamOut]], status_code=status.HTTP_200_OK)
async def get_all_teams(
    skip: int = Query(0, description="Número de registros a saltar"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    region: Optional[str] = Query(None, description="Filtrar por región: Americas, EMEA, Pacific, CN"),
    service: TeamService = Depends(get_team_service),
    current_user = Depends(get_current_user)
):
    """Obtener todos los equipos profesionales con filtros opcionales."""
    if region:
        teams = await service.get_by_region(region)
    else:
        teams = await service.get_all(skip=skip, limit=limit)
    
    return {"success": True, "data": teams}

@router.get("/teams/{team_id}", response_model=StandardResponse[TeamOut], status_code=status.HTTP_200_OK)
async def get_team_by_id(
    team_id: int, 
    service: TeamService = Depends(get_team_service),
    current_user = Depends(get_current_user)
):
    """Obtener detalles de un equipo profesional por ID."""
    team = await service.get_by_id(team_id)
    return {"success": True, "data": team}

# ============================================================================
# PLAYERS ENDPOINTS
# ============================================================================

@router.get("/players", response_model=StandardResponse[List[PlayerOut]], status_code=status.HTTP_200_OK)
async def get_all_players(
    skip: int = Query(0, description="Número de registros a saltar"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    team_id: Optional[int] = Query(None, description="Filtrar por equipo"),
    role: Optional[str] = Query(None, description="Filtrar por rol: Duelist, Initiator, Controller, Sentinel, Flex"),
    region: Optional[str] = Query(None, description="Filtrar por región: Americas, EMEA, Pacific, CN"),
    min_price: Optional[float] = Query(None, description="Precio mínimo"),
    max_price: Optional[float] = Query(None, description="Precio máximo"),
    top: Optional[int] = Query(None, description="Obtener top N jugadores por puntos"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: points, price_asc, price_desc"),
    service: PlayerService = Depends(get_player_service),
    current_user = Depends(get_current_user)
):
    """
    Obtener jugadores profesionales con filtros opcionales.
    
    Prioridad de filtros:
    1. top (mejores jugadores por puntos)
    2. team_id
    3. role
    4. region
    5. rango de precio (min_price + max_price)
    6. paginación estándar con ordenamiento opcional
    """
    # Delegar la lógica de filtrado al servicio para código más limpio
    players = await service.get_players_with_filters(
        skip=skip,
        limit=limit,
        team_id=team_id,
        role=role,
        region=region,
        min_price=min_price,
        max_price=max_price,
        top=top,
        sort_by=sort_by
    )
    
    return {"success": True, "data": players}

@router.get("/players/{player_id}", response_model=StandardResponse[PlayerOut], status_code=status.HTTP_200_OK)
async def get_player_by_id(
    player_id: int, 
    service: PlayerService = Depends(get_player_service),
    current_user = Depends(get_current_user)
):
    """Obtener detalles de un jugador profesional por ID."""
    player = await service.get_by_id(player_id)
    return {"success": True, "data": player}

@router.get("/players/{player_id}/price-history", response_model=StandardResponse[List[PriceHistoryOut]], status_code=status.HTTP_200_OK)
async def get_player_price_history(
    player_id: int, 
    service: PlayerService = Depends(get_player_service),
    current_user = Depends(get_current_user)
):
    """Obtener el historial de precios de un jugador."""
    history = await service.get_price_history(player_id)
    return {"success": True, "data": history}
