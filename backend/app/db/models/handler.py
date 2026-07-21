"""
Handler model for warehouse staff and drivers who physically handle shipments
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..base import Base


class HandlerType(str, enum.Enum):
    """Type of handler"""
    warehouse_staff = "warehouse_staff"  # Sorts, scans packages at hub
    driver = "driver"  # Picks up and delivers


class HandlerStatus(str, enum.Enum):
    """Handler operational status"""
    active = "active"
    on_leave = "on_leave"
    inactive = "inactive"
    suspended = "suspended"


class Handler(Base):
    """
    Handler entity - warehouse staff or drivers who physically interact with shipments
    Each handler is assigned to a hub and tracks their scanning/delivery actions via ShipmentLog
    """
    __tablename__ = "handlers"

    id = Column(Integer, primary_key=True, index=True)
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Personal information
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    
    # Operational details
    handler_type = Column(SQLEnum(HandlerType), nullable=False)
    hub_id = Column(Integer, ForeignKey("hubs.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(HandlerStatus), default=HandlerStatus.active, nullable=False)
    
    # License/Certification (for drivers)
    license_number = Column(String(50), nullable=True)
    license_expiry = Column(DateTime(timezone=True), nullable=True)
    license_category = Column(String(10), nullable=True)  # e.g., "B", "C", "D"
    
    # Employment information
    employee_id = Column(String(50), nullable=True, unique=True)
    hire_date = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    
    # Badge/Scanner information
    badge_number = Column(String(50), nullable=True, unique=True)  # RFID badge for warehouse access
    scanner_id = Column(String(50), nullable=True)  # Handheld scanner device ID
    
    # Notes and metadata
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    hub = relationship("Hub", back_populates="handlers")
    shipment_logs = relationship("ShipmentLog", back_populates="handler", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Handler {self.full_name} ({self.handler_type})>"
