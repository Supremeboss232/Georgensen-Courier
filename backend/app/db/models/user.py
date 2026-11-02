from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..base import Base


class UserRole(str, enum.Enum):
    # System-wide roles
    system_admin = "system_admin"  # Full visibility, global metrics, user management
    
    # Logistics-specific roles
    warehouse_manager = "warehouse_manager"  # Manages specific hub, staff scheduling
    driver = "driver"  # Handles in-transit phase, pickup/delivery, POD upload
    handler = "handler"  # Warehouse staff who scan packages
    
    # Legacy roles (kept for backward compatibility)
    admin = "admin"
    customer = "customer"
    partner = "partner"
    support = "support"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    role = Column(SQLEnum(UserRole), default=UserRole.customer, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    
    # LOGISTICS: Hub assignment for managers, drivers, handlers
    assigned_hub_id = Column(Integer, nullable=True, index=True)
    profile_data = Column(JSON, default=dict, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    auth_logs = relationship("AuthAuditLog", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")

    @property
    def status(self) -> str:
        if isinstance(self.profile_data, dict) and "status" in self.profile_data:
            return self.profile_data["status"]
        return "active" if self.is_active else "inactive"

    @status.setter
    def status(self, value: str):
        self.is_active = value in ("active", "approved", "verified")
        data = dict(self.profile_data or {})
        data["status"] = value
        self.profile_data = data

    @property
    def primary_region(self) -> str:
        if isinstance(self.profile_data, dict):
            return self.profile_data.get("primary_region", "NA")
        return "NA"

    @property
    def compliance_status(self) -> str:
        if isinstance(self.profile_data, dict):
            return self.profile_data.get("compliance_status", "verified")
        return "verified"

    @property
    def kyc_status(self) -> str:
        if isinstance(self.profile_data, dict):
            return self.profile_data.get("kyc_status", "verified")
        return "verified"

    def __repr__(self):
        return f"<User {self.email}>"
