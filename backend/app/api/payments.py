"""Payment API endpoints - handle invoice payment with Stripe"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.base import get_db
from app.db.models import User, Invoice
from app.api.deps import get_current_user, get_current_customer
from app.services.stripe_payment import payment_service
from app.services.notifications import NotificationService

router = APIRouter(
    prefix="/api/v1/payments",
    tags=["Payments"]
)


@router.post("/intents")
async def create_payment_intent(
    invoice_id: int,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe payment intent for an invoice
    
    Returns client_secret for frontend payment form
    """
    
    try:
        # Verify invoice exists and belongs to customer
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to pay this invoice")
        
        # Check invoice not already paid
        if invoice.status == "paid":
            raise HTTPException(status_code=400, detail="Invoice already paid")
        
        # Convert amount to cents for Stripe
        amount_cents = int(invoice.total_amount * 100)
        
        # Create payment intent
        result = await payment_service.create_payment_intent(
            amount_cents=amount_cents,
            customer_email=current_user.email,
            invoice_id=invoice_id,
            description=f"Invoice #{invoice_id} for shipment"
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to create payment intent")
            )
        
        return {
            "success": True,
            "invoice_id": invoice_id,
            "client_secret": result["client_secret"],
            "intent_id": result["intent_id"],
            "amount": result["amount"],
            "currency": "usd",
            "publishable_key": payment_service.get_publishable_key()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Payment setup failed: {str(e)}"
        )


@router.get("/intents/{intent_id}")
async def get_payment_intent(
    intent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check payment intent status
    
    Verify payment was successful
    """
    
    try:
        result = await payment_service.retrieve_payment_intent(intent_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail="Payment intent not found")
        
        return {
            "success": True,
            "intent_id": result["intent_id"],
            "status": result["status"],
            "amount": result["amount"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve payment status: {str(e)}"
        )


@router.post("/intents/{intent_id}/confirm")
async def confirm_payment(
    intent_id: str,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Confirm payment completion
    
    Called after Stripe confirms payment
    Updates invoice status to paid
    """
    
    try:
        # Confirm payment with Stripe
        result = await payment_service.confirm_payment(intent_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Payment not completed")
            )
        
        # Find invoice by intent metadata
        # In production, you'd store intent_id → invoice_id mapping
        # For now, we'll search by customer and pending status
        invoices = db.query(Invoice).filter(
            Invoice.customer_id == current_user.id,
            Invoice.status.in_(["pending", "unpaid"])
        ).all()
        
        if not invoices:
            raise HTTPException(status_code=404, detail="No invoice found for this payment")
        
        # Update invoice status
        for invoice in invoices:
            if invoice.status != "paid":
                invoice.status = "paid"
                invoice.payment_method = "stripe"
                invoice.transaction_id = intent_id
                db.commit()
                
                # Send payment confirmation email
                try:
                    await NotificationService.send_payment_confirmation_email(
                        recipient_email=current_user.email,
                        invoice_id=invoice.id,
                        amount=invoice.total_amount
                    )
                except Exception as e:
                    print(f"Failed to send confirmation email: {str(e)}")
                
                return {
                    "success": True,
                    "message": "Payment confirmed and processed",
                    "invoice_id": invoice.id,
                    "amount": invoice.total_amount,
                    "status": "paid"
                }
        
        raise HTTPException(status_code=400, detail="Could not update invoice")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Payment confirmation failed: {str(e)}"
        )


@router.post("/refunds/{intent_id}")
async def refund_payment(
    intent_id: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process refund for a payment
    
    Admin only - used for dispute resolution
    """
    
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        # Process refund
        result = await payment_service.refund_payment(
            intent_id=intent_id,
            reason=reason or "requested_by_customer"
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Refund failed")
            )
        
        return {
            "success": True,
            "message": "Refund processed",
            "refund_id": result["refund_id"],
            "amount": result["amount"],
            "reason": result["reason"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Refund processing failed: {str(e)}"
        )


@router.post("/{invoice_id}/mark-paid")
async def mark_invoice_paid(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark invoice as paid (manual, for admin/partner payments)
    
    Used for offline payments or wire transfers
    """
    
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice.status == "paid":
            raise HTTPException(status_code=400, detail="Invoice already paid")
        
        invoice.status = "paid"
        invoice.payment_method = "manual"
        db.commit()
        
        return {
            "success": True,
            "message": "Invoice marked as paid",
            "invoice_id": invoice_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update invoice: {str(e)}"
        )
