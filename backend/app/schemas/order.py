from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ServiceTypeEnum(str, Enum):
    LOCAL = "local"
    INTERCITY = "intercity"
    INTERNATIONAL = "international"

class SpeedEnum(str, Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    EXPRESS = "express"

class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# ==================== Quote Schema ====================
class QuoteRequest(BaseModel):
    service_type: ServiceTypeEnum
    distance: float = Field(default=10, ge=0)
    weight: float = Field(default=1, ge=0)
    speed: SpeedEnum = SpeedEnum.STANDARD
    package_value: float = Field(default=0, ge=0)

class PriceBreakdown(BaseModel):
    base: float
    distance: float
    weight: float
    speed: str
    insurance: float

class QuoteResponse(BaseModel):
    base_fare: float
    distance_charge: float
    weight_charge: float
    speed_multiplier: float
    insurance_charge: float
    subtotal: float
    total_price: float
    breakdown: PriceBreakdown

# ==================== Order Schema ====================
class OrderCreate(BaseModel):
    service_type: ServiceTypeEnum
    speed: SpeedEnum
    
    # Pickup
    pickup_address: str
    pickup_city: str = "Local"
    pickup_zip: str = "10001"
    pickup_contact: str
    pickup_phone: str
    
    # Delivery
    delivery_address: str
    delivery_city: str = "Local"
    delivery_zip: str = "10002"
    delivery_contact: str
    delivery_phone: str
    delivery_email: EmailStr
    
    # Package
    package_type: Optional[str] = None
    package_weight: float = Field(default=1, ge=0)
    package_value: float = Field(default=0, ge=0)
    package_description: Optional[str] = None
    
    special_instructions: Optional[str] = None

class OrderResponse(BaseModel):
    id: str
    tracking_number: str
    customer_id: str
    service_type: str
    speed: str
    status: str
    total_price: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrderDetailResponse(OrderResponse):
    pickup_address: str
    delivery_address: str
    assigned_partner_id: Optional[str]
    payment_status: str
    base_fare: float
    distance_charge: float
    weight_charge: float
    insurance_charge: float

class OrderListResponse(BaseModel):
    id: str
    tracking_number: str
    status: str
    total_price: float
    created_at: datetime
    pickup_city: str
    delivery_city: str

# ==================== Tracking Schema ====================
class TrackingHistoryResponse(BaseModel):
    id: str
    status: str
    location: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ShipmentResponse(BaseModel):
    id: str
    tracking_number: str
    current_status: str
    current_location: Optional[str]
    history: List[TrackingHistoryResponse] = []
    
    class Config:
        from_attributes = True

class ProofOfDeliverySubmit(BaseModel):
    recipient_name: str
    notes: Optional[str] = None
    signature_path: Optional[str] = None
    photo_path: Optional[str] = None

# ==================== User Schema ====================
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    phone: Optional[str] = None
    role: str = "customer"
    profile: Optional[dict] = None  # For partner profile data

class UserLogin(BaseModel):
    email: str  # Accept any string for login (email or username)
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional['UserResponse'] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# ==================== Partner Schema ====================
class PartnerProfile(BaseModel):
    vehicle_type: Optional[str] = None
    service_types: Optional[List[str]] = None
    service_area: Optional[str] = None
    availability: Optional[dict] = None

class PartnerRegister(UserRegister):
    profile: Optional[PartnerProfile] = None

class PartnerResponse(UserResponse):
    profile_data: Optional[dict] = None
