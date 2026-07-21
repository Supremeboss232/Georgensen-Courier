"""
Hub/Warehouse model for logistics infrastructure
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..base import Base


class HubStatus(str, enum.Enum):
    """Status of a hub/warehouse"""
    active = "active"
    maintenance = "maintenance"
    closed = "closed"
    pending = "pending"


class Hub(Base):
    """
    Warehouse/Hub entity - physical location where packages are sorted and stored
    Multiple hubs form the network backbone of the logistics operation
    """
    __tablename__ = "hubs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)  # e.g., "HUB-NYC", "HUB-LA"
    
    # Location information
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(2), nullable=False)
    postal_code = Column(String(10), nullable=False)
    
    # Geographic coordinates (for route optimization, distance calculation)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Capacity and operations
    sorting_capacity = Column(Integer, nullable=True)  # Max packages per day
    storage_capacity = Column(Integer, nullable=True)  # Max packages in storage
    operating_hours_start = Column(String(5), nullable=True)  # "08:00"
    operating_hours_end = Column(String(5), nullable=True)  # "18:00"
    
    # Contact information
    manager_name = Column(String(255), nullable=True)
    manager_email = Column(String(255), nullable=True)
    manager_phone = Column(String(20), nullable=True)
    
    # Status and metadata
    status = Column(SQLEnum(HubStatus), default=HubStatus.active, nullable=False)
    is_regional_hub = Column(Boolean, default=False)  # If true, this hub distributes to smaller hubs
    parent_hub_id = Column(Integer, nullable=True)  # For hierarchical hub structure
    
    # Statistics
    total_capacity = Column(Integer, default=0)  # Current total capacity
    available_capacity = Column(Integer, default=0)  # Currently available capacity
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    fleet_vehicles = relationship("FleetVehicle", back_populates="hub", cascade="all, delete-orphan")
    handlers = relationship("Handler", back_populates="hub", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Hub {self.code}>"
