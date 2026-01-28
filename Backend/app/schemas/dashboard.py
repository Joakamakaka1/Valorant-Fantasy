from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PointsHistoryItem(BaseModel):
    recorded_at: datetime
    total_points: float = Field(0.0, ge=0)
    global_rank: Optional[int] = None

class DashboardOverviewOut(BaseModel):
    total_points: float = Field(0.0, ge=0)
    global_rank: str
    active_leagues: int = Field(0, ge=0)
    available_budget: str
    points_history: List[PointsHistoryItem]
