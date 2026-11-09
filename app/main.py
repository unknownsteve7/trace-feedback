from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.database import init_db
from app.services.reference import reference_service
from app.routers import feedback, meta, admin


class VercelPathRewriteMiddleware:
    """
    ASGI middleware to restore original request path on Vercel.
    When Vercel rewrites /(.*) to /api/index.py, Vercel sets 'x-matched-path'
    header to the original requested URI (e.g. /feedback?r=784).
    This middleware restores scope['path'] so FastAPI matches the correct route.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            for name, val in scope.get("headers", []):
                if name.lower() == b"x-matched-path":
                    raw_matched = val.decode("latin1").split("?")[0]
                    if raw_matched:
                        scope["path"] = raw_matched
                    break
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize reference data into memory (safe fallback)
    try:
        reference_service.load()
    except Exception as e:
        print(f"Warning: reference load: {e}")

    # 2. Database schema initialization (safe on serverless)
    try:
        init_db()
    except Exception as e:
        print(f"Warning: init_db on startup: {e}")

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="FastAPI service for QR-based passenger grievance ingestion in Delhi transit.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Vercel ASGI path restoration middleware
app.add_middleware(VercelPathRewriteMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers at both root and /api for maximum compatibility
app.include_router(feedback.router)
app.include_router(feedback.router, prefix="/api")

app.include_router(meta.router)
app.include_router(meta.router, prefix="/api")

app.include_router(admin.router)
app.include_router(admin.router, prefix="/api")


@app.get("/")
@app.get("/api")
@app.get("/api/index.py")
def root():
    return {
        "service": "TRACE Delhi Passenger Feedback API",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "feedback_form": "/feedback?r=784&v=DL1PC9421",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
