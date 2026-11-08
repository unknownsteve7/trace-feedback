from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Feedback
from app.schemas import FeedbackAdminOut

router = APIRouter(prefix="/admin", tags=["Admin Export Pipeline"])

async def verify_admin_key(x_api_key: str = Header(...)):
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-API-KEY header"
        )
    return x_api_key

@router.get("/export", response_model=list[FeedbackAdminOut])
async def export_feedback_data(
    since: Optional[datetime] = Query(None, description="Export feedback received after this UTC timestamp"),
    include_synthetic: bool = Query(True, description="Include synthetic test rows"),
    limit: int = Query(2000, le=10000, description="Batch limit for ETL extract"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """
    Export endpoint designed for scheduled Bronze/Silver ingestion pull.
    API-Key protected.
    """
    stmt = select(Feedback).order_by(Feedback.received_at_utc.asc()).limit(limit)

    if since:
        stmt = stmt.where(Feedback.received_at_utc > since)
    if not include_synthetic:
        stmt = stmt.where(Feedback.is_synthetic == False)

    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/stats")
async def get_feedback_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_admin_key)
):
    """Returns high-level summary counts for monitoring."""
    total_q = await db.execute(select(func.count(Feedback.feedback_id)))
    synth_q = await db.execute(select(func.count(Feedback.feedback_id)).where(Feedback.is_synthetic == True))
    
    total = total_q.scalar() or 0
    synthetic = synth_q.scalar() or 0

    return {
        "total_records": total,
        "synthetic_records": synthetic,
        "live_records": total - synthetic
    }
