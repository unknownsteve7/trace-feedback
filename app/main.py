from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings
from app.database import init_db
from app.services.reference import reference_service
from app.routers import feedback, meta, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize reference data into memory (safe fallback)
    try:
        reference_service.load()
    except Exception as e:
        print(f"Warning: reference load: {e}")

    # 2. Database schema initialization (safe on serverless)
    try:
        await init_db()
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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(feedback.router)
app.include_router(meta.router)
app.include_router(admin.router)

@app.get("/")
async def root():
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
