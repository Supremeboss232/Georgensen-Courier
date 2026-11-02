"""
Shipment model for tracking deliveries
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
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
    pickup_state = Column(String(2), nullable=False, default="ON")
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
    delivery_state = Column(String(2), nullable=False, default="ON")
    delivery_zip = Column(String(10), nullable=False)
    estimated_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    
    # LOGISTICS: Destination hub assignment  
    destination_hub_id = Column(Integer, ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    
    # Package information
    package_type = Column(String(100), nullable=False, default="box")
    package_weight = Column(Float, nullable=False, default=1.0)
    package_dimensions = Column(String(50), nullable=True)
    package_value = Column(Float, nullable=True, default=0.0)
    package_description = Column(Text, nullable=True)
    
    # Pricing
    quoted_price = Column(Float, nullable=False, default=0.0)
    actual_cost = Column(Float, nullable=True)
    insurance_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    base_fare = Column(Float, default=0.0, nullable=True)
    distance_charge = Column(Float, default=0.0, nullable=True)
    weight_charge = Column(Float, default=0.0, nullable=True)
    partner_payout = Column(Float, nullable=True)
    payment_status = Column(String(50), default="pending", nullable=True)
    
    # Global / Multi-region metadata
    origin_country = Column(String(10), default="CA", nullable=True)
    destination_country = Column(String(10), default="CA", nullable=True)
    currency = Column(String(10), default="CAD", nullable=True)
    estimated_distance_km = Column(Float, default=10.0, nullable=True)
    customs_status = Column(String(50), default="cleared", nullable=True)
    
    # Current location tracking - LOGISTICS CRITICAL
    current_location = Column(String(500), nullable=True)
    current_hub_id = Column(Integer, ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    
    # LOGISTICS: Handler assignment (driver or warehouse staff)
    assigned_handler_id = Column(Integer, ForeignKey("handlers.id", ondelete="SET NULL"), nullable=True)
    assigned_vehicle_id = Column(Integer, ForeignKey("fleet_vehicles.id", ondelete="SET NULL"), nullable=True)
    
    # LOGISTICS: State locking and proof of delivery
    is_locked = Column(Boolean, default=False)
    delivery_proof_signature = Column(Text, nullable=True)
    delivery_proof_photo = Column(String(500), nullable=True)
    signature_required = Column(Boolean, default=False)
    
    # Notes
    special_instructions = Column(Text, nullable=True)
    delivery_instructions = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Partner assignment
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

    # Compatibility properties for unified Order / Shipment access
    @property
    def partner_id(self):
        return self.assigned_partner_id

    @partner_id.setter
    def partner_id(self, value):
        self.assigned_partner_id = value

    @property
    def total_price(self) -> float:
        if self.actual_cost is not None:
            return float(self.actual_cost)
        return float(self.quoted_price or 0.0)

    @total_price.setter
    def total_price(self, value: float):
        self.quoted_price = value
        self.actual_cost = value

    @property
    def total_value(self) -> float:
        return self.total_price

    @property
    def weight(self) -> float:
        return float(self.package_weight or 0.0)

    @weight.setter
    def weight(self, value: float):
        self.package_weight = value

    @property
    def delivered_at(self):
        return self.actual_delivery

    @delivered_at.setter
    def delivered_at(self, value):
        self.actual_delivery = value

    @property
    def insurance_charge(self) -> float:
        return float(self.insurance_amount or 0.0)

    @insurance_charge.setter
    def insurance_charge(self, value: float):
        self.insurance_amount = value

    @property
    def current_status(self) -> str:
        return str(self.status)

    @current_status.setter
    def current_status(self, value: str):
        self.status = value

    @property
    def pickup_contact(self) -> str:
        return self.pickup_contact_name

    @pickup_contact.setter
    def pickup_contact(self, value: str):
        self.pickup_contact_name = value

    @property
    def delivery_contact(self) -> str:
        return self.delivery_contact_name

    @delivery_contact.setter
    def delivery_contact(self, value: str):
        self.delivery_contact_name = value

    def __repr__(self):
        return f"<Shipment {self.tracking_number}>"
