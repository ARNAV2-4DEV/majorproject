"""
Habit routes - skip-risk analysis and streak tracking, based on real
workout session history stored in the database.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.workout_session import WorkoutSession
from app.modules.habit_tracker.habit_engine import analyze_habit

router = APIRouter(prefix="/habit", tags=["habit"])


@router.get("/status")
def get_habit_status(db: Session = Depends(get_db)):
    """
    Pulls every workout session's timestamp from the database and runs
    the habit analysis on it - real data, not a demo/mock log.
    """
    sessions = db.query(WorkoutSession).all()
    session_dates = [s.created_at for s in sessions if s.created_at is not None]

    return analyze_habit(session_dates)