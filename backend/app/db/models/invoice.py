from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from ..base import Base


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    issued = "issued"
    sent = "sent"
    viewed = "viewed"
    pending = "pending"
    partial = "partial"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"
    disputed = "disputed"
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
    subtotal = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    
    # Payment method
    payment_method = Column(String, nullable=True)
    
    # Payment reconciliation fields
    stripe_payment_intent_id = Column(String, unique=True, nullable=True, index=True)
    stripe_charge_id = Column(String, unique=True, nullable=True, index=True)
    
    # Refund tracking
    refund_amount = Column(Float, default=0.0)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dispute tracking
    dispute_id = Column(String, nullable=True, index=True)
    
    # Failure tracking
    failure_reason = Column(Text, nullable=True)
    
    # Legacy fields
    transaction_id = Column(String, unique=True, nullable=True)
    notes = Column(Text, nullable=True)
    payment_terms = Column(String, default="Due on receipt")
    
    # Dates
    issued_date = Column(DateTime(timezone=True), server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    shipment = relationship("Shipment", back_populates="invoices")

    __table_args__ = (
        Index('idx_invoice_customer_status', 'customer_id', 'status'),
        Index('idx_invoice_stripe_intent', 'stripe_payment_intent_id'),
        Index('idx_invoice_created_status', 'created_at', 'status'),
    )

    # Compatibility properties for Customer & Payment routers
    @property
    def amount_due(self) -> float:
        return float(self.total_amount or 0.0)

    @amount_due.setter
    def amount_due(self, value: float):
        self.total_amount = float(value or 0.0)
        if not self.subtotal:
            self.subtotal = float(value or 0.0)

    @property
    def amount_paid(self) -> float:
        st = self.status.value if hasattr(self.status, "value") else str(self.status)
        if st == "paid":
            return float(self.total_amount or 0.0)
        return 0.0

    @amount_paid.setter
    def amount_paid(self, value: float):
        if float(value or 0.0) >= float(self.total_amount or 0.0) and float(self.total_amount or 0.0) > 0:
            self.status = InvoiceStatus.paid

    @property
    def issue_date(self):
        return self.issued_date

    @issue_date.setter
    def issue_date(self, value):
        self.issued_date = value

    @property
    def paid_date(self):
        return self.paid_at

    @paid_date.setter
    def paid_date(self, value):
        self.paid_at = value

    @property
    def description(self) -> str:
        return self.notes or f"Invoice {self.invoice_number}"

    @description.setter
    def description(self, value: str):
        self.notes = value

    @property
    def stripe_payment_intent(self) -> str:
        return self.stripe_payment_intent_id

    @stripe_payment_intent.setter
    def stripe_payment_intent(self, value: str):
        self.stripe_payment_intent_id = value

    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.status}>"
