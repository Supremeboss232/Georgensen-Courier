"""Stripe payment service - handles real payment processing"""
from typing import Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

# Import Stripe - will need to be installed: pip install stripe
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    logger.warning("Stripe SDK not installed. Install with: pip install stripe")


from app.services.payrail_payment import payrail_payment_service

class StripePaymentService:
    """Handle Stripe payment processing with fallback integration for Payrail"""
    
    def __init__(self):
        """Initialize Stripe with API key"""
        self.api_key = settings.STRIPE_SECRET_KEY or ''
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY or ''
        self.use_payrail = True  # Flag to bypass Stripe and route to Payrail
        
        if self.use_payrail:
            self.enabled = True
        elif STRIPE_AVAILABLE and self.api_key:
            stripe.api_key = self.api_key
            self.enabled = True
        else:
            self.enabled = False
            if not STRIPE_AVAILABLE:
                logger.warning("Stripe SDK not available - payment processing disabled")
            elif not self.api_key:
                logger.warning("STRIPE_SECRET_KEY not set - payment processing disabled")
    
    async def create_payment_intent(
        self,
        amount_cents: int,
        customer_email: str,
        invoice_id: int,
        description: str = None
    ) -> Dict:
        """Create a payment intent (routes to Payrail if active)"""
        if not self.enabled:
            return {
                "success": False,
                "error": "Payment processing not configured",
                "client_secret": None
            }
            
        if self.use_payrail:
            res = await payrail_payment_service.create_payment_intent(
                amount_cents=amount_cents,
                customer_email=customer_email,
                invoice_id=invoice_id,
                description=description
            )
            if res.get("success"):
                return {
                    "success": True,
                    "client_secret": res["client_secret"],
                    "intent_id": res["reference"],
                    "amount": amount_cents,
                    "status": "requires_payment_method",
                    "authorization_url": res.get("authorization_url")
                }
            return {"success": False, "error": res.get("error", "Failed to initialize Payrail transaction")}
        
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                payment_method_types=["card"],
                receipt_email=customer_email,
                metadata={
                    "invoice_id": invoice_id,
                    "customer_email": customer_email
                },
                description=description or f"Invoice #{invoice_id}"
            )
            
            logger.info(f"Payment intent created: {intent.id} for invoice {invoice_id}")
            
            return {
                "success": True,
                "client_secret": intent.client_secret,
                "intent_id": intent.id,
                "amount": intent.amount,
                "status": intent.status
            }
        
        except stripe.error.CardError as e:
            logger.error(f"Card error: {e.user_message}")
            return {"success": False, "error": e.user_message}
        
        except stripe.error.RateLimitError:
            logger.error("Stripe rate limit exceeded")
            return {"success": False, "error": "Too many requests, try again later"}
        
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid request: {e.user_message}")
            return {"success": False, "error": f"Invalid request: {e.user_message}"}
        
        except stripe.error.AuthenticationError:
            logger.error("Stripe authentication failed")
            return {"success": False, "error": "Payment service authentication failed"}
        
        except stripe.error.APIConnectionError:
            logger.error("Stripe API connection failed")
            return {"success": False, "error": "Payment service unavailable"}
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {"success": False, "error": "Payment processing error"}
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"success": False, "error": "Unexpected error during payment"}
     
    async def retrieve_payment_intent(self, intent_id: str) -> Dict:
        """Retrieve payment intent status"""
        if not self.enabled:
            return {"success": False, "error": "Payment processing not configured"}
            
        if self.use_payrail:
            res = await payrail_payment_service.verify_payment(intent_id)
            if res.get("success"):
                status_mapping = {
                    "success": "succeeded",
                    "failed": "failed",
                    "pending": "processing"
                }
                status = res.get("status")
                stripe_status = status_mapping.get(status, "requires_payment_method")
                return {
                    "success": True,
                    "intent_id": intent_id,
                    "status": stripe_status,
                    "amount": 0,
                    "charges": [{"id": f"ch_{intent_id}"}]
                }
            return {"success": False, "error": res.get("error", "Failed to verify Payrail payment")}
        
        try:
            intent = stripe.PaymentIntent.retrieve(intent_id)
            
            return {
                "success": True,
                "intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount,
                "charges": intent.charges.data if intent.charges else []
            }
        
        except Exception as e:
            logger.error(f"Failed to retrieve intent: {str(e)}")
            return {"success": False, "error": str(e)}
     
    async def confirm_payment(self, intent_id: str) -> Dict:
        """Confirm payment was successful"""
        try:
            intent = await self.retrieve_payment_intent(intent_id)
            
            if not intent["success"]:
                return intent
            
            if intent["status"] == "succeeded":
                return {
                    "success": True,
                    "message": "Payment confirmed",
                    "intent_id": intent_id,
                    "status": "succeeded"
                }
            elif intent["status"] == "processing":
                return {
                    "success": False,
                    "message": "Payment still processing",
                    "intent_id": intent_id,
                    "status": "processing"
                }
            else:
                return {
                    "success": False,
                    "message": f"Payment {intent['status']}",
                    "intent_id": intent_id,
                    "status": intent["status"]
                }
        
        except Exception as e:
            logger.error(f"Payment confirmation error: {str(e)}")
            return {"success": False, "error": str(e)}
     
    async def refund_payment(
        self,
        intent_id: str,
        amount_cents: Optional[int] = None,
        reason: str = None
    ) -> Dict:
        """Refund a payment (full or partial)"""
        if not self.enabled:
            return {"success": False, "error": "Payment processing not configured"}
            
        if self.use_payrail:
            res = await payrail_payment_service.refund_payment(intent_id, amount_cents or 0)
            if res.get("success"):
                return {
                    "success": True,
                    "refund_id": f"ref_{intent_id}",
                    "charge_id": f"ch_{intent_id}",
                    "amount": amount_cents,
                    "status": "succeeded"
                }
            return {"success": False, "error": res.get("error", "Payrail refund request failed")}
        
        try:
            intent = await self.retrieve_payment_intent(intent_id)
            
            if not intent["success"]:
                return {"success": False, "error": "Payment intent not found"}
            
            # Get charge ID from intent
            if not intent.get("charges") or len(intent["charges"]) == 0:
                return {"success": False, "error": "No charge found for this payment"}
            
            charge_id = intent["charges"][0]["id"]
            
            # Process refund
            refund = stripe.Refund.create(
                charge=charge_id,
                amount=amount_cents,
                reason=reason or "requested_by_customer",
                metadata={"intent_id": intent_id}
            )
            
            logger.info(f"Refund processed: {refund.id} for charge {charge_id}")
            
            return {
                "success": True,
                "refund_id": refund.id,
                "charge_id": charge_id,
                "amount": refund.amount,
                "status": refund.status,
                "reason": reason
            }
        
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Refund request invalid: {e.user_message}")
            return {"success": False, "error": e.user_message}
        
        except Exception as e:
            logger.error(f"Refund processing error: {str(e)}")
            return {"success": False, "error": str(e)}
     
    async def create_customer(
        self,
        email: str,
        name: str,
        phone: Optional[str] = None
    ) -> Dict:
        """Create customer account mapping"""
        if not self.enabled:
            return {"success": False, "error": "Payment processing not configured"}
            
        if self.use_payrail:
            return {
                "success": True,
                "customer_id": f"payrail_cust_{email.replace('@', '_')}",
                "email": email
            }
        
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                phone=phone,
                metadata={"created_at": datetime.now().isoformat()}
            )
            
            logger.info(f"Stripe customer created: {customer.id}")
            
            return {
                "success": True,
                "customer_id": customer.id,
                "email": customer.email
            }
        
        except Exception as e:
            logger.error(f"Customer creation error: {str(e)}")
            return {"success": False, "error": str(e)}
     
    @staticmethod
    def get_publishable_key() -> str:
        """Get publishable key"""
        return os.getenv('STRIPE_PUBLISHABLE_KEY', '')


# Initialize service
payment_service = StripePaymentService()
