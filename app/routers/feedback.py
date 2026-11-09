import os
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Feedback
from app.schemas import FeedbackCreate, FeedbackResponse
from app.services.spam import spam_service
from app.services.validation import validation_service

router = APIRouter(tags=["Feedback"])

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
FORM_HTML_PATH = STATIC_DIR / "form.html"

# Self-contained embedded template for serverless environments (Vercel)
EMBEDDED_FORM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TRACE | Delhi Bus Passenger Feedback</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #f0f2f5; color: #1c1e21; display: flex; justify-content: center; padding: 12px; }
        .card { background: #fff; width: 100%; max-width: 480px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; margin-top: 8px; }
        .header { background: #1a237e; color: #fff; padding: 22px 20px; text-align: center; }
        .header h1 { font-size: 20px; font-weight: 700; }
        .header p { font-size: 13px; opacity: 0.9; margin-top: 4px; }
        .context-pill { background: #e8eaf6; padding: 12px 16px; border-left: 4px solid #3f51b5; font-size: 13px; margin: 16px 20px 0; border-radius: 4px; display: flex; justify-content: space-between; }
        .context-pill span { font-weight: 600; color: #1a237e; }
        form { padding: 20px; }
        .form-group { margin-bottom: 18px; }
        label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: #333; text-transform: uppercase; letter-spacing: 0.5px; }
        select, textarea, input[type="text"] { width: 100%; padding: 12px; border: 1px solid #ced4da; border-radius: 8px; font-size: 15px; }
        select:focus, textarea:focus { outline: none; border-color: #1a237e; }
        .rating-stars { display: flex; gap: 12px; margin: 8px 0; }
        .star-btn { font-size: 32px; color: #ccc; cursor: pointer; user-select: none; transition: 0.2s; }
        .star-btn.active { color: #fbc02d; }
        .char-count { font-size: 11px; color: #777; text-align: right; margin-top: 4px; }
        button[type="submit"] { width: 100%; background: #1a237e; color: #fff; border: none; padding: 15px; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: 0.2s; margin-top: 10px; }
        button[type="submit"]:hover { background: #0d47a1; }
        .success-box { display: none; padding: 35px 20px; text-align: center; }
        .success-box h2 { color: #2e7d32; font-size: 22px; margin-bottom: 8px; }
        .success-box p { font-size: 14px; color: #555; }
        .id-badge { display: inline-block; background: #e8f5e9; color: #2e7d32; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin: 15px 0; font-family: monospace; }
        .err-msg { color: #d32f2f; font-size: 13px; margin-top: 6px; display: none; }
        .hp-field { display: none !important; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1>TRACE &bull; Delhi Bus Feedback</h1>
            <p>Passenger Reliability &amp; Experience Reporting</p>
        </div>

        <div class="context-pill">
            <div>Route: <span id="route-display">--</span></div>
            <div>Bus: <span id="vehicle-display">--</span></div>
        </div>

        <form id="feedback-form">
            <input type="hidden" id="route_id" name="route_id">
            <input type="hidden" id="vehicle_id" name="vehicle_id">
            <input type="text" id="website" name="website" class="hp-field" tabindex="-1" autocomplete="off">

            <div class="form-group">
                <label>Issue Category</label>
                <select id="category" required>
                    <option value="" disabled selected>Select an issue category...</option>
                    <option value="Late/not arrived">Late / Not arrived</option>
                    <option value="Bunching (multiple buses together)">Bunching (Multiple buses together)</option>
                    <option value="Overcrowded">Overcrowded</option>
                    <option value="Breakdown">Breakdown</option>
                    <option value="Route changed/skipped stops">Route changed / Skipped stops</option>
                    <option value="Driver behaviour">Driver behaviour</option>
                    <option value="Conductor/staff behaviour">Conductor / Staff behaviour</option>
                    <option value="Wrong stop announcement/display">Wrong stop announcement / Display</option>
                    <option value="Cleanliness">Cleanliness</option>
                    <option value="Safety issue">Safety issue</option>
                    <option value="Ticketing/fare issue">Ticketing / Fare issue</option>
                    <option value="AC/fan/seats/lights not working">AC / Fan / Seats / Lights not working</option>
                    <option value="Accessibility">Accessibility</option>
                    <option value="Other">Other</option>
                </select>
            </div>

            <div class="form-group">
                <label>Overall Trip Rating</label>
                <div class="rating-stars" id="star-container">
                    <span class="star-btn" data-val="1">&#9733;</span>
                    <span class="star-btn" data-val="2">&#9733;</span>
                    <span class="star-btn" data-val="3">&#9733;</span>
                    <span class="star-btn" data-val="4">&#9733;</span>
                    <span class="star-btn" data-val="5">&#9733;</span>
                </div>
                <input type="hidden" id="rating-val" value="3">
            </div>

            <div class="form-group">
                <label>Comments (Optional)</label>
                <textarea id="comment" maxlength="300" placeholder="Describe the delay or experience (max 300 characters)..."></textarea>
                <div class="char-count"><span id="char-num">0</span> / 300</div>
            </div>

            <div class="err-msg" id="error-box"></div>
            <button type="submit" id="submit-btn">Submit Grievance</button>
        </form>

        <div class="success-box" id="success-screen">
            <h2>&#10003; Grievance Logged</h2>
            <p>Your report has been recorded with embedded vehicle telemetry context.</p>
            <div class="id-badge" id="ticket-id">ID: --</div>
            <p style="font-size: 12px; color: #888;">This feedback links directly to TRACE delay analytics.</p>
        </div>
    </div>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const rParam = urlParams.get('r') || urlParams.get('route') || '784';
        const vParam = urlParams.get('v') || urlParams.get('vehicle') || 'DL1PC9421';

        document.getElementById('route_id').value = rParam;
        document.getElementById('vehicle_id').value = vParam;
        document.getElementById('route-display').innerText = rParam;
        document.getElementById('vehicle-display').innerText = vParam;

        let currentRating = 3;
        const stars = document.querySelectorAll('.star-btn');
        function setRating(val) {
            currentRating = val;
            document.getElementById('rating-val').value = val;
            stars.forEach(s => {
                s.classList.toggle('active', parseInt(s.dataset.val) <= val);
            });
        }
        setRating(3);
        stars.forEach(s => {
            s.addEventListener('click', () => setRating(parseInt(s.dataset.val)));
        });

        const commentBox = document.getElementById('comment');
        commentBox.addEventListener('input', () => {
            document.getElementById('char-num').innerText = commentBox.value.length;
        });

        document.getElementById('feedback-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            const errBox = document.getElementById('error-box');
            errBox.style.display = 'none';

            const payload = {
                route_id: document.getElementById('route_id').value,
                vehicle_id: document.getElementById('vehicle_id').value,
                category: document.getElementById('category').value,
                rating: parseInt(document.getElementById('rating-val').value),
                comment: commentBox.value.trim() || null,
                website: document.getElementById('website').value || null
            };

            try {
                const res = await fetch('/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('feedback-form').style.display = 'none';
                    document.getElementById('ticket-id').innerText = 'TICKET: ' + data.feedback_id.substring(0, 8);
                    document.getElementById('success-screen').style.display = 'block';
                } else {
                    const err = await res.json();
                    errBox.innerText = err.detail || 'Error submitting feedback. Please try again.';
                    errBox.style.display = 'block';
                }
            } catch (error) {
                errBox.innerText = 'Network error connecting to feedback service.';
                errBox.style.display = 'block';
            }
        });
    </script>
</body>
</html>"""

@router.get("/feedback", response_class=HTMLResponse)
def serve_feedback_form(r: str = "784", v: str = "DL1PC9421"):
    if FORM_HTML_PATH.exists():
        html = FORM_HTML_PATH.read_text(encoding="utf-8")
    else:
        html = EMBEDDED_FORM_HTML
    return HTMLResponse(content=html)

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    if not spam_service.check_honeypot(payload.website):
        return FeedbackResponse(
            feedback_id="00000000-0000-0000-0000-000000000000",
            received_at_utc=datetime.now(timezone.utc),
            message="Submission received."
        )

    if not validation_service.validate_category(payload.category):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category '{payload.category}'. Must be a recognised category."
        )

    client_ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "unknown")
    device_hash = spam_service.compute_device_hash(client_ip, user_agent)

    if not spam_service.check_rate_limit(device_hash):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many submissions from this device. Please wait a few minutes before submitting again."
        )

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
    db.commit()
    db.refresh(feedback_entry)

    return FeedbackResponse(
        feedback_id=feedback_entry.feedback_id,
        received_at_utc=feedback_entry.received_at_utc,
        status="received",
        message="Thank you! Your feedback has been recorded."
    )
