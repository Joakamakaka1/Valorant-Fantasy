from typing import List
from fastapi import APIRouter, Depends, status, Query
from app.auth.deps import get_current_user, check_self_or_admin
from app.api.deps import get_league_service, get_league_member_service, get_roster_service
from app.core.constants import ErrorCode
from app.core.exceptions import AppError, AlreadyExistsException
from app.service.league import LeagueService, LeagueMemberService, RosterService
from app.schemas.league import (
    LeagueCreate, LeagueUpdate, LeagueOut,
    LeagueMemberCreate, LeagueMemberUpdate, LeagueMemberOut,
    RosterCreate, RosterUpdate, RosterOut
)
from app.schemas.responses import StandardResponse

router = APIRouter(prefix="/leagues", tags=["Leagues"])

# ============================================================================
# LEAGUES ENDPOINTS
# ============================================================================

@router.get("/", response_model=StandardResponse[List[LeagueOut]], status_code=status.HTTP_200_OK)
async def get_all_leagues(
    skip: int = 0,
    limit: int = 100,
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    """Obtener todas las ligas disponibles con paginación."""
    leagues = await service.get_all(skip=skip, limit=limit)
    return {"success": True, "data": leagues}

@router.get("/my", response_model=StandardResponse[List[LeagueMemberOut]], status_code=status.HTTP_200_OK)
async def get_my_leagues(
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    """Obtener todas las ligas en las que participa el usuario actual."""
    my_leagues = await service.get_by_user(user_id=current_user.user_id)
    return {"success": True, "data": my_leagues}


@router.get("/{league_id}", response_model=StandardResponse[LeagueOut], status_code=status.HTTP_200_OK)
async def get_league_by_id(
    league_id: int, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    """Obtener detalles de una liga por ID."""
    league = await service.get_by_id(league_id)
    return {"success": True, "data": league}

@router.get("/invite/{invite_code}", response_model=StandardResponse[LeagueOut], status_code=status.HTTP_200_OK)
async def get_league_by_invite_code(
    invite_code: str, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    """Obtener detalles de una liga por código de invitación."""
    league = await service.get_by_invite_code(invite_code)
    return {"success": True, "data": league}

@router.post("/", response_model=StandardResponse[LeagueOut], status_code=status.HTTP_201_CREATED)
async def create_league(
    payload: LeagueCreate, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    """Crear una nueva liga."""
    league = await service.create(
        name=payload.name,
        admin_user_id=current_user.user_id,
        max_teams=payload.max_teams
    )
    return {"success": True, "data": league}

@router.put("/{league_id}", response_model=StandardResponse[LeagueOut], status_code=status.HTTP_200_OK)
async def update_league(
    league_id: int, 
    payload: LeagueUpdate, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    """Actualizar una liga existente (solo admin de la liga)."""
    league = await service.get_by_id(league_id)
    
    check_self_or_admin(current_user, league.admin_user_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    updated_league = await service.update(league_id, update_data)
    return {"success": True, "data": updated_league}

@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_league(
    league_id: int, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    """Eliminar una liga (solo admin de la liga)."""
    league = await service.get_by_id(league_id)
    
    check_self_or_admin(current_user, league.admin_user_id)
    
    await service.delete(league_id)

# ============================================================================
# LEAGUE MEMBERS ENDPOINTS
# ============================================================================

@router.get("/{league_id}/members", response_model=StandardResponse[List[LeagueMemberOut]], status_code=status.HTTP_200_OK)
async def get_league_members(
    league_id: int, 
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    """Obtener todos los miembros de una liga."""
    members = await service.get_by_league(league_id)
    return {"success": True, "data": members}

@router.get("/{league_id}/rankings", response_model=StandardResponse[List[LeagueMemberOut]], status_code=status.HTTP_200_OK)
async def get_league_rankings(
    league_id: int, 
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    """Obtener el ranking de una liga ordenado por puntos."""
    rankings = await service.get_league_rankings(league_id)
    return {"success": True, "data": rankings}

@router.post("/{league_id}/join", response_model=StandardResponse[LeagueMemberOut], status_code=status.HTTP_201_CREATED)
async def join_league(
    league_id: int,
    team_name: str = Query(..., description="Nombre de tu equipo"),
    selected_team_id: int = Query(None, description="ID del equipo profesional elegido"),
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    """
    Unirse a una liga con un nombre de equipo.
    
    Maneja automáticamente duplicados si el usuario ya está en la liga.
    """
    try:
        member = await service.join_league(
            league_id=league_id,
            user_id=current_user.user_id,
            team_name=team_name,
            selected_team_id=selected_team_id
        )
        return {"success": True, "data": member}
    except AlreadyExistsException as e:
        # Usuario ya está en esta liga (constraint uq_league_user)
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="ALREADY_IN_LEAGUE",
            message="Ya estás participando en esta liga",
            details=e.details
        )

@router.get("/members/{member_id}", response_model=StandardResponse[LeagueMemberOut], status_code=status.HTTP_200_OK)
async def get_member_by_id(
    member_id: int, 
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    """Obtener detalles de un miembro de liga por ID."""
    member = await service.get_by_id(member_id)
    return {"success": True, "data": member}

@router.patch("/members/{member_id}", response_model=StandardResponse[LeagueMemberOut], status_code=status.HTTP_200_OK)
async def update_league_member(
    member_id: int, 
    payload: LeagueMemberUpdate, 
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    """Actualizar información de un miembro de liga (solo el propio usuario)."""
    member = await service.get_by_id(member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    updated_member = await service.update(member_id, update_data)
    return {"success": True, "data": updated_member}

@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_or_remove_league_member(
    member_id: int, 
    service: LeagueMemberService = Depends(get_league_member_service),
    league_service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    """
    Abandonar una liga o eliminar a un miembro.
    
    Permitido para: el propio usuario, admin de la liga, o admin del sistema.
    """
    member = await service.get_by_id(member_id)
    league = await league_service.get_by_id(member.league_id)
    
    if (current_user.user_id != member.user_id and 
        current_user.role != "admin" and 
        current_user.user_id != league.admin_user_id):
        raise AppError(status.HTTP_403_FORBIDDEN, ErrorCode.FORBIDDEN, "No tienes permiso para eliminar a este miembro")
    
    await service.leave_league(member_id)

# ============================================================================
# ROSTER ENDPOINTS
# ============================================================================

@router.get("/members/{member_id}/roster", response_model=StandardResponse[List[RosterOut]], status_code=status.HTTP_200_OK)
async def get_member_roster(
    member_id: int, 
    service: RosterService = Depends(get_roster_service),
    current_user = Depends(get_current_user)
):
    """Obtener el roster completo de un miembro de liga."""
    roster = await service.get_by_league_member(member_id)
    return {"success": True, "data": roster}

@router.get("/members/{member_id}/roster/starters", response_model=StandardResponse[List[RosterOut]], status_code=status.HTTP_200_OK)
async def get_member_starters(
    member_id: int, 
    service: RosterService = Depends(get_roster_service),
    current_user = Depends(get_current_user)
):
    """Obtener solo los jugadores titulares del roster."""
    starters = await service.get_starters(member_id)
    return {"success": True, "data": starters}

@router.get("/members/{member_id}/roster/bench", response_model=StandardResponse[List[RosterOut]], status_code=status.HTTP_200_OK)
async def get_member_bench(
    member_id: int, 
    service: RosterService = Depends(get_roster_service),
    current_user = Depends(get_current_user)
):
    """Obtener solo los jugadores en el banquillo."""
    bench = await service.get_bench(member_id)
    return {"success": True, "data": bench}

@router.post("/members/{member_id}/roster", response_model=StandardResponse[RosterOut], status_code=status.HTTP_201_CREATED)
async def add_player_to_roster(
    member_id: int, 
    payload: RosterCreate, 
    service: RosterService = Depends(get_roster_service),
    member_service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    """
    Agregar un jugador al roster.
    
    Maneja automáticamente duplicados si el jugador ya está en el roster.
    """
    member = await member_service.get_by_id(member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    try:
        roster_entry = await service.add_player(
            league_member_id=member_id,
            player_id=payload.player_id,
            is_starter=payload.is_starter,
            is_bench=payload.is_bench,
            role_position=payload.role_position
        )
        return {"success": True, "data": roster_entry}
    except AlreadyExistsException as e:
        # Jugador ya está en este roster (constraint uq_roster_player)
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="PLAYER_ALREADY_IN_ROSTER",
            message="Este jugador ya está en tu equipo",
            details=e.details
        )

@router.patch("/roster/{roster_id}", response_model=StandardResponse[RosterOut], status_code=status.HTTP_200_OK)
async def update_roster_entry(
    roster_id: int, 
    payload: RosterUpdate, 
    service: RosterService = Depends(get_roster_service),
    member_service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    """Actualizar una entrada del roster (cambiar titular/banquillo, etc.)."""
    roster = await service.repo.get_by_id(roster_id)
    if not roster:
         raise AppError(status.HTTP_404_NOT_FOUND, ErrorCode.NOT_FOUND, "Entrada no encontrada")
    
    member = await member_service.get_by_id(roster.league_member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    updated_roster = await service.update_roster_entry(roster_id, update_data)
    return {"success": True, "data": updated_roster}

@router.delete("/roster/{roster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_player_from_roster(
    roster_id: int, 
    service: RosterService = Depends(get_roster_service),
    member_service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    """Eliminar un jugador del roster."""
    roster = await service.repo.get_by_id(roster_id)
    if not roster:
         raise AppError(status.HTTP_404_NOT_FOUND, ErrorCode.NOT_FOUND, "Entrada no encontrada")
    
    member = await member_service.get_by_id(roster.league_member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    await service.remove_player(roster_id)
