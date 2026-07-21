from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from ..base import Base


class TrackingHistory(Base):
    """
    Historical record of shipment tracking updates
    Each GPS update, status change, or location update creates a new record
    """
    __tablename__ = "tracking_history"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    tracking_number = Column(String(50), index=True, nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    
    # Status and location
    status = Column(String(50), nullable=False)  # picked_up, in_transit, out_for_delivery, delivered
    location = Column(String(500), nullable=True)  # Human-readable location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Additional details
    notes = Column(Text, nullable=True)
    distance_traveled = Column(Float, nullable=True)  # km since last update
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    shipment = relationship("Shipment")

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "status": self.status,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "notes": self.notes,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "distance_traveled": self.distance_traveled
        }

    def __repr__(self):
        return f"<TrackingHistory shipment_id={self.shipment_id} status={self.status} at {self.created_at}>"
