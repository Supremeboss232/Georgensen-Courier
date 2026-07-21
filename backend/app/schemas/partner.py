from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PartnerBase(BaseModel):
    business_name: str
    business_registration: str
    contact_person: str
    contact_email: str
    contact_phone: str
    business_address: str
    city: str
    state: str
    postal_code: str
    vehicle_type: Optional[str] = None
    vehicle_registration: Optional[str] = None


class PartnerCreate(PartnerBase):
    user_id: int
    bank_account: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    license_number: Optional[str] = None


class PartnerUpdate(BaseModel):
    business_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    business_address: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_registration: Optional[str] = None


class Partner(PartnerBase):
    id: int
    user_id: int
    status: str
    rating: float
    completed_orders: int
    total_earnings: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
