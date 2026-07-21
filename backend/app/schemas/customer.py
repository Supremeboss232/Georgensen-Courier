"""
Customer schemas for Pydantic validation
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class AddressBase(BaseModel):
    """Base address fields"""
    street_address: str = Field(..., min_length=5, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    postal_code: str = Field(..., min_length=5, max_length=10)
    country: str = Field(default="USA", max_length=100)
    address_type: str = Field(..., pattern="^(residential|business|warehouse)$")
    is_default: bool = False
    delivery_instructions: Optional[str] = Field(None, max_length=500)


class AddressCreate(AddressBase):
    """Address creation"""
    pass


class AddressUpdate(BaseModel):
    """Address updates"""
    street_address: Optional[str] = Field(None, min_length=5, max_length=255)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    postal_code: Optional[str] = Field(None, min_length=5, max_length=10)
    country: Optional[str] = Field(None, max_length=100)
    address_type: Optional[str] = None
    is_default: Optional[bool] = None
    delivery_instructions: Optional[str] = Field(None, max_length=500)


class AddressResponse(AddressBase):
    """Address response with metadata"""
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    """Base customer fields"""
    company_name: str = Field(..., min_length=2, max_length=255)
    account_type: str = Field(..., pattern="^(individual|business|enterprise)$")
    phone: Optional[str] = Field(None, max_length=20)
    email_verified: bool = False
    phone_verified: bool = False


class CustomerCreate(CustomerBase):
    """Customer creation"""
    user_id: int


class CustomerUpdate(BaseModel):
    """Customer updates"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    account_type: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Customer response with metadata"""
    id: int
    user_id: int
    total_shipments: int = 0
    total_spent: float = 0.0
    account_balance: float = 0.0
    email_notifications: bool = True
    sms_notifications: bool = False
    created_at: datetime
    updated_at: datetime
    addresses: List[AddressResponse] = []

    class Config:
        from_attributes = True


class CustomerDashboard(BaseModel):
    """Customer dashboard data"""
    customer_info: CustomerResponse
    recent_shipments: List[dict] = []
    pending_invoices: int = 0
    outstanding_balance: float = 0.0
    total_shipments_month: int = 0
    stats: dict = {
        "total_shipments": 0,
        "total_spent": 0.0,
        "avg_shipment_value": 0.0,
        "on_time_rate": 0.0
    }


class SupportTicketBase(BaseModel):
    """Base support ticket fields"""
    subject: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10, max_length=5000)
    category: str = Field(..., pattern="^(billing|delivery|lost|damaged|other)$")
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    related_shipment_id: Optional[int] = None


class SupportTicketCreate(SupportTicketBase):
    """Support ticket creation"""
    pass


class SupportTicketUpdate(BaseModel):
    """Support ticket updates"""
    status: Optional[str] = Field(None, pattern="^(open|in_progress|resolved|closed)$")
    resolution_notes: Optional[str] = Field(None, max_length=5000)


class SupportTicketResponse(SupportTicketBase):
    """Support ticket response"""
    id: int
    customer_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    resolution_notes: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentMethodBase(BaseModel):
    """Base payment method fields"""
    method_type: str = Field(..., pattern="^(credit_card|bank_transfer|ach)$")
    is_default: bool = False
    is_active: bool = True


class PaymentMethodResponse(PaymentMethodBase):
    """Payment method response"""
    id: int
    customer_id: int
    last_four: str  # Last 4 digits of card or account
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    """Invoice response"""
    id: int
    customer_id: int
    invoice_number: str
    amount_due: float
    amount_paid: float
    issue_date: datetime
    due_date: datetime
    status: str  # draft, sent, viewed, partial, paid, overdue
    items_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ShipmentResponse(BaseModel):
    """Shipment response for customer"""
    id: int
    customer_id: int
    tracking_number: str
    status: str
    pickup_location: dict
    delivery_location: dict
    weight: float
    service_type: str
    quoted_price: float
    actual_cost: Optional[float] = None
    estimated_delivery: datetime
    actual_delivery: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
