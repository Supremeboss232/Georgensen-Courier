from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..base import Base


class Customer(Base):
    """
    Customer entity - separate from User model (which is auth/identity only)
    A Customer owns shipments, invoices, addresses, and support tickets
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Profile information
    company_name = Column(String, nullable=True)
    tax_id = Column(String, nullable=True, unique=True)
    phone = Column(String, nullable=True)
    
    # Billing information
    billing_address = Column(String, nullable=True)
    billing_city = Column(String, nullable=True)
    billing_state = Column(String, nullable=True)
    billing_zip = Column(String, nullable=True)
    
    # Shipping preferences
    default_return_address = Column(String, nullable=True)
    preferred_service_type = Column(String, default="local")
    preferred_pickup_time = Column(String, nullable=True)  # e.g., "09:00-12:00"
    
    # Account settings
    account_type = Column(String, default="individual")  # individual, business, enterprise
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    total_shipments = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    account_balance = Column(Float, default=0.0)  # Prepaid balance or credit
    average_rating = Column(Float, default=0.0)
    
    # Preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    promotional_emails = Column(Boolean, default=True)
    
    # Notes & metadata
    internal_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_shipment_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    addresses = relationship("Address", back_populates="customer", cascade="all, delete-orphan")
    support_tickets = relationship("SupportTicket", back_populates="customer", cascade="all, delete-orphan")
    shipments = relationship("Shipment", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer user_id={self.user_id}>"
