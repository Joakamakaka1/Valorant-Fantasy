from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.auth.deps import get_db, get_current_user
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
def get_all_matches(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = Query(None, description="Filter by status: upcoming, live, completed"),
    team_id: int = Query(None, description="Filter by team"),
    unprocessed: bool = Query(False, description="Get only unprocessed completed matches"),
    recent_days: int = Query(None, description="Get matches from last N days"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener todos los partidos.
    Soporta múltiples filtros.
    """
    service = MatchService(db)
    
    if unprocessed:
        return service.get_unprocessed()
    if status_filter:
        return service.get_by_status(status_filter)
    if team_id:
        return service.get_by_team(team_id)
    if recent_days:
        return service.get_recent(days=recent_days)
    
    return service.get_all(skip=skip, limit=limit)

@router.get("/{match_id}", response_model=MatchOut, status_code=status.HTTP_200_OK)
def get_match_by_id(
    match_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener un partido específico por ID"""
    service = MatchService(db)
    return service.get_by_id(match_id)

@router.get("/{match_id}/stats", response_model=List[PlayerMatchStatsOut], status_code=status.HTTP_200_OK)
def get_match_stats(
    match_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener todas las estadísticas de un partido"""
    service = PlayerMatchStatsService(db)
    return service.get_by_match(match_id)

@router.get("/players/{player_id}/stats", response_model=List[PlayerMatchStatsOut], status_code=status.HTTP_200_OK)
def get_player_stats(
    player_id: int,
    recent: int = Query(None, description="Get only N most recent matches"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener todas las estadísticas de un jugador.
    Opcionalmente obtener solo las N más recientes.
    """
    service = PlayerMatchStatsService(db)
    
    if recent:
        return service.get_recent_by_player(player_id, limit=recent)
    
    return service.get_by_player(player_id)
