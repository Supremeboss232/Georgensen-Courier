from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.sql import func
import enum
from ..base import Base


class DisputeStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"
    rejected = "rejected"


class DisputeType(str, enum.Enum):
    delivery_failure = "delivery_failure"
    quality_issue = "quality_issue"
    missing_items = "missing_items"
    damage = "damage"
    other = "other"


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    dispute_number = Column(String, unique=True, index=True, nullable=False)
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dispute_type = Column(SQLEnum(DisputeType), nullable=False)
    status = Column(SQLEnum(DisputeStatus), default=DisputeStatus.open, nullable=False)
    priority = Column(String, default="medium")  # low, medium, high, critical
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    evidence_url = Column(String, nullable=True)
    resolution = Column(Text, nullable=True)
    refund_amount = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Dispute {self.dispute_number}>"
