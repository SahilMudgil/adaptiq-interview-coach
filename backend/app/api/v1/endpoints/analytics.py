import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.all_models import User
from backend.app.services.analytics_service import (
    get_user_dashboard_analytics,
    generate_session_text_export
)

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns candidate dashboard metrics:
    - Overview cards (total interviews, average score, mastery tier)
    - Chronological score progression trajectory
    - 4-rubric radar chart metrics
    - Subject mastery percentage across 7 subjects
    - Weak-topic heatmap with severity levels
    - Recent session history
    """
    try:
        data = get_user_dashboard_analytics(current_user.id, db)
        return data
    except Exception as e:
        logger.error(f"Error computing dashboard analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard analytics: {str(e)}"
        )

@router.get("/sessions")
def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns full history of interview sessions for the authenticated user.
    """
    try:
        analytics = get_user_dashboard_analytics(current_user.id, db)
        return {"sessions": analytics.get("recent_sessions", [])}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/session/{session_id}/export", response_class=PlainTextResponse)
def export_session_report(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a downloadable/copyable text report summary of an interview session.
    """
    try:
        report_text = generate_session_text_export(session_id, current_user.id, db)
        return report_text
    except Exception as e:
        logger.error(f"Failed to export session report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate session export."
        )
