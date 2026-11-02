from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Union
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
    OVERNIGHT = "overnight"


class OrderStatusEnum(str, Enum):
    ORDER_RECEIVED = "order_received"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED_DELIVERY = "failed_delivery"
    CANCELLED = "cancelled"


# ==================== Quote Schema ====================
class QuoteRequest(BaseModel):
    service_type: ServiceTypeEnum = ServiceTypeEnum.LOCAL
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
    service_type: ServiceTypeEnum = ServiceTypeEnum.LOCAL
    speed: SpeedEnum = SpeedEnum.STANDARD
    
    # Pickup
    pickup_address: str
    pickup_city: str = "Toronto"
    pickup_state: str = "ON"
    pickup_zip: str = "M5V 2T6"
    pickup_contact: str = "Sender"
    pickup_phone: str = "+1-800-555-0100"
    
    # Delivery
    delivery_address: str
    delivery_city: str = "Toronto"
    delivery_state: str = "ON"
    delivery_zip: str = "M5J 2N8"
    delivery_contact: str = "Recipient"
    delivery_phone: str = "+1-800-555-0199"
    delivery_email: Optional[EmailStr] = None
    
    # Package
    package_type: Optional[str] = "box"
    package_weight: float = Field(default=1, ge=0)
    package_value: float = Field(default=0, ge=0)
    package_description: Optional[str] = None
    
    special_instructions: Optional[str] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Union[int, str]
    tracking_number: str
    customer_id: Optional[Union[int, str]] = None
    service_type: str
    speed: str
    status: str
    total_price: float
    created_at: Optional[datetime] = None


class OrderDetailResponse(OrderResponse):
    pickup_address: str
    delivery_address: str
    assigned_partner_id: Optional[Union[int, str]] = None
    payment_status: Optional[str] = "pending"
    base_fare: Optional[float] = 0.0
    distance_charge: Optional[float] = 0.0
    weight_charge: Optional[float] = 0.0
    insurance_charge: Optional[float] = 0.0


class OrderListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Union[int, str]
    tracking_number: str
    status: str
    total_price: float
    created_at: Optional[datetime] = None
    pickup_city: Optional[str] = None
    delivery_city: Optional[str] = None


# ==================== Tracking Schema ====================
class TrackingHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Union[int, str]
    status: str
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Union[int, str]
    tracking_number: str
    current_status: str
    current_location: Optional[str] = None
    history: List[TrackingHistoryResponse] = []


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
    profile: Optional[dict] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


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
