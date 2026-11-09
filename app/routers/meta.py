from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas import HealthResponse
from app.services.reference import reference_service

router = APIRouter(tags=["Metadata"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/categories", response_model=list[str])
def get_categories():
    return reference_service.categories
