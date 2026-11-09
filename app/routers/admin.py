from datetime import datetime, timezone
import traceback
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Feedback
from app.schemas import FeedbackAdminOut

router = APIRouter(prefix="/admin", tags=["Admin Export Pipeline"])


def verify_admin_key(x_api_key: str = Header(...)):
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-API-KEY header"
        )
    return x_api_key


@router.get("/export", response_model=list[FeedbackAdminOut])
def export_feedback_data(
    since: Optional[str] = Query(None, description="Export feedback received after this UTC timestamp"),
    include_synthetic: bool = Query(True, description="Include synthetic test rows"),
    limit: int = Query(2000, le=10000, description="Batch limit for ETL extract"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """
    Export endpoint designed for scheduled Bronze/Silver ingestion pull.
    API-Key protected.
    """
    try:
        query = db.query(Feedback).order_by(Feedback.received_at_utc.asc()).limit(limit)

        if since:
            clean_since = since.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_since)
            query = query.filter(Feedback.received_at_utc > dt)

        if not include_synthetic:
            query = query.filter(Feedback.is_synthetic.is_(False))

        records = query.all()
        return records
    except Exception as e:
        print(f"Error in export_feedback_data: {e}\n{traceback.format_exc()}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_feedback_stats(
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """Returns high-level summary counts for monitoring."""
    total = db.query(func.count(Feedback.feedback_id)).scalar() or 0
    synthetic = db.query(func.count(Feedback.feedback_id)).filter(Feedback.is_synthetic.is_(True)).scalar() or 0

    return {
        "total_records": total,
        "synthetic_records": synthetic,
        "live_records": total - synthetic
    }
