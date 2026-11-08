import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from app.database import Base

class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    received_at_utc = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    route_id = Column(String(50), nullable=False, index=True)
    vehicle_id = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(String(300), nullable=True)
    device_hash = Column(String(64), nullable=False, index=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Feedback(id={self.feedback_id}, route={self.route_id}, vehicle={self.vehicle_id}, cat={self.category})>"
