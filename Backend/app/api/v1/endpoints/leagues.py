from typing import List
from fastapi import APIRouter, Depends, status, Query
from app.auth.deps import get_current_user, check_self_or_admin
from app.api.deps import get_league_service, get_league_member_service, get_roster_service
from app.core.constants import ErrorCode
from app.core.exceptions import AppError
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
async def get_all_leagues(
    skip: int = 0,
    limit: int = 100,
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    return await service.get_all(skip=skip, limit=limit)

@router.get("/my", response_model=List[LeagueMemberOut], status_code=status.HTTP_200_OK)
async def get_my_leagues(
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    return await service.get_by_user(user_id=current_user.user_id)


@router.get("/{league_id}", response_model=LeagueOut, status_code=status.HTTP_200_OK)
async def get_league_by_id(
    league_id: int, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    return await service.get_by_id(league_id)

@router.get("/invite/{invite_code}", response_model=LeagueOut, status_code=status.HTTP_200_OK)
async def get_league_by_invite_code(
    invite_code: str, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    return await service.get_by_invite_code(invite_code)

@router.post("/", response_model=LeagueOut, status_code=status.HTTP_201_CREATED)
async def create_league(
    payload: LeagueCreate, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    return await service.create(
        name=payload.name,
        admin_user_id=current_user.user_id,
        max_teams=payload.max_teams
    )

@router.put("/{league_id}", response_model=LeagueOut, status_code=status.HTTP_200_OK)
async def update_league(
    league_id: int, 
    payload: LeagueUpdate, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    league = await service.get_by_id(league_id)
    
    check_self_or_admin(current_user, league.admin_user_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    return await service.update(league_id, update_data)

@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_league(
    league_id: int, 
    service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
    league = await service.get_by_id(league_id)
    
    check_self_or_admin(current_user, league.admin_user_id)
    
    await service.delete(league_id)

# ============================================================================
# LEAGUE MEMBERS ENDPOINTS
# ============================================================================

@router.get("/{league_id}/members", response_model=List[LeagueMemberOut], status_code=status.HTTP_200_OK)
async def get_league_members(
    league_id: int, 
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    return await service.get_by_league(league_id)

@router.get("/{league_id}/rankings", response_model=List[LeagueMemberOut], status_code=status.HTTP_200_OK)
async def get_league_rankings(
    league_id: int, 
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    return await service.get_league_rankings(league_id)

@router.post("/{league_id}/join", response_model=LeagueMemberOut, status_code=status.HTTP_201_CREATED)
async def join_league(
    league_id: int,
    team_name: str = Query(..., description="Nombre de tu equipo"),
    selected_team_id: int = Query(None, description="ID del equipo profesional elegido"),
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    return await service.join_league(
        league_id=league_id,
        user_id=current_user.user_id,
        team_name=team_name,
        selected_team_id=selected_team_id
    )

@router.get("/members/{member_id}", response_model=LeagueMemberOut, status_code=status.HTTP_200_OK)
async def get_member_by_id(
    member_id: int, 
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    return await service.get_by_id(member_id)

@router.patch("/members/{member_id}", response_model=LeagueMemberOut, status_code=status.HTTP_200_OK)
async def update_league_member(
    member_id: int, 
    payload: LeagueMemberUpdate, 
    service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    member = await service.get_by_id(member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    return await service.update(member_id, update_data)

@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_or_remove_league_member(
    member_id: int, 
    service: LeagueMemberService = Depends(get_league_member_service),
    league_service: LeagueService = Depends(get_league_service),
    current_user = Depends(get_current_user)
):
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

@router.get("/members/{member_id}/roster", response_model=List[RosterOut], status_code=status.HTTP_200_OK)
async def get_member_roster(
    member_id: int, 
    service: RosterService = Depends(get_roster_service),
    current_user = Depends(get_current_user)
):
    return await service.get_by_league_member(member_id)

@router.get("/members/{member_id}/roster/starters", response_model=List[RosterOut], status_code=status.HTTP_200_OK)
async def get_member_starters(
    member_id: int, 
    service: RosterService = Depends(get_roster_service),
    current_user = Depends(get_current_user)
):
    return await service.get_starters(member_id)

@router.get("/members/{member_id}/roster/bench", response_model=List[RosterOut], status_code=status.HTTP_200_OK)
async def get_member_bench(
    member_id: int, 
    service: RosterService = Depends(get_roster_service),
    current_user = Depends(get_current_user)
):
    return await service.get_bench(member_id)

@router.post("/members/{member_id}/roster", response_model=RosterOut, status_code=status.HTTP_201_CREATED)
async def add_player_to_roster(
    member_id: int, 
    payload: RosterCreate, 
    service: RosterService = Depends(get_roster_service),
    member_service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    member = await member_service.get_by_id(member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    return await service.add_player(
        league_member_id=member_id,
        player_id=payload.player_id,
        is_starter=payload.is_starter,
        is_bench=payload.is_bench,
        role_position=payload.role_position
    )

@router.patch("/roster/{roster_id}", response_model=RosterOut, status_code=status.HTTP_200_OK)
async def update_roster_entry(
    roster_id: int, 
    payload: RosterUpdate, 
    service: RosterService = Depends(get_roster_service),
    member_service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    roster = await service.repo.get_by_id(roster_id)
    if not roster:
         raise AppError(status.HTTP_404_NOT_FOUND, ErrorCode.NOT_FOUND, "Entrada no encontrada")
    
    member = await member_service.get_by_id(roster.league_member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    return await service.update_roster_entry(roster_id, update_data)

@router.delete("/roster/{roster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_player_from_roster(
    roster_id: int, 
    service: RosterService = Depends(get_roster_service),
    member_service: LeagueMemberService = Depends(get_league_member_service),
    current_user = Depends(get_current_user)
):
    roster = await service.repo.get_by_id(roster_id)
    if not roster:
         raise AppError(status.HTTP_404_NOT_FOUND, ErrorCode.NOT_FOUND, "Entrada no encontrada")
    
    member = await member_service.get_by_id(roster.league_member_id)
    
    check_self_or_admin(current_user, member.user_id)
    
    await service.remove_player(roster_id)
