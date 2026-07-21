"""
Fleet Vehicle model for trucks, vans, and delivery vehicles
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..base import Base


class VehicleStatus(str, enum.Enum):
    """Vehicle operational status"""
    available = "available"
    in_use = "in_use"
    maintenance = "maintenance"
    decommissioned = "decommissioned"
    inactive = "inactive"


class VehicleType(str, enum.Enum):
    """Type of vehicle for different delivery needs"""
    motorcycle = "motorcycle"
    car = "car"
    van = "van"
    truck = "truck"
    cargo = "cargo"


class FleetVehicle(Base):
    """
    Fleet vehicle entity - trucks, vans, motorcycles used for deliveries
    Each vehicle is assigned to a hub and tracked for location and capacity
    """
    __tablename__ = "fleet_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    
    # Vehicle identification
    plate_number = Column(String(50), nullable=False, unique=True, index=True)
    vin = Column(String(50), nullable=True, unique=True)  # Vehicle Identification Number
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    color = Column(String(50), nullable=True)
    
    # Operational details
    hub_id = Column(Integer, ForeignKey("hubs.id", ondelete="CASCADE"), nullable=False, index=True)
    current_driver_id = Column(Integer, ForeignKey("handlers.id"), nullable=True)  # Current assigned driver
    
    # Capacity specifications
    weight_capacity = Column(Float, nullable=False)  # in kg
    volume_capacity = Column(Float, nullable=False)  # in cubic meters
    max_packages = Column(Integer, nullable=False)  # Max number of packages
    
    # Current load
    current_weight = Column(Float, default=0.0)  # Current load weight
    current_packages = Column(Integer, default=0)  # Current number of packages
    
    # Location tracking
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    last_location_update = Column(DateTime(timezone=True), nullable=True)
    
    # Status and certification
    status = Column(SQLEnum(VehicleStatus), default=VehicleStatus.available, nullable=False)
    registration_expiry = Column(DateTime(timezone=True), nullable=True)
    insurance_expiry = Column(DateTime(timezone=True), nullable=True)
    inspection_expiry = Column(DateTime(timezone=True), nullable=True)
    
    # Maintenance and usage
    mileage = Column(Float, default=0.0)  # Current odometer reading
    next_maintenance_date = Column(DateTime(timezone=True), nullable=True)
    fuel_type = Column(String(50), nullable=True)  # diesel, petrol, electric, hybrid
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    hub = relationship("Hub", back_populates="fleet_vehicles")

    def __repr__(self):
        return f"<FleetVehicle {self.plate_number}>"
