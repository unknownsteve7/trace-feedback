"""
scripts/generate_qr.py
──────────────────────
Generates offline QR code PNGs embedding vehicle and route context.
URL format: http://<host>:8000/feedback?r=<route_id>&v=<vehicle_id>

Usage:
    python scripts/generate_qr.py
"""

import os
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "scripts" / "qr_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Host configuration (can be localhost, local LAN IP, or Azure App Service domain)
HOST_URL = os.getenv("FEEDBACK_HOST", "http://127.0.0.1:8000")

# Sample Delhi routes and active vehicles from DTC fleet
SAMPLE_TARGETS = [
    {"route_id": "784",  "route_name": "774DOWN", "vehicle_id": "DL1PC9421"},
    {"route_id": "1001", "route_name": "863UP2",   "vehicle_id": "DL1PD1024"},
    {"route_id": "1002", "route_name": "871DOWN",  "vehicle_id": "DL1PC5520"},
    {"route_id": "2203", "route_name": "729DOWN",  "vehicle_id": "DL1PC8812"},
    {"route_id": "1598", "route_name": "144UP",    "vehicle_id": "DL1PD3301"},
    {"route_id": "1932", "route_name": "433UP",    "vehicle_id": "DL1PC7729"},
]

def make_qr_sticker(route_id: str, route_name: str, vehicle_id: str):
    url = f"{HOST_URL}/feedback?r={route_id}&v={vehicle_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1a237e", back_color="white").convert("RGB")

    card_w = qr_img.width + 60
    card_h = qr_img.height + 120
    card = Image.new("RGB", (card_w, card_h), "#ffffff")
    draw = ImageDraw.Draw(card)

    # Header
    draw.rectangle([(0, 0), (card_w, 45)], fill="#1a237e")
    draw.text((15, 13), "TRACE - Delhi Bus Feedback", fill="white")

    # QR
    card.paste(qr_img, (30, 58))

    # Bottom labels
    draw.text((30, card_h - 45), f"Bus: {vehicle_id}  |  Route: {route_name}", fill="#1a237e")
    draw.text((30, card_h - 25), "Scan to report delay, bunching or service issue", fill="#555555")

    filename = f"qr_{vehicle_id}_{route_id}.png"
    out_path = OUT_DIR / filename
    card.save(out_path)
    print(f"Generated QR: {filename} -> {url}")

if __name__ == "__main__":
    print(f"Generating QR stickers pointing to: {HOST_URL}")
    for item in SAMPLE_TARGETS:
        make_qr_sticker(item["route_id"], item["route_name"], item["vehicle_id"])
    print(f"Done. QR stickers saved in {OUT_DIR}")
