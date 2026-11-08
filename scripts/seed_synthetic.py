"""
scripts/seed_synthetic.py
─────────────────────────
Seeds synthetic passenger feedback into the database.
All rows are explicitly flagged with is_synthetic = True.

Usage:
    python scripts/seed_synthetic.py [num_rows]
"""

import sys
import uuid
import random
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add root folder to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import AsyncSessionLocal, init_db
from app.models import Feedback
from app.services.reference import reference_service

CATEGORIES = [
    "Late/not arrived",
    "Bunching (multiple buses together)",
    "Overcrowded",
    "Breakdown",
    "Route changed/skipped stops",
    "Driver behaviour",
    "Conductor/staff behaviour",
    "Cleanliness",
    "Safety issue",
    "AC/fan/seats/lights not working"
]

WEIGHTS = [0.35, 0.20, 0.15, 0.08, 0.07, 0.05, 0.04, 0.03, 0.02, 0.01]

SAMPLE_ROUTES = ["784", "1001", "1002", "2203", "1598", "1932", "544", "879", "522"]
SAMPLE_VEHICLES = ["DL1PC9421", "DL1PD1024", "DL1PC5520", "DL1PC8812", "DL1PD3301", "DL1PC7729"]

COMMENTS = {
    "Late/not arrived": ["Bus delayed by 25 mins", "Waited 40 mins at terminal", "Never arrived"],
    "Bunching (multiple buses together)": ["3 buses of route 784 arrived at once", "Buses running bumper to bumper"],
    "Overcrowded": ["Packed completely, could not board", "Too crowded to stand"],
    "Breakdown": ["Bus stopped near flyover due to engine failure"],
    "Route changed/skipped stops": ["Driver skipped Anand Vihar stop"],
    "Driver behaviour": ["Rash overtaking in traffic"],
}

async def seed(n: int = 100):
    await init_db()
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        print(f"Seeding {n} synthetic feedback entries (is_synthetic=True)...")

        entries = []
        for _ in range(n):
            cat = random.choices(CATEGORIES, weights=WEIGHTS, k=1)[0]
            rating = random.choice([1, 2, 2, 3, 4]) if cat in ("Late/not arrived", "Bunching (multiple buses together)", "Breakdown") else random.randint(1, 5)
            comment_list = COMMENTS.get(cat, [""])
            comment = random.choice(comment_list) if random.random() > 0.4 else None
            
            # Simulated timestamp in the last 4 days
            delta_mins = random.randint(10, 4 * 24 * 60)
            received_at = now - timedelta(minutes=delta_mins)

            entry = Feedback(
                feedback_id=str(uuid.uuid4()),
                received_at_utc=received_at,
                route_id=random.choice(SAMPLE_ROUTES),
                vehicle_id=random.choice(SAMPLE_VEHICLES),
                category=cat,
                rating=rating,
                comment=comment,
                device_hash=f"synthetic_device_hash_{random.randint(1000, 9999)}",
                is_synthetic=True
            )
            entries.append(entry)

        session.add_all(entries)
        await session.commit()
        print(f"Successfully seeded {len(entries)} synthetic records into database ✓")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    asyncio.run(seed(count))
