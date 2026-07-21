from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.sql import func
import enum
from ..base import Base


class PartnerStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    active = "active"
    suspended = "suspended"
    inactive = "inactive"


class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    business_name = Column(String, nullable=False)
    business_registration = Column(String, unique=True, nullable=False)
    contact_person = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=False)
    business_address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    bank_account = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    account_holder = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)  # e.g., 'car', 'bike', 'van'
    vehicle_registration = Column(String, nullable=True)
    insurance_expiry = Column(DateTime(timezone=True), nullable=True)
    license_number = Column(String, nullable=True)
    status = Column(SQLEnum(PartnerStatus), default=PartnerStatus.pending, nullable=False)
    rating = Column(Float, default=0.0)
    completed_orders = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Partner {self.business_name}>"
