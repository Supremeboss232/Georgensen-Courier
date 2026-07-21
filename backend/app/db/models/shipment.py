"""
Shipment model for tracking deliveries
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base


class ShipmentStatus(str, enum.Enum):
    """Shipment status"""
    ORDER_RECEIVED = "order_received"
    PROCESSING = "processing"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED_DELIVERY = "failed_delivery"
    CANCELLED = "cancelled"


class Shipment(Base):
    """Shipment entity for order fulfillment - Production Logistics Grade"""
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    tracking_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Service details
    service_type = Column(String(50), nullable=False)  # local, intercity, international
    speed = Column(String(50), nullable=False)  # economy, standard, express
    status = Column(String(50), default=ShipmentStatus.ORDER_RECEIVED, index=True)
    
    # Pickup information
    pickup_contact_name = Column(String(255), nullable=False)
    pickup_phone = Column(String(20), nullable=False)
    pickup_address = Column(String(500), nullable=False)
    pickup_city = Column(String(100), nullable=False)
    pickup_state = Column(String(2), nullable=False)
    pickup_zip = Column(String(10), nullable=False)
    pickup_at = Column(DateTime, nullable=True)
    
    # LOGISTICS: Pickup hub assignment
    origin_hub_id = Column(Integer, ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    
    # Delivery information
    delivery_contact_name = Column(String(255), nullable=False)
    delivery_phone = Column(String(20), nullable=False)
    delivery_email = Column(String(255), nullable=True)
    delivery_address = Column(String(500), nullable=False)
    delivery_city = Column(String(100), nullable=False)
    delivery_state = Column(String(2), nullable=False)
    delivery_zip = Column(String(10), nullable=False)
    estimated_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    
    # LOGISTICS: Destination hub assignment  
    destination_hub_id = Column(Integer, ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    
    # Package information
    package_type = Column(String(100), nullable=False)  # box, envelope, pallet
    package_weight = Column(Float, nullable=False)  # in kg
    package_dimensions = Column(String(50), nullable=True)  # LxWxH
    package_value = Column(Float, nullable=True)
    package_description = Column(Text, nullable=True)
    
    # Pricing
    quoted_price = Column(Float, nullable=False)
    actual_cost = Column(Float, nullable=True)
    insurance_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    
    # Current location tracking - LOGISTICS CRITICAL
    current_location = Column(String(500), nullable=True)
    current_hub_id = Column(Integer, ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)  # Where is it NOW
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    
    # LOGISTICS: Handler assignment (driver or warehouse staff)
    assigned_handler_id = Column(Integer, ForeignKey("handlers.id", ondelete="SET NULL"), nullable=True)
    assigned_vehicle_id = Column(Integer, ForeignKey("fleet_vehicles.id", ondelete="SET NULL"), nullable=True)
    
    # LOGISTICS: State locking and proof of delivery
    is_locked = Column(Boolean, default=False)  # Once delivered, becomes read-only
    delivery_proof_signature = Column(Text, nullable=True)  # Base64 encoded signature
    delivery_proof_photo = Column(String(500), nullable=True)  # URL to photo
    signature_required = Column(Boolean, default=False)
    
    # Notes
    special_instructions = Column(Text, nullable=True)
    delivery_instructions = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Partner assignment (legacy support)
    assigned_partner_id = Column(Integer, ForeignKey("partners.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="shipments")
    partner = relationship("Partner")
    tracking = relationship("Tracking", back_populates="shipment", cascade="all, delete-orphan")
    proof_of_delivery = relationship("POD", uselist=False, back_populates="shipment")
    invoices = relationship("Invoice", back_populates="shipment", cascade="all, delete-orphan")
    
    # LOGISTICS: Audit trail and chain of custody
    logs = relationship("ShipmentLog", back_populates="shipment", cascade="all, delete-orphan")
    origin_hub = relationship("Hub", foreign_keys=[origin_hub_id])
    destination_hub = relationship("Hub", foreign_keys=[destination_hub_id])
    current_hub = relationship("Hub", foreign_keys=[current_hub_id])

    def __repr__(self):
        return f"<Shipment {self.tracking_number}>"
