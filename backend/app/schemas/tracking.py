from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TrackingBase(BaseModel):
    tracking_number: str
    current_status: str
    current_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TrackingCreate(TrackingBase):
    order_id: int
    estimated_delivery: Optional[datetime] = None
    signature_required: bool = False


class TrackingUpdate(BaseModel):
    current_status: Optional[str] = None
    current_location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class Tracking(TrackingBase):
    id: int
    order_id: int
    partner_id: Optional[int] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
