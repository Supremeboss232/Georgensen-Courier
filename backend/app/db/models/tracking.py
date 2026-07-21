from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..base import Base


class TrackingStatus(str, enum.Enum):
    pending = "pending"
    pickup_scheduled = "pickup_scheduled"
    picked_up = "picked_up"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    failed_delivery = "failed_delivery"
    returned = "returned"
    cancelled = "cancelled"


class Tracking(Base):
    __tablename__ = "tracking"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    tracking_number = Column(String, unique=True, index=True, nullable=False)
    current_status = Column(SQLEnum(TrackingStatus), default=TrackingStatus.pending, nullable=False)
    current_location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    estimated_delivery = Column(DateTime(timezone=True), nullable=True)
    actual_delivery = Column(DateTime(timezone=True), nullable=True)
    signature_required = Column(Boolean, default=False)
    delivery_proof_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shipment = relationship("Shipment", back_populates="tracking")

    def __repr__(self):
        return f"<Tracking {self.tracking_number}>"
