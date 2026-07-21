"""
ShipmentLog model for detailed audit trail - "Chain of Custody"
Every status change, scan, or location update creates a new log entry
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..base import Base


class LogAction(str, enum.Enum):
    """Actions that create log entries"""
    # Origin
    order_received = "order_received"
    payment_confirmed = "payment_confirmed"
    
    # Warehouse
    scanned = "scanned"
    sorted = "sorted"
    dispatched = "dispatched"
    packed = "packed"
    
    # In Transit
    pickup_started = "pickup_started"
    picked_up = "picked_up"
    in_transit = "in_transit"
    at_hub = "at_hub"
    departed_hub = "departed_hub"
    
    # Delivery
    out_for_delivery = "out_for_delivery"
    delivery_attempt = "delivery_attempt"
    delivered = "delivered"
    delivery_failed = "delivery_failed"
    returned = "returned"
    
    # Other
    damaged = "damaged"
    lost = "lost"
    manual_override = "manual_override"


class ShipmentLog(Base):
    """
    Detailed audit trail for a shipment's journey
    This is the "Chain of Custody" - every touch point, every status change is logged
    Critical for logistics operations and proof of delivery
    """
    __tablename__ = "shipment_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Shipment reference
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    tracking_number = Column(String(50), nullable=False, index=True)
    
    # Status transition
    action = Column(SQLEnum(LogAction), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)  # Previous shipment status
    new_status = Column(String(50), nullable=True)  # New shipment status
    
    # Handler information - who scanned/processed it
    handler_id = Column(Integer, ForeignKey("handlers.id"), nullable=True)
    handler_name = Column(String(255), nullable=True)  # Backup handler name for auditing
    
    # Hub information - where it was processed
    hub_id = Column(Integer, ForeignKey("hubs.id"), nullable=True)
    hub_name = Column(String(255), nullable=True)  # Backup hub name
    
    # Vehicle information - if in transit
    vehicle_id = Column(Integer, ForeignKey("fleet_vehicles.id"), nullable=True)
    vehicle_plate = Column(String(50), nullable=True)  # Backup plate number
    
    # Geographic data - exact location of this event
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(500), nullable=True)  # Human-readable location
    
    # Verification data
    barcode_scanned = Column(String(255), nullable=True)  # Barcode/QR code read
    device_id = Column(String(50), nullable=True)  # Scanner or mobile device ID
    
    # Additional information
    notes = Column(Text, nullable=True)
    proof_image_url = Column(String(500), nullable=True)  # Photo/signature for POD
    distance_from_destination = Column(Float, nullable=True)  # km to final destination
    
    # Proof of Action
    is_verified = Column(Boolean, default=False)  # Has this log been verified?
    verification_method = Column(String(50), nullable=True)  # barcode_scan, gps, manual, webhook
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    shipment = relationship("Shipment", back_populates="logs")
    handler = relationship("Handler", back_populates="shipment_logs")

    def __repr__(self):
        return f"<ShipmentLog shipment_id={self.shipment_id} action={self.action} at {self.timestamp}>"
