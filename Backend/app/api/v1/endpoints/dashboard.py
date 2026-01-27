from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.auth.deps import get_db, get_current_user
from app.db.models.league import LeagueMember
from app.db.models.stats import UserPointsHistory
from app.schemas.dashboard import DashboardOverviewOut, PointsHistoryItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/overview", response_model=DashboardOverviewOut, status_code=status.HTTP_200_OK)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtener estadísticas globales para el Dashboard Overview.
    """
    # 1. Calcular puntos totales de todas las ligas
    total_points = db.query(func.sum(LeagueMember.total_points))\
        .filter(LeagueMember.user_id == current_user.user_id)\
        .scalar() or 0.0

    # 2. Calcular presupuesto disponible (del equipo principal o media)
    # Por ahora pillamos el presupuesto de su primera liga activa
    first_member = db.query(LeagueMember)\
        .filter(LeagueMember.user_id == current_user.user_id)\
        .first()
    
    budget_str = f"€{first_member.budget:.1f}M" if first_member else "€0M"
    leagues_count = db.query(LeagueMember)\
        .filter(LeagueMember.user_id == current_user.user_id)\
        .count()

    # 3. Calcular Rank Global (Muy simplificado por ahora: posición según puntos totales)
    # En una versión real, esto requeriría una query que compare sumas de puntos de todos los usuarios
    # user_ranks = db.query(LeagueMember.user_id, func.sum(LeagueMember.total_points).label('total'))\
    #     .group_by(LeagueMember.user_id)\
    #     .order_by(func.sum(LeagueMember.total_points).desc()).all()
    # rank = next((i + 1 for i, r in enumerate(user_ranks) if r.user_id == current_user.user_id), 0)
    # rank_str = f"#{rank}" if rank > 0 else "N/A"
    rank_str = "#1,234" # Placeholder para no ralentizar el desarrollo inicial

    # 4. Obtener historial de puntos
    history_data = db.query(UserPointsHistory)\
        .filter(UserPointsHistory.user_id == current_user.user_id)\
        .order_by(UserPointsHistory.recorded_at.asc())\
        .limit(30).all()
    
    points_history = [
        PointsHistoryItem(
            recorded_at=h.recorded_at,
            total_points=h.total_points,
            global_rank=h.global_rank
        ) for h in history_data
    ]

    return DashboardOverviewOut(
        total_points=total_points,
        global_rank=rank_str,
        active_leagues=leagues_count,
        available_budget=budget_str,
        points_history=points_history
    )
