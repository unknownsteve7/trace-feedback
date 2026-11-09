import os
import ssl
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.config import settings

# Database URL & connection arguments
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url.startswith("sqlite") and os.path.isdir("/tmp"):
    # Safe writable path for serverless AWS Lambda / Vercel
    db_url = "sqlite+aiosqlite:////tmp/feedback.db"

connect_args = {}
pool_kwargs = {"future": True, "echo": settings.DEBUG}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "supabase" in db_url or "pooler" in db_url or "sslmode=require" in db_url:
    # Supabase uses custom SSL certificate chain on port 5432 / 6543
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    connect_args = {"ssl": ctx}
    # PgBouncer handles connection pooling on Supabase side; use NullPool locally
    pool_kwargs["poolclass"] = NullPool

engine = create_async_engine(
    db_url,
    connect_args=connect_args,
    **pool_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
