from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PointsHistoryItem(BaseModel):
    recorded_at: datetime
    total_points: float
    global_rank: Optional[int] = None

class DashboardOverviewOut(BaseModel):
    total_points: float
    global_rank: str
    active_leagues: int
    available_budget: str
    points_history: List[PointsHistoryItem]
