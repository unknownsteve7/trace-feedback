import io
from datetime import datetime, timezone
from fastapi import APIRouter, Response
import qrcode
from PIL import Image, ImageDraw

from app.schemas import HealthResponse
from app.services.reference import reference_service

router = APIRouter(tags=["Metadata"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/categories", response_model=list[str])
def get_categories():
    return reference_service.categories


@router.get("/qr", summary="Generate Dynamic Printable Bus QR Sticker")
def generate_qr_sticker(r: str = "784", v: str = "DL1PC9421", s: str | None = None):
    """
    On-the-fly QR code sticker generation for any bus or stop.
    Usage:
      /qr?r=502&v=DL1PA1234
      /qr?s=DEL0234
    """
    base_url = "https://trace-feedback.vercel.app/feedback"
    params = []
    if r:
        params.append(f"r={r}")
    if v:
        params.append(f"v={v}")
    if s:
        params.append(f"s={s}")

    target_url = base_url + ("?" + "&".join(params) if params else "")

    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1a237e", back_color="white").convert("RGB")

    # Build branded sticker card (350x410)
    card_w = qr_img.width + 60
    card_h = qr_img.height + 120
    card = Image.new("RGB", (card_w, card_h), "#f8f9fa")
    draw = ImageDraw.Draw(card)

    # Header banner
    draw.rectangle([(0, 0), (card_w, 45)], fill="#1a237e")
    draw.text((15, 14), "TRACE • Delhi Bus Passenger Feedback", fill="white")

    # Paste QR code
    card.paste(qr_img, (30, 60))

    # Footer instructions
    if r and v:
        route_text = f"Route: {r} | Bus: {v}"
    elif s:
        route_text = f"Bus Stop ID: {s}"
    else:
        route_text = "Scan to report delays / crowding"

    draw.text((30, card_h - 45), route_text, fill="#0d47a1")
    draw.text((30, card_h - 25), "Scan with any smartphone camera to report", fill="#555555")

    buf = io.BytesIO()
    card.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
