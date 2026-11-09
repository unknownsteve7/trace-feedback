from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from app.config import settings
from app.database import init_db
from app.services.reference import reference_service
from app.routers import feedback, meta, admin
from app.routers.feedback import serve_feedback_form

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
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers (both at root and with /api prefix for Vercel serverless compatibility)
app.include_router(feedback.router)
app.include_router(meta.router)
app.include_router(admin.router)

app.include_router(feedback.router, prefix="/api")
app.include_router(meta.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/api/index", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
async def root(r: str = "784", v: str = "DL1PC9421"):
    # Directly render the form — NO 307 redirects to avoid proxy redirect loops
    return await serve_feedback_form(r=r, v=v)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
