from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class FeedbackCreate(BaseModel):
    route_id: str = Field(..., min_length=1, max_length=50, description="DTC Route ID")
    vehicle_id: str = Field(..., min_length=1, max_length=50, description="Vehicle Registration ID")
    category: str = Field(..., min_length=2, max_length=100, description="Feedback category")
    rating: int = Field(..., ge=1, le=5, description="Satisfaction rating (1 to 5 stars)")
    comment: Optional[str] = Field(None, max_length=300, description="Optional passenger remarks")
    
    # Anti-Spam Honeypot field (must be empty from legitimate humans)
    website: Optional[str] = Field(None, description="Honeypot field — should be empty")

    @field_validator("comment")
    @classmethod
    def sanitize_comment(cls, v: Optional[str]) -> Optional[str]:
        if v:
            cleaned = v.strip()
            return cleaned if cleaned else None
        return None

class FeedbackResponse(BaseModel):
    feedback_id: str
    received_at_utc: datetime
    status: str = "received"
    message: str = "Thank you. Your feedback has been recorded."

class FeedbackAdminOut(BaseModel):
    feedback_id: str
    received_at_utc: datetime
    route_id: str
    vehicle_id: str
    category: str
    rating: int
    comment: Optional[str]
    device_hash: str
    is_synthetic: bool

    model_config = {"from_attributes": True}

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"
