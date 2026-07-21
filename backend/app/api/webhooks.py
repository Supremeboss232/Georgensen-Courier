"""
Webhook handlers for payment and third-party integrations
"""
import json
import hmac
import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models.invoice import Invoice
from app.db.models.tracking import Tracking
from app.core.config import settings
from app.services.payments import PaymentService

router = APIRouter(
    prefix="/api/v1",
    tags=["Webhooks"]
)


class WebhookLog:
    """Simple webhook tracking to prevent duplicate processing
    
    TODO: Create database table for persistent storage:
    - webhook_id (Stripe event ID)
    - event_type
    - processed_at
    - response_status
    """
    
    _processed_ids = set()  # In-memory cache (replace with DB in production)
    
    @classmethod
    def is_duplicate(cls, webhook_id: str) -> bool:
        """Check if webhook was already processed"""
        return webhook_id in cls._processed_ids
    
    @classmethod
    def mark_processed(cls, webhook_id: str):
        """Mark webhook as processed"""
        cls._processed_ids.add(webhook_id)


@router.post("/webhooks/stripe")
async def handle_stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events for payment reconciliation
    
    Processes:
    - payment_intent.succeeded: Mark invoice as paid
    - payment_intent.payment_failed: Mark invoice as failed
    - charge.refunded: Process refund
    - charge.dispute.created: Flag for manual review
    
    Webhook signature verification required for security
    """
    
    # Get webhook signature from headers
    stripe_signature = request.headers.get("stripe-signature")
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    # Read raw body for signature verification
    body = await request.body()
    
    # Verify webhook signature
    if not _verify_stripe_signature(body, stripe_signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature"
        )
    
    # Parse event
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
        # Check for duplicates (idempotency) using database
    event_id = event.get("id")
    event_type = event.get("type")
    
    from app.db.models.webhook import WebhookEvent
    existing_event = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
    if existing_event:
        return {"received": True, "note": "Duplicate event ignored"}
    
    # Process event based on type
    data = event.get("data", {})
    
    try:
        if event_type == "payment_intent.succeeded":
            _handle_payment_succeeded(db, data)
        elif event_type == "payment_intent.payment_failed":
            _handle_payment_failed(db, data)
        elif event_type == "charge.refunded":
            _handle_refund(db, data)
        elif event_type == "charge.dispute.created":
            _handle_dispute_created(db, data)
        
        # Mark as processed in DB after successful handling
        db_event = WebhookEvent(
            event_id=event_id,
            provider="stripe",
            event_type=event_type,
            payload=event
        )
        db.add(db_event)
        db.commit()
        
        return {"received": True}
    
    except Exception as e:
        # Log error but return 200 (don't retry failed events)
        # In production, store failed events for manual review
        print(f"Error processing webhook {event_id}: {str(e)}")
        return {"received": True, "error": str(e)}


def _handle_payment_succeeded(db: Session, data: dict):
    """Handle successful payment
    
    Update invoice status to paid
    """
    
    object_data = data.get("object", {})
    payment_intent_id = object_data.get("id")
    
    # Find invoice by payment intent ID
    invoice = db.query(Invoice).filter(
        Invoice.stripe_payment_intent_id == payment_intent_id
    ).first()
    
    if not invoice:
        print(f"Invoice not found for payment intent {payment_intent_id}")
        return
    
    # Update invoice status
    previous_status = invoice.status
    invoice.status = "paid"
    invoice.paid_at = datetime.now(timezone.utc)
    invoice.stripe_charge_id = object_data.get("charges", {}).get("data", [{}])[0].get("id")
    
    db.commit()
    
    print(f"Invoice {invoice.id} marked as paid (was {previous_status})")


def _handle_payment_failed(db: Session, data: dict):
    """Handle failed payment
    
    Update invoice status to failed
    """
    
    object_data = data.get("object", {})
    payment_intent_id = object_data.get("id")
    
    # Find invoice
    invoice = db.query(Invoice).filter(
        Invoice.stripe_payment_intent_id == payment_intent_id
    ).first()
    
    if not invoice:
        return
    
    # Update invoice status
    invoice.status = "failed"
    invoice.failure_reason = object_data.get("last_payment_error", {}).get("message")
    
    db.commit()
    
    print(f"Invoice {invoice.id} marked as failed: {invoice.failure_reason}")


def _handle_refund(db: Session, data: dict):
    """Handle refund
    
    Update invoice status and create refund record
    """
    
    object_data = data.get("object", {})
    charge_id = object_data.get("id")
    refund_amount = object_data.get("amount_refunded")
    
    # Find invoice by charge ID
    invoice = db.query(Invoice).filter(
        Invoice.stripe_charge_id == charge_id
    ).first()
    
    if not invoice:
        return
    
    # Update invoice
    invoice.status = "refunded"
    invoice.refund_amount = refund_amount / 100  # Convert from cents
    invoice.refunded_at = datetime.now(timezone.utc)
    
    db.commit()
    
    print(f"Invoice {invoice.id} refunded: ${invoice.refund_amount}")


def _handle_dispute_created(db: Session, data: dict):
    """Handle chargeback/dispute
    
    Flag invoice for manual review, create support ticket
    """
    
    object_data = data.get("object", {})
    charge_id = object_data.get("charge")
    dispute_id = object_data.get("id")
    
    # Find invoice
    invoice = db.query(Invoice).filter(
        Invoice.stripe_charge_id == charge_id
    ).first()
    
    if not invoice:
        return
    
    # Update invoice
    invoice.status = "disputed"
    invoice.dispute_id = dispute_id
    
    # TODO: Create support ticket for manual review
    # Create automatic support ticket to alert support team
    
    db.commit()
    
    print(f"Invoice {invoice.id} marked as disputed: {dispute_id}")


def _verify_stripe_signature(body: bytes, signature: str) -> bool:
    """
    Verify Stripe webhook signature
    
    Ensures webhook came from Stripe and wasn't tampered with
    """
    
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        print("WARNING: STRIPE_WEBHOOK_SECRET not configured, skipping signature verification")
        return True  # If not configured, accept all webhooks (dev only!)
    
    # Stripe signature format: t=timestamp,v1=hash
    try:
        timestamp, signature_value = None, None
        for part in signature.split(','):
            if part.startswith('t='):
                timestamp = part[2:]
            elif part.startswith('v1='):
                signature_value = part[4:]
        
        if not timestamp or not signature_value:
            return False
        
        # Create signed content
        signed_content = f"{timestamp}.{body.decode('utf-8')}"
        
        # Create HMAC-SHA256
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            signed_content.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures (constant time to prevent timing attacks)
        return hmac.compare_digest(signature_value, expected_signature)
    
    except Exception as e:
        print(f"Signature verification error: {str(e)}")
        return False


@router.post("/webhooks/email-delivery")
async def handle_email_delivery_webhook(request: Request):
    """
    Handle email delivery webhooks from SendGrid/Mailgun
    
    Process:
    - delivery: Email delivered successfully
    - bounce: Email bounced
    - complaint: User marked as spam
    
    TODO: Implement email delivery tracking
    """
    
    body = await request.json()
    event_type = body.get("event")
    
    if event_type == "bounce":
        email = body.get("email")
        print(f"Email bounce: {email}")
    elif event_type == "complaint":
        email = body.get("email")
        print(f"Spam complaint: {email}")
    
    return {"received": True}


@router.post("/webhooks/sms-delivery")
async def handle_sms_delivery_webhook(request: Request):
    """
    Handle SMS delivery webhooks from Twilio
    
    Process:
    - delivered: SMS delivered
    - failed: SMS failed to deliver
    - read: Recipient read receipt
    """
    
    body = await request.json()
    message_sid = body.get("MessageSid")
    status = body.get("MessageStatus")
    
    print(f"SMS {message_sid}: {status}")
    
    return {"received": True}


# ==============================
# CARRIER WEBHOOK HANDLERS
# ==============================

@router.post("/webhooks/fedex")
async def handle_fedex_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle FedEx TrackWeb webhook for real-time shipment tracking updates
    
    **Webhook Events:**
    - Package picked up
    - Package in transit
    - Package out for delivery
    - Package delivered
    - Package exception (delay, damage, etc.)
    
    **Expected Payload:**
    ```json
    {
        "tracking_number": "794587284837",
        "status_code": "DL",
        "status_description": "Delivered",
        "timestamp": "2026-04-17T14:30:00Z",
        "signature": "fedex_signature_hash",
        "events": [
            {
                "status": "DL",
                "timestamp": "2026-04-17T14:30:00Z",
                "location": "Toronto, ON",
                "details": "Delivered"
            }
        ]
    }
    ```
    
    **Documentation:** FedEx Developer Portal - TrackWeb Services
    """
    
    try:
        body = await request.json()
        
        # Verify FedEx webhook signature
        signature = request.headers.get("X-FedEx-Signature")
        if not _verify_fedex_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid FedEx webhook signature"
            )
        
        # Extract tracking data
        tracking_number = body.get("tracking_number")
        carrier_tracking_id = body.get("carrier_id") or "FEDEX"
        status_code = body.get("status_code")
        status_description = body.get("status_description")
        timestamp = body.get("timestamp")
        
        if not tracking_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing tracking_number"
            )
        
        # Find or create tracking record
        tracking = db.query(Tracking).filter(
            Tracking.tracking_number == tracking_number
        ).first()
        
        if not tracking:
            # New tracking record from carrier notification
            print(f"New FedEx tracking notification: {tracking_number}")
            return {"received": True, "action": "new_shipment"}
        
        # Process tracking events
        events = body.get("events", [])
        for event in events:
            event_status = event.get("status", status_code)
            event_location = event.get("location", "")
            event_timestamp = event.get("timestamp", timestamp)
            event_details = event.get("details", event.get("status_description"))
            
            # Map FedEx status to internal status
            internal_status = _map_fedex_status(event_status)
            
            # Create tracking history entry
            history_entry = {
                "status": internal_status,
                "status_code": event_status,
                "location": event_location,
                "timestamp": event_timestamp,
                "notes": event_details,
                "carrier": "FEDEX",
                "carrier_tracking_id": carrier_tracking_id
            }
            
            # Add to tracking history
            if tracking.raw_history is None:
                tracking.raw_history = []
            
            tracking.raw_history.append(history_entry)
        
        # Update tracking status
        tracking.current_status = _map_fedex_status(status_code)
        tracking.updated_at = datetime.now(timezone.utc)
        
        # Check for delivery
        if status_code == "DL":
            tracking.delivered_at = datetime.now(timezone.utc)
        
        # Check for exceptions
        if status_code in ["EX", "DY", "LO"]:  # Exception, Delay, Lost
            tracking.has_exception = True
            tracking.exception_details = status_description
        
        db.commit()
        
        print(f"FedEx tracking updated: {tracking_number} - {status_description}")
        
        return {
            "received": True,
            "tracking_number": tracking_number,
            "status": internal_status,
            "message": "Tracking updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing FedEx webhook: {str(e)}")
        # Return 200 to prevent carrier retry loops
        return {"received": True, "error": str(e)}


@router.post("/webhooks/ups")
async def handle_ups_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle UPS OnTrack webhook for real-time shipment tracking updates
    
    **Webhook Events:**
    - Order processed
    - Package picked up
    - Package in transit
    - Out for delivery
    - Package delivered
    - Exception
    
    **Expected Payload:**
    ```json
    {
        "shipment": {
            "shipment_number": "1Z999AA10123456784",
            "status": "DELIVERED",
            "status_timestamp": "2026-04-17T14:30:00-04:00",
            "events": [
                {
                    "status": "DELIVERED",
                    "timestamp": "2026-04-17T14:30:00-04:00",
                    "location": {
                        "city": "Toronto",
                        "state": "ON",
                        "country": "CA"
                    }
                }
            ]
        }
    }
    ```
    
    **Documentation:** UPS Developer Portal - OnTrack API
    """
    
    try:
        body = await request.json()
        
        # Verify UPS webhook signature
        signature = request.headers.get("X-UPS-Signature")
        if not _verify_ups_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid UPS webhook signature"
            )
        
        # Extract shipment data
        shipment = body.get("shipment", {})
        tracking_number = shipment.get("shipment_number")
        carrier_tracking_id = shipment.get("carrier_id") or "UPS"
        status_code = shipment.get("status")
        timestamp = shipment.get("status_timestamp")
        
        if not tracking_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing shipment_number"
            )
        
        # Find tracking record
        tracking = db.query(Tracking).filter(
            Tracking.tracking_number == tracking_number
        ).first()
        
        if not tracking:
            print(f"New UPS tracking notification: {tracking_number}")
            return {"received": True, "action": "new_shipment"}
        
        # Process tracking events
        events = shipment.get("events", [])
        for event in events:
            event_status = event.get("status", status_code)
            event_location = event.get("location", {})
            event_timestamp = event.get("timestamp", timestamp)
            
            # Format location string
            city = event_location.get("city", "")
            state = event_location.get("state", "")
            country = event_location.get("country", "")
            location_str = f"{city}, {state} {country}".strip()
            
            # Map UPS status to internal status
            internal_status = _map_ups_status(event_status)
            
            # Create tracking history entry
            history_entry = {
                "status": internal_status,
                "status_code": event_status,
                "location": location_str,
                "timestamp": event_timestamp,
                "notes": event.get("status_description", ""),
                "carrier": "UPS",
                "carrier_tracking_id": carrier_tracking_id
            }
            
            # Add to tracking history
            if tracking.raw_history is None:
                tracking.raw_history = []
            
            tracking.raw_history.append(history_entry)
        
        # Update tracking status
        tracking.current_status = _map_ups_status(status_code)
        tracking.updated_at = datetime.now(timezone.utc)
        
        # Check for delivery
        if status_code == "DELIVERED":
            tracking.delivered_at = datetime.now(timezone.utc)
        
        # Check for exceptions
        if status_code == "EXCEPTION":
            tracking.has_exception = True
            tracking.exception_details = shipment.get("exception_description", "UPS exception")
        
        db.commit()
        
        print(f"UPS tracking updated: {tracking_number} - {status_code}")
        
        return {
            "received": True,
            "tracking_number": tracking_number,
            "status": internal_status,
            "message": "Tracking updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing UPS webhook: {str(e)}")
        return {"received": True, "error": str(e)}


# ==============================
# CARRIER SIGNATURE VERIFICATION
# ==============================

def _verify_fedex_signature(body: dict, signature: str) -> bool:
    """
    Verify FedEx webhook signature using HMAC-SHA256
    
    FedEx signs the request body with a shared secret key
    """
    
    fedex_webhook_key = settings.FEDEX_WEBHOOK_SECRET
    if not fedex_webhook_key:
        print("WARNING: FEDEX_WEBHOOK_SECRET not configured")
        return True  # Dev mode - accept all
    
    try:
        # Serialize body for signature verification
        body_string = json.dumps(body, separators=(',', ':'), sort_keys=True)
        
        # Create HMAC-SHA256
        expected_signature = hmac.new(
            fedex_webhook_key.encode('utf-8'),
            body_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(signature or "", expected_signature)
    
    except Exception as e:
        print(f"FedEx signature verification error: {str(e)}")
        return False


def _verify_ups_signature(body: dict, signature: str) -> bool:
    """
    Verify UPS webhook signature using HMAC-SHA256
    
    UPS signs the request body with OAuth credentials
    """
    
    ups_webhook_key = settings.UPS_WEBHOOK_SECRET
    if not ups_webhook_key:
        print("WARNING: UPS_WEBHOOK_SECRET not configured")
        return True  # Dev mode - accept all
    
    try:
        # Serialize body for signature verification
        body_string = json.dumps(body, separators=(',', ':'), sort_keys=True)
        
        # Create HMAC-SHA256
        expected_signature = hmac.new(
            ups_webhook_key.encode('utf-8'),
            body_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(signature or "", expected_signature)
    
    except Exception as e:
        print(f"UPS signature verification error: {str(e)}")
        return False


# ==============================
# STATUS MAPPING FUNCTIONS
# ==============================

def _map_fedex_status(fedex_status: str) -> str:
    """
    Map FedEx status codes to internal status strings
    
    FedEx Status Codes:
    - OC = On Fedex vehicle for delivery
    - DE = Delivered
    - AP = At fedex pending location
    - PU = Picked up
    - IT = In transit
    - OD = Out for delivery
    - DL = Delivered
    - EX = Exception
    - DY = Delay
    - LO = Lost
    """
    
    status_map = {
        "OC": "out_for_delivery",
        "DE": "delivered",
        "DL": "delivered",
        "AP": "pending",
        "PU": "picked_up",
        "IT": "in_transit",
        "OD": "out_for_delivery",
        "EX": "exception",
        "DY": "exception",
        "LO": "exception",
        "RTO": "returned_to_origin",
    }
    
    return status_map.get(fedex_status, "in_transit")


def _map_ups_status(ups_status: str) -> str:
    """
    Map UPS status codes to internal status strings
    
    UPS Status Codes:
    - PROCESSED = Order processed
    - PICKED_UP = Package picked up
    - IN_TRANSIT = In transit
    - OUT_FOR_DELIVERY = Out for delivery
    - DELIVERED = Delivered
    - RETURN_TO_SENDER = Return to sender
    - EXCEPTION = Exception/delay
    """
    
    status_map = {
        "PROCESSED": "pending",
        "PICKED_UP": "picked_up",
        "IN_TRANSIT": "in_transit",
        "OUT_FOR_DELIVERY": "out_for_delivery",
        "DELIVERED": "delivered",
        "RETURN_TO_SENDER": "returned_to_origin",
        "EXCEPTION": "exception",
        "CANCELLED": "cancelled",
    }
    
    return status_map.get(ups_status, "in_transit")
