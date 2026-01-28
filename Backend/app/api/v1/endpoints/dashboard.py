# from fastapi import APIRouter, Depends, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import func, select
# from app.auth.deps import get_async_db, get_current_user
# from app.db.models.league import LeagueMember
# from app.schemas.dashboard import DashboardOverviewOut

# from app.schemas.responses import StandardResponse

# ### DEPRECATED ###  

# router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# @router.get("/overview", response_model=StandardResponse[DashboardOverviewOut], status_code=status.HTTP_200_OK)
# async def get_dashboard_overview(
#     db: AsyncSession = Depends(get_async_db),
#     current_user = Depends(get_current_user)
# ):
#     # 1. Calculate total points from all leagues
#     query_points = select(func.sum(LeagueMember.total_points)).where(LeagueMember.user_id == current_user.user_id)
#     result_points = await db.execute(query_points)
#     total_points = result_points.scalar() or 0.0
    
#     # 2. Get global rank (dummy for now, but following the model)
#     global_rank = "#1"
    
#     # 3. Active leagues count
#     query_leagues = select(func.count(LeagueMember.id)).where(LeagueMember.user_id == current_user.user_id)
#     result_leagues = await db.execute(query_leagues)
#     active_leagues = result_leagues.scalar() or 0
    
#     # 4. Available budget (aggregated across all memberships for now)
#     query_budget = select(func.sum(LeagueMember.budget)).where(LeagueMember.user_id == current_user.user_id)
#     result_budget = await db.execute(query_budget)
#     total_budget = result_budget.scalar() or 0.0
    
#     # 5. Points history
#     # Query total_points from daily stats (or weekly) for this user.
#     # In a real app we'd have a separate table or query. 
#     # For now, let's return an empty list or simulated item.
#     points_history = [
#         # PointsHistoryItem(recorded_at=datetime.utcnow(), total_points=total_points)
#     ]
    
#     data = DashboardOverviewOut(
#         total_points=total_points,
#         global_rank=global_rank,
#         active_leagues=active_leagues,
#         available_budget=f"{total_budget:,.0f}",
#         points_history=points_history
#     )

#     return {"success": True, "data": data}
