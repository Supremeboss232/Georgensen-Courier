from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..base import Base


class POD(Base):
    __tablename__ = "proof_of_delivery"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    tracking_id = Column(Integer, ForeignKey("tracking.id"), nullable=False)
    recipient_name = Column(String, nullable=False)
    recipient_email = Column(String, nullable=True)
    signature_url = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    delivery_time = Column(DateTime(timezone=True), nullable=False)
    location_latitude = Column(String, nullable=True)
    location_longitude = Column(String, nullable=True)
    delivery_notes = Column(Text, nullable=True)
    items_verified = Column(Boolean, default=False)
    condition_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    shipment = relationship("Shipment", back_populates="proof_of_delivery")

    def __repr__(self):
        return f"<POD shipment_id={self.shipment_id}>"
