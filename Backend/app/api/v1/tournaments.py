from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.auth.deps import get_async_db
from app.service.tournament import TournamentService
from app.schemas.tournament import TournamentOut, TournamentStatus
from app.core.redis import RedisCache
from app.core.config import settings

router = APIRouter()


def get_tournament_service(db: AsyncSession = Depends(get_async_db)) -> TournamentService:
    return TournamentService(db)


@router.get("", response_model=List[TournamentOut], status_code=status.HTTP_200_OK)
async def get_tournaments(
    skip: int = 0,
    limit: int = 100,
    tournament_service: TournamentService = Depends(get_tournament_service)
):
    """
    Obtiene la lista de todos los torneos.
    
    - **skip**: Número de registros a saltar (paginación)
    - **limit**: Máximo número de registros a devolver
    
    Returns:
        List[TournamentOut]: Lista de torneos
    """
    tournaments = await tournament_service.get_all_tournaments(skip=skip, limit=limit)
    return tournaments


@router.get("/ongoing", response_model=TournamentOut | None, status_code=status.HTTP_200_OK)
async def get_ongoing_tournament(
    tournament_service: TournamentService = Depends(get_tournament_service)
):
    """
    Obtiene el torneo actualmente en curso (status = ONGOING).
    
    Si hay múltiples torneos ongoing, devuelve el primero.
    
    Returns:
        TournamentOut | None: Torneo en curso o None si no hay ninguno
    """
    tournament = await tournament_service.get_ongoing_tournament()
    return tournament


@router.get("/{tournament_id}", response_model=TournamentOut, status_code=status.HTTP_200_OK)
async def get_tournament_by_id(
    tournament_id: int,
    tournament_service: TournamentService = Depends(get_tournament_service)
):
    """
    Obtiene un torneo específico por ID.
    
    - **tournament_id**: ID del torneo
    
    Returns:
        TournamentOut: Información del torneo
    """
    tournament = await tournament_service.repo.get_by_id(tournament_id)
    
    if not tournament:
        from app.core.exceptions import AppError
        from app.core.constants import ErrorCode
        raise AppError(404, ErrorCode.NOT_FOUND, f"Tournament with ID {tournament_id} not found")
    
    return tournament
