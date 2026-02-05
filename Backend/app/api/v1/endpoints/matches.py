from typing import List, Optional 
from fastapi import APIRouter, Depends, status, Query
from fastapi.responses import JSONResponse
from app.auth.deps import get_current_user
from app.api.deps import get_match_service, get_player_match_stats_service
from app.service.match import MatchService, PlayerMatchStatsService
from app.schemas.match import (
    MatchOut,
    PlayerMatchStatsOut
)
from app.schemas.responses import StandardResponse

router = APIRouter(prefix="/matches", tags=["Matches"])

# ============================================================================
# MATCHES ENDPOINTS
# ============================================================================

@router.get("", response_model=StandardResponse[List[MatchOut]], status_code=status.HTTP_200_OK)
async def get_all_matches(
    skip: int = Query(0, description="Número de registros a saltar"),
    limit: int = Query(100, description="Número máximo de registros a devolver"),
    status_filter: Optional[str] = Query(None, description="Filtrar por estado: upcoming, live, completed"),
    team_id: Optional[int] = Query(None, description="Filtrar por equipo"),
    unprocessed: bool = Query(False, description="Obtener solo partidos completados sin procesar"),
    recent_days: Optional[int] = Query(None, description="Obtener partidos de los últimos N días"),
    service: MatchService = Depends(get_match_service),
    current_user = Depends(get_current_user)
):
    """
    Obtener partidos con filtros opcionales.
    
    Prioridad de filtros:
    1. unprocessed (si es True)
    2. status_filter
    3. team_id
    4. recent_days
    5. paginación estándar (skip, limit)
    """
    # Delegar la lógica de filtrado al servicio para código más limpio
    matches = await service.get_matches_with_filters(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        team_id=team_id,
        unprocessed=unprocessed,
        recent_days=recent_days
    )
    
    return {"success": True, "data": matches}

@router.get("/{match_id}", response_model=StandardResponse[MatchOut], status_code=status.HTTP_200_OK)
async def get_match_by_id(
    match_id: int, 
    service: MatchService = Depends(get_match_service),
    current_user = Depends(get_current_user)
):
    """Obtener detalles de un partido por ID."""
    match = await service.get_by_id(match_id)
    return {"success": True, "data": match}

@router.get("/{match_id}/stats", response_model=StandardResponse[List[PlayerMatchStatsOut]], status_code=status.HTTP_200_OK)
async def get_match_stats(
    match_id: int, 
    service: PlayerMatchStatsService = Depends(get_player_match_stats_service),
    current_user = Depends(get_current_user)
):
    """Obtener estadísticas de todos los jugadores en un partido."""
    stats = await service.get_by_match(match_id)
    
    # Si viene de Redis (lista de dicts), saltamos validación Pydantic
    if isinstance(stats, list) and len(stats) > 0 and isinstance(stats[0], dict):
        return JSONResponse(
            content={"success": True, "data": stats},
            status_code=status.HTTP_200_OK
        )
        
    return {"success": True, "data": stats}

@router.get("/players/{player_id}/stats", response_model=StandardResponse[List[PlayerMatchStatsOut]], status_code=status.HTTP_200_OK)
async def get_player_stats(
    player_id: int,
    recent: Optional[int] = Query(None, description="Obtener solo los N partidos más recientes"),
    service: PlayerMatchStatsService = Depends(get_player_match_stats_service),
    current_user = Depends(get_current_user)
):
    """Obtener estadísticas de un jugador en sus partidos."""
    if recent:
        stats = await service.get_recent_by_player(player_id, limit=recent)
    else:
        stats = await service.get_by_player(player_id)
    
    return {"success": True, "data": stats}
