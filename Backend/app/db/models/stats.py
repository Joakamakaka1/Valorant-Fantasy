from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class UserPointsHistory(Base):
    __tablename__ = "user_points_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_points = Column(Float, default=0.0)
    global_rank = Column(Integer, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    # Performance Indexes
    __table_args__ = (
        # Performance Index: Consultas de historial de puntos ordenadas por fecha
        Index('idx_points_history_date', 'recorded_at'),
    )
