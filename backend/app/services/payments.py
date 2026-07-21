"""Payment processing service"""
from typing import Optional
from sqlalchemy.orm import Session
from ..db.models.invoice import Invoice, InvoiceStatus
import logging

logger = logging.getLogger(__name__)


class PaymentService:
    """Handle payment processing and transactions"""

    @staticmethod
    async def process_payment(
        invoice_id: int,
        payment_method: str,
        amount: float,
        db: Session
    ) -> dict:
        """Process payment for an invoice"""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {"success": False, "error": "Invoice not found"}

        if invoice.status == InvoiceStatus.paid:
            return {"success": False, "error": "Invoice already paid"}

        try:
            # Process payment with payment gateway
            transaction_id = await PaymentService._process_with_gateway(
                amount, payment_method
            )
            
            # Update invoice
            invoice.status = InvoiceStatus.paid
            invoice.payment_method = payment_method
            invoice.transaction_id = transaction_id
            db.commit()
            
            logger.info(f"Payment processed: invoice {invoice_id}, amount {amount}")
            return {"success": True, "transaction_id": transaction_id}
        except Exception as e:
            logger.error(f"Payment processing error: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def _process_with_gateway(amount: float, method: str) -> str:
        """Process payment with payment gateway (Stripe, etc.)"""
        # Mock implementation
        return f"TXN-{int(amount*100)}-{method}"

    @staticmethod
    async def refund_payment(
        invoice_id: int,
        amount: float,
        reason: str,
        db: Session
    ) -> dict:
        """Refund a payment"""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return {"success": False, "error": "Invoice not found"}

        try:
            # Process refund
            refund_id = f"REF-{invoice.transaction_id}"
            invoice.status = InvoiceStatus.draft  # Mark as refunded
            db.commit()
            
            logger.info(f"Refund processed: {refund_id}, amount {amount}")
            return {"success": True, "refund_id": refund_id}
        except Exception as e:
            logger.error(f"Refund processing error: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def verify_payment(transaction_id: str) -> dict:
        """Verify payment status with gateway"""
        # Mock implementation
        return {"transaction_id": transaction_id, "status": "completed"}

    @staticmethod
    async def get_payment_methods() -> list:
        """Get available payment methods"""
        return [
            {"id": "credit_card", "name": "Credit Card"},
            {"id": "debit_card", "name": "Debit Card"},
            {"id": "bank_transfer", "name": "Bank Transfer"},
            {"id": "paypal", "name": "PayPal"}
        ]
