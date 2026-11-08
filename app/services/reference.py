import json
import csv
from pathlib import Path
from app.config import settings

class ReferenceService:
    def __init__(self):
        self.categories: list[str] = []
        self.valid_routes: set[str] = set()
        self.valid_vehicles: set[str] = set()

    def load(self):
        # 1. Load categories
        cat_file = Path(settings.CATEGORIES_PATH)
        if cat_file.exists():
            with open(cat_file, "r", encoding="utf-8") as f:
                self.categories = json.load(f)
        else:
            self.categories = [
                "Late/not arrived", "Bunching (multiple buses together)", "Overcrowded",
                "Breakdown", "Route changed/skipped stops", "Driver behaviour",
                "Conductor/staff behaviour", "Wrong stop announcement/display",
                "Cleanliness", "Safety issue", "Ticketing/fare issue",
                "AC/fan/seats/lights not working", "Accessibility", "Other"
            ]

        # 2. Load reference routes and vehicles
        ref_file = Path(settings.REFERENCE_CSV_PATH)
        if ref_file.exists():
            with open(ref_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    item_type = row.get("type", "").lower()
                    item_id = str(row.get("id", "")).strip()
                    if not item_id:
                        continue
                    if item_type == "route":
                        self.valid_routes.add(item_id)
                    elif item_type == "vehicle":
                        self.valid_vehicles.add(item_id)

reference_service = ReferenceService()
