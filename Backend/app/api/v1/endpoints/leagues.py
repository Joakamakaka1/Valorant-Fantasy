from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.auth.deps import get_db, get_current_user, check_self_or_admin
from app.core.constants import ErrorCode
from app.service.league import LeagueService, LeagueMemberService, RosterService
from app.schemas.league import (
    LeagueCreate, LeagueUpdate, LeagueOut,
    LeagueMemberCreate, LeagueMemberUpdate, LeagueMemberOut,
    RosterCreate, RosterUpdate, RosterOut
)

router = APIRouter(prefix="/leagues", tags=["Leagues"])

# ============================================================================
# LEAGUES ENDPOINTS
# ============================================================================

@router.get("/", response_model=List[LeagueOut], status_code=status.HTTP_200_OK)
def get_all_leagues(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener todas las ligas"""
    service = LeagueService(db)
    return service.get_all(skip=skip, limit=limit)

@router.get("/my", response_model=List[LeagueMemberOut], status_code=status.HTTP_200_OK)
def get_my_leagues(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener todas las ligas a las que el usuario actual se ha unido"""
    service = LeagueMemberService(db)
    return service.get_by_user(user_id=current_user.user_id)


@router.get("/{league_id}", response_model=LeagueOut, status_code=status.HTTP_200_OK)
def get_league_by_id(
    league_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener una liga específica por ID"""
    service = LeagueService(db)
    return service.get_by_id(league_id)

@router.get("/invite/{invite_code}", response_model=LeagueOut, status_code=status.HTTP_200_OK)
def get_league_by_invite_code(
    invite_code: str, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener una liga por código de invitación"""
    service = LeagueService(db)
    return service.get_by_invite_code(invite_code)

@router.post("/", response_model=LeagueOut, status_code=status.HTTP_201_CREATED)
def create_league(
    payload: LeagueCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Crear una nueva liga.
    El usuario actual se convierte en administrador.
    Se genera un código de invitación único automáticamente.
    """
    service = LeagueService(db)
    return service.create(
        name=payload.name,
        admin_user_id=current_user.user_id,
        max_teams=payload.max_teams
    )

@router.put("/{league_id}", response_model=LeagueOut, status_code=status.HTTP_200_OK)
def update_league(
    league_id: int, 
    payload: LeagueUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Actualizar una liga (solo administrador de la liga o admin global)"""
    service = LeagueService(db)
    league = service.get_by_id(league_id)
    
    # Seguridad: Solo admin global o el creador de la liga
    check_self_or_admin(current_user, league.admin_user_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    return service.update(league_id, update_data)

@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_league(
    league_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Eliminar una liga (solo administrador de la liga o admin global)"""
    service = LeagueService(db)
    league = service.get_by_id(league_id)
    
    check_self_or_admin(current_user, league.admin_user_id)
    
    service.delete(league_id)

# ============================================================================
# LEAGUE MEMBERS ENDPOINTS
# ============================================================================

@router.get("/{league_id}/members", response_model=List[LeagueMemberOut], status_code=status.HTTP_200_OK)
def get_league_members(
    league_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener todos los miembros de una liga"""
    service = LeagueMemberService(db)
    return service.get_by_league(league_id)

@router.get("/{league_id}/rankings", response_model=List[LeagueMemberOut], status_code=status.HTTP_200_OK)
def get_league_rankings(
    league_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener el ranking de una liga.
    Ordenado por total_points descendente.
    """
    service = LeagueMemberService(db)
    return service.get_league_rankings(league_id)

@router.post("/{league_id}/join", response_model=LeagueMemberOut, status_code=status.HTTP_201_CREATED)
def join_league(
    league_id: int,
    team_name: str = Query(..., description="Nombre de tu equipo"),
    selected_team_id: int = Query(None, description="ID del equipo profesional elegido"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Unirse a una liga.
    Valida que la liga no esté llena y que el usuario no esté ya en la liga.
    """
    service = LeagueMemberService(db)
    return service.join_league(
        league_id=league_id,
        user_id=current_user.user_id,
        team_name=team_name,
        selected_team_id=selected_team_id
    )

@router.get("/members/{member_id}", response_model=LeagueMemberOut, status_code=status.HTTP_200_OK)
def get_member_by_id(
    member_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener un miembro específico"""
    service = LeagueMemberService(db)
    return service.get_by_id(member_id)

@router.patch("/members/{member_id}", response_model=LeagueMemberOut, status_code=status.HTTP_200_OK)
def update_league_member(
    member_id: int, 
    payload: LeagueMemberUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Actualizar un miembro (solo el propio usuario o admin)"""
    service = LeagueMemberService(db)
    member = service.get_by_id(member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    return service.update(member_id, update_data)

@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def leave_or_remove_league_member(
    member_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Salir de una liga (self) o eliminar a alguien (league-admin).
    """
    service = LeagueMemberService(db)
    member = service.get_by_id(member_id)
    league_service = LeagueService(db)
    league = league_service.get_by_id(member.league_id)
    
    # Permiso: El propio usuario, el admin global, O el admin de la liga
    if (current_user.user_id != member.user_id and 
        current_user.role != "admin" and 
        current_user.user_id != league.admin_user_id):
        raise AppError(status.HTTP_403_FORBIDDEN, ErrorCode.FORBIDDEN, "No tienes permiso para eliminar a este miembro")
    
    service.leave_league(member_id)

# ============================================================================
# ROSTER ENDPOINTS (Gestión de equipos de usuarios)
# ============================================================================

@router.get("/members/{member_id}/roster", response_model=List[RosterOut], status_code=status.HTTP_200_OK)
def get_member_roster(
    member_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener el roster completo de un miembro"""
    service = RosterService(db)
    return service.get_by_league_member(member_id)

@router.get("/members/{member_id}/roster/starters", response_model=List[RosterOut], status_code=status.HTTP_200_OK)
def get_member_starters(
    member_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener solo los titulares (máximo 8)"""
    service = RosterService(db)
    return service.get_starters(member_id)

@router.get("/members/{member_id}/roster/bench", response_model=List[RosterOut], status_code=status.HTTP_200_OK)
def get_member_bench(
    member_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener solo los suplentes (máximo 3)"""
    service = RosterService(db)
    return service.get_bench(member_id)

@router.post("/members/{member_id}/roster", response_model=RosterOut, status_code=status.HTTP_201_CREATED)
def add_player_to_roster(
    member_id: int, 
    payload: RosterCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Añadir jugador (solo dueño del equipo)"""
    member_service = LeagueMemberService(db)
    member = member_service.get_by_id(member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    service = RosterService(db)
    return service.add_player(
        league_member_id=member_id,
        player_id=payload.player_id,
        is_starter=payload.is_starter,
        is_bench=payload.is_bench,
        role_position=payload.role_position
    )

@router.patch("/roster/{roster_id}", response_model=RosterOut, status_code=status.HTTP_200_OK)
def update_roster_entry(
    roster_id: int, 
    payload: RosterUpdate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Actualizar entrada (solo dueño del equipo)"""
    service = RosterService(db)
    roster = service.repo.get_by_id(roster_id)
    if not roster:
         raise AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Entrada no encontrada")
    
    member_service = LeagueMemberService(db)
    member = member_service.get_by_id(roster.league_member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    return service.update_roster_entry(roster_id, update_data)

@router.delete("/roster/{roster_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_player_from_roster(
    roster_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Quitar jugador (solo dueño del equipo)"""
    service = RosterService(db)
    roster = service.repo.get_by_id(roster_id)
    if not roster:
         raise AppError(status.HTTP_404_NOT_FOUND, ErrorCode.NOT_FOUND, "Entrada no encontrada")
    
    member_service = LeagueMemberService(db)
    member = member_service.get_by_id(roster.league_member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    service.remove_player(roster_id)
