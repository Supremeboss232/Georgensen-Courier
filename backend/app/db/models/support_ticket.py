"""
Support ticket model for customer issues and inquiries
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base


class TicketStatus(str, enum.Enum):
    """Support ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketCategory(str, enum.Enum):
    """Support ticket category"""
    BILLING = "billing"
    DELIVERY = "delivery"
    LOST = "lost"
    DAMAGED = "damaged"
    DISPUTE = "dispute"
    ACCOUNT = "account"
    OTHER = "other"


class TicketPriority(str, enum.Enum):
    """Support ticket priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SupportTicket(Base):
    """Customer support ticket"""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="SET NULL"), nullable=True)
    
    subject = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), default=TicketCategory.OTHER)
    priority = Column(String(50), default=TicketPriority.NORMAL)
    status = Column(String(50), default=TicketStatus.OPEN, index=True)
    
    resolution_notes = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="support_tickets")
    shipment = relationship("Shipment", foreign_keys=[shipment_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<SupportTicket {self.id} - {self.subject}>"
