from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TournamentStatus(str, Enum):
    """Estados posibles de un torneo."""
    UPCOMING = "UPCOMING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"


class TournamentOut(BaseModel):
    """Schema para respuesta de torneo."""
    id: int
    name: str
    vlr_event_id: int
    vlr_event_path: str
    vlr_series_id: Optional[int] = None
    status: TournamentStatus
    start_date: datetime
    end_date: Optional[datetime] = None
    created_at: datetime
    last_scraped_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        use_enum_values = True
