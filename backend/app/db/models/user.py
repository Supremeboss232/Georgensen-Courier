from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SQLEnum
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
    is_email_verified = Column(Boolean, default=False)  # NEW: Track email verification
    role = Column(SQLEnum(UserRole), default=UserRole.customer, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    
    # LOGISTICS: Hub assignment for managers, drivers, handlers
    assigned_hub_id = Column(Integer, nullable=True, index=True)  # Will link to Hub table
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships - NEW
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    auth_logs = relationship("AuthAuditLog", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
