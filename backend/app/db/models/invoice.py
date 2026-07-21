from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..base import Base


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    issued = "issued"
    sent = "sent"
    viewed = "viewed"
    pending = "pending"  # Awaiting payment
    paid = "paid"
    failed = "failed"  # Payment failed
    refunded = "refunded"  # Refunded
    disputed = "disputed"  # Chargeback or dispute
    overdue = "overdue"
    cancelled = "cancelled"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True, index=True)
    
    # Invoice status
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.issued, nullable=False, index=True)
    
    # Amounts
    subtotal = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # Payment method
    payment_method = Column(String, nullable=True)  # credit_card, bank_transfer, stripe, etc.
    
    # Stripe payment reconciliation fields (NEW)
    stripe_payment_intent_id = Column(String, unique=True, nullable=True, index=True)
    stripe_charge_id = Column(String, unique=True, nullable=True, index=True)
    
    # Refund tracking (NEW)
    refund_amount = Column(Float, default=0.0)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dispute tracking (NEW)
    dispute_id = Column(String, nullable=True, index=True)
    
    # Failure tracking (NEW)
    failure_reason = Column(Text, nullable=True)
    
    # Legacy fields
    transaction_id = Column(String, unique=True, nullable=True)
    notes = Column(Text, nullable=True)
    payment_terms = Column(String, default="Due on receipt")
    
    # Dates
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)  # Renamed from paid_date for clarity
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    shipment = relationship("Shipment", back_populates="invoices")

    # Indexes for query optimization
    __table_args__ = (
        Index('idx_invoice_customer_status', 'customer_id', 'status'),
        Index('idx_invoice_stripe_intent', 'stripe_payment_intent_id'),
        Index('idx_invoice_created_status', 'created_at', 'status'),
    )

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.status}>"
