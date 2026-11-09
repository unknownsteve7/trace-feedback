import os
import ssl
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool

from app.config import settings

# Database URL — convert async schemes to sync
db_url = settings.DATABASE_URL

if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
elif db_url.startswith("sqlite+aiosqlite://"):
    db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://", 1)

# SQLite: use /tmp on serverless (writable), else local file
if db_url.startswith("sqlite"):
    if os.path.isdir("/tmp"):
        db_url = "sqlite:////tmp/feedback.db"
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args, echo=settings.DEBUG)
else:
    # PostgreSQL / Supabase — use psycopg2 with SSL
    engine = create_engine(
        db_url,
        connect_args={"sslmode": "require"},
        poolclass=NullPool,
        echo=settings.DEBUG,
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: init_db failed: {e}")
