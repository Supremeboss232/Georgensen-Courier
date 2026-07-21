from sqlalchemy import Column, String, DateTime, JSON
from app.db.base import Base
from datetime import datetime, timezone

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    event_id = Column(String, primary_key=True, index=True)
    provider = Column(String, nullable=False)  # e.g., "stripe", "fedex"
    event_type = Column(String, nullable=False)  # e.g., "payment_intent.succeeded"
    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    payload = Column(JSON, nullable=True)
