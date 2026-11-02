"""Payment API routes - Payrail & Stripe integration"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..db.base import get_db
from ..db.models import Invoice, User, Customer
from ..services.stripe_payment import StripePaymentService
from ..api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


def _user_owns_invoice(db: Session, user: User, invoice: Invoice) -> bool:
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    if role_val in ("admin", "system_admin") or user.is_superuser:
        return True
    if invoice.customer_id == user.id:
        return True
    cust = db.query(Customer).filter(Customer.user_id == user.id).first()
    return bool(cust and invoice.customer_id == cust.id)


@router.post("/create-intent", status_code=status.HTTP_201_CREATED)
async def create_payment_intent(
    invoice_id: int,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create payment intent for invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if not _user_owns_invoice(db, current_user, invoice):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to pay this invoice"
        )

    result = await StripePaymentService.create_payment_intent(
        invoice_id=invoice_id,
        amount=invoice.amount_due,
        currency="usd",
        customer_email=current_user.email,
        description=description or f"Invoice #{invoice.invoice_number}",
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Payment creation failed")
        )

    return result


@router.post("/confirm/{payment_intent_id}")
async def confirm_payment(
    payment_intent_id: str,
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm payment completion"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice or not _user_owns_invoice(db, current_user, invoice):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized"
        )

    result = await StripePaymentService.confirm_payment(
        payment_intent_id=payment_intent_id,
        invoice_id=invoice_id,
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Payment confirmation failed")
        )

    return result


@router.post("/refund/{invoice_id}")
async def refund_payment(
    invoice_id: int,
    amount: Optional[float] = None,
    reason: str = "requested_by_customer",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refund payment for invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if not _user_owns_invoice(db, current_user, invoice):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized"
        )

    result = await StripePaymentService.refund_payment(
        payment_intent_id=invoice.stripe_payment_intent,
        amount=amount,
        reason=reason,
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Refund failed")
        )

    return result


@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle payment provider webhook events"""
    signature = request.headers.get("payrail-signature") or request.headers.get("stripe-signature") or ""
    body = await request.body()

    result = await StripePaymentService.webhook_handler(
        event_body=body,
        sig_header=signature,
        db=db
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Webhook verification failed")
        )

    return {"received": True}
