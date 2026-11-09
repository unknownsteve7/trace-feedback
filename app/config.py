import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "TRACE Passenger Feedback Service"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Database: Supports SQLite (async) or PostgreSQL
    # Example: postgresql+asyncpg://postgres:trace_pass@localhost:5432/trace_db
    DATABASE_URL: str = "sqlite:///./feedback.db"

    # Security & Anti-Spam
    DEVICE_HASH_SALT: str = "trace_delhi_transit_salt_2026_xyz"
    ADMIN_API_KEY: str = "trace_admin_secret_key_change_in_prod"
    RATE_LIMIT_PER_DEVICE: int = 5          # max 5 requests
    RATE_LIMIT_WINDOW_SECONDS: int = 600    # per 10 minutes

    # Reference data paths
    CATEGORIES_PATH: str = str(BASE_DIR / "data" / "categories.json")
    REFERENCE_CSV_PATH: str = str(BASE_DIR / "data" / "reference_routes_vehicles.csv")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
