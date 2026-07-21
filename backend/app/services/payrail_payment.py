import urllib.request
import urllib.parse
import json
import logging
import os
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models.invoice import Invoice, InvoiceStatus

logger = logging.getLogger(__name__)

class PayrailPaymentService:
    """Generic/Custom API Client for Payrail payment gateway integration
    Uses standard library urllib for zero-dependency execution safety on Render.
    """
    
    def __init__(self):
        # Resolve API key from multiple possible environment configurations
        self.api_key = (
            os.getenv('PAYRAIL_SECRET_KEY') or
            os.getenv('STRIPE_SECRET_KEY') or
            os.getenv('PAYRAIL_API_KEY') or
            (getattr(settings, 'STRIPE_SECRET_KEY', None)) or
            ''
        )
        self.base_url = "https://api.payrail.co/v1"
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("Payrail API key not configured. Payment processing disabled.")

    def _send_request(self, method: str, path: str, payload: Optional[Dict] = None) -> Dict:
        """Helper to send HTTP requests to Payrail API"""
        if not self.enabled:
            return {"success": False, "error": "Payrail integration is disabled (missing API key)"}
            
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                return {
                    "success": True,
                    "status_code": response.status,
                    "data": json.loads(res_body) if res_body else {}
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            logger.error(f"Payrail API Error ({e.code}): {err_body}")
            try:
                err_json = json.loads(err_body)
                error_msg = err_json.get("message", "API Request Failed")
            except Exception:
                error_msg = err_body or str(e)
            return {"success": False, "error": error_msg, "status_code": e.code}
        except Exception as e:
            logger.error(f"Payrail Request Exception: {str(e)}")
            return {"success": False, "error": str(e)}

    async def create_payment_intent(
        self,
        amount_cents: int,
        customer_email: str,
        invoice_id: int,
        description: Optional[str] = None
    ) -> Dict:
        """Initialize transaction/payment intent on Payrail"""
        payload = {
            "amount": amount_cents,  # amount in base subunits (cents or kobo depending on currency)
            "email": customer_email,
            "reference": f"INV-{invoice_id}-{amount_cents}",
            "metadata": {
                "invoice_id": invoice_id,
                "description": description or f"Payment for invoice #{invoice_id}"
            }
        }
        
        # Call Payrail transaction initialize endpoint
        # Default REST path: POST /transactions/initialize or /charges
        result = self._send_request("POST", "/transactions/initialize", payload)
        
        if result.get("success"):
            data = result.get("data", {})
            return {
                "success": True,
                "client_secret": data.get("client_secret") or data.get("access_code"),
                "reference": data.get("reference") or payload["reference"],
                "authorization_url": data.get("authorization_url")
            }
        
        return {
            "success": False,
            "error": result.get("error", "Failed to initialize payment"),
            "client_secret": None
        }

    async def verify_payment(self, reference: str) -> Dict:
        """Verify transaction status on Payrail"""
        result = self._send_request("GET", f"/transactions/verify/{reference}")
        
        if result.get("success"):
            data = result.get("data", {})
            status = data.get("status") or data.get("data", {}).get("status")
            return {
                "success": True,
                "status": status,  # "success", "failed", "pending"
                "transaction_id": data.get("id") or reference
            }
        
        return {"success": False, "error": result.get("error", "Verification failed")}

    async def refund_payment(self, reference: str, amount_cents: int) -> Dict:
        """Initiate refund request on Payrail"""
        payload = {
            "transaction_reference": reference,
            "amount": amount_cents
        }
        result = self._send_request("POST", "/refunds", payload)
        return result

payrail_payment_service = PayrailPaymentService()
