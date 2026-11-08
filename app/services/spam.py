import hashlib
import time
from collections import defaultdict
from app.config import settings

class SpamProtectionService:
    def __init__(self):
        # device_hash -> list of submission timestamps (float)
        self.submissions = defaultdict(list)

    def compute_device_hash(self, client_ip: str, user_agent: str) -> str:
        """
        Creates a salted SHA-256 hash. Does NOT store raw IP for privacy compliance.
        """
        raw = f"{client_ip}|{user_agent}|{settings.DEVICE_HASH_SALT}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def check_honeypot(self, honeypot_val: str | None) -> bool:
        """Returns True if clean (honeypot empty), False if bot filled it."""
        return not bool(honeypot_val and honeypot_val.strip())

    def check_rate_limit(self, device_hash: str) -> bool:
        """
        Sliding-window rate limiter. Returns True if permitted, False if 429.
        """
        now = time.time()
        window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS

        # Prune older entries
        self.submissions[device_hash] = [
            t for t in self.submissions[device_hash] if t > window_start
        ]

        if len(self.submissions[device_hash]) >= settings.RATE_LIMIT_PER_DEVICE:
            return False

        self.submissions[device_hash].append(now)
        return True

spam_service = SpamProtectionService()
