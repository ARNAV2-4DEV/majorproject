"""
WorkoutSession model - one row per completed workout session (either a
video upload analyzed via /workout/analyze, or a live camera session).
This is what Phase 3 (Habit Tracker) and Phase 5 (Performance Analyzer)
will query to see actual history instead of working off nothing.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from app.database import Base


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    exercise = Column(String, nullable=False)
    session_type = Column(String, nullable=False)  # rep or hold
    total_reps = Column(Integer, nullable=True)
    total_hold_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())