"""Leaderboard rankings routes."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import LeaderboardEntry
from security import get_current_user
from routers.analytics import get_analytics

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])

@router.get("", response_model=List[LeaderboardEntry])
def get_leaderboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full leaderboard rankings sorted by score and speed."""
    summary = get_analytics(current_user=current_user, db=db)
    return summary.leaderboard

