import os
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Feedback
from app.schemas import FeedbackCreate, FeedbackResponse
from app.services.spam import spam_service
from app.services.validation import validation_service

router = APIRouter(tags=["Feedback"])

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
FORM_HTML_PATH = STATIC_DIR / "form.html"

@router.get("/feedback", response_class=HTMLResponse)
async def serve_feedback_form(r: str = "", v: str = ""):
    """
    Serves the mobile web form. Query parameters ?r=<route_id>&v=<vehicle_id>
    are automatically injected into the form fields.
    """
    if not FORM_HTML_PATH.exists():
        return HTMLResponse("<h3>Feedback form under maintenance.</h3>", status_code=503)
    
    html = FORM_HTML_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=html)

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 1. Anti-spam honeypot verification
    if not spam_service.check_honeypot(payload.website):
        # Fake success for automated bot traps
        return FeedbackResponse(
            feedback_id="00000000-0000-0000-0000-000000000000",
            received_at_utc=datetime.now(timezone.utc),
            message="Submission received."
        )

    # 2. Category validation
    if not validation_service.validate_category(payload.category):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category '{payload.category}'. Must be a recognised category."
        )

    # 3. Compute salted device hash (no raw IP stored)
    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "unknown")
    device_hash = spam_service.compute_device_hash(client_ip, user_agent)

    # 4. Rate limiting check (sliding window)
    if not spam_service.check_rate_limit(device_hash):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many submissions from this device. Please wait a few minutes before submitting again."
        )

    # 5. Persist to database (server-side UTC timestamp generated)
    feedback_entry = Feedback(
        route_id=payload.route_id.strip(),
        vehicle_id=payload.vehicle_id.strip(),
        category=payload.category,
        rating=payload.rating,
        comment=payload.comment,
        device_hash=device_hash,
        is_synthetic=False
    )

    db.add(feedback_entry)
    await db.commit()
    await db.refresh(feedback_entry)

    return FeedbackResponse(
        feedback_id=feedback_entry.feedback_id,
        received_at_utc=feedback_entry.received_at_utc,
        status="received",
        message="Thank you! Your feedback has been recorded."
    )
