"""
Partner payout and settlement service
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.partner import Partner
from app.db.models.invoice import Invoice
from app.db.models.shipment import Shipment
from app.core.config import settings
import stripe


class PayoutStatus(str, Enum):
    """Status of partner payout"""
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class PayoutMethod(str, Enum):
    """How to pay partner"""
    bank_transfer = "bank_transfer"  # ACH for US
    stripe_connect = "stripe_connect"  # Stripe Connect account
    paypal = "paypal"
    manual = "manual"  # Invoice/manual wiring


class PartnerPayout:
    """Partner earnings and settlement tracking
    
    DB Table structure (TODO):
    - id
    - partner_id (FK)
    - period_start (date)
    - period_end (date)
    - total_earnings (float)
    - status (PayoutStatus)
    - payout_method (PayoutMethod)
    - reference_id (transaction ID from payment gateway)
    - metadata (JSON)
    - created_at
    - completed_at
    """
    
    def __init__(self, db: Session):
        self.db = db
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    def calculate_partner_earnings(
        self,
        partner_id: int,
        period_start: datetime,
        period_end: datetime
    ) -> dict:
        """
        Calculate partner earnings for a period
        
        Earnings are based on:
        - Commission on completed shipments (shipment.commission_rate)
        - Bonus for on-time deliveries
        - Deductions for disputes/chargebacks
        
        Returns:
            {
                "partner_id": int,
                "period": "2024-01-01 to 2024-01-31",
                "total_shipments": int,
                "total_earnings": float,
                "commission_earnings": float,
                "bonus_earnings": float,
                "deductions": float,
                "breakdown": [
                    {
                        "shipment_id": int,
                        "amount": float,
                        "type": "commission|bonus|deduction"
                    }
                ]
            }
        """
        
        partner = self.db.query(Partner).get(partner_id)
        if not partner:
            raise ValueError(f"Partner {partner_id} not found")
        
        # Find completed shipments for this partner in the period
        shipments = self.db.query(Shipment).filter(
            and_(
                Shipment.partner_id == partner_id,
                Shipment.status == "delivered",
                Shipment.delivered_at >= period_start,
                Shipment.delivered_at <= period_end
            )
        ).all()
        
        breakdown = []
        commission_earnings = 0.0
        bonus_earnings = 0.0
        deductions = 0.0
        
        for shipment in shipments:
            # Commission earnings
            commission = (shipment.total_amount or 0) * (partner.commission_rate or 0.15)
            commission_earnings += commission
            breakdown.append({
                "shipment_id": shipment.id,
                "amount": commission,
                "type": "commission"
            })
            
            # On-time delivery bonus (if delivered before due date)
            if shipment.delivered_at and shipment.scheduled_delivery_date:
                if shipment.delivered_at.date() <= shipment.scheduled_delivery_date:
                    bonus = commission * 0.10  # 10% bonus on commission
                    bonus_earnings += bonus
                    breakdown.append({
                        "shipment_id": shipment.id,
                        "amount": bonus,
                        "type": "bonus"
                    })
            
            # TODO: Deductions for disputes
            # Check if invoice associated with shipment has disputes
            disputed_invoices = self.db.query(Invoice).filter(
                and_(
                    Invoice.shipment_id == shipment.id,
                    Invoice.status == "disputed"
                )
            ).count()
            
            if disputed_invoices > 0:
                deduction = commission * 0.50  # 50% deduction for disputes
                deductions += deduction
                breakdown.append({
                    "shipment_id": shipment.id,
                    "amount": -deduction,
                    "type": "deduction_dispute"
                })
        
        total_earnings = commission_earnings + bonus_earnings - deductions
        
        return {
            "partner_id": partner_id,
            "partner_name": partner.name,
            "period": f"{period_start.date()} to {period_end.date()}",
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_shipments": len(shipments),
            "commission_earnings": round(commission_earnings, 2),
            "bonus_earnings": round(bonus_earnings, 2),
            "deductions": round(deductions, 2),
            "total_earnings": round(total_earnings, 2),
            "breakdown": breakdown
        }
    
    def process_weekly_payouts(self) -> List[dict]:
        """
        Process payouts for all partners for the past week
        
        Called once per week (suggest: Sunday midnight UTC)
        """
        
        # Calculate: Last Sunday to Saturday
        today = datetime.now(timezone.utc).date()
        days_since_sunday = (today.weekday() + 1) % 7  # Monday=0, Sunday=6
        period_end = today - timedelta(days=days_since_sunday)
        period_start = period_end - timedelta(days=7)
        
        # Get all active partners
        partners = self.db.query(Partner).filter(Partner.is_active == True).all()
        
        payouts = []
        
        for partner in partners:
            try:
                # Calculate earnings
                earnings = self.calculate_partner_earnings(
                    partner.id,
                    datetime.combine(period_start, datetime.min.time()).replace(tzinfo=timezone.utc),
                    datetime.combine(period_end, datetime.max.time()).replace(tzinfo=timezone.utc)
                )
                
                if earnings["total_earnings"] <= 0:
                    # No earnings or negative (likely deductions)
                    continue
                
                # Process payout
                payout_result = self._process_payout(partner, earnings)
                payouts.append(payout_result)
            
            except Exception as e:
                print(f"Error processing payout for partner {partner.id}: {str(e)}")
                payouts.append({
                    "partner_id": partner.id,
                    "status": "failed",
                    "error": str(e)
                })
        
        return payouts
    
    def _process_payout(self, partner: Partner, earnings: dict) -> dict:
        """
        Execute actual payout using selected payment method
        
        Methods:
        - Stripe Connect: Send to partner's Stripe account
        - Bank Transfer: Generate ACH request (requires banking integration)
        - PayPal: Send to PayPal account
        - Manual: Create invoice for accounting team
        """
        
        amount_cents = int(earnings["total_earnings"] * 100)
        
        # Determine payout method
        payout_method = self._get_partner_payout_method(partner)
        
        try:
            if payout_method == PayoutMethod.stripe_connect:
                return self._payout_via_stripe_connect(partner, amount_cents, earnings)
            elif payout_method == PayoutMethod.bank_transfer:
                return self._payout_via_bank_transfer(partner, amount_cents, earnings)
            elif payout_method == PayoutMethod.paypal:
                return self._payout_via_paypal(partner, amount_cents, earnings)
            else:
                return self._payout_manual(partner, amount_cents, earnings)
        
        except Exception as e:
            return {
                "partner_id": partner.id,
                "status": "failed",
                "error": str(e),
                "method": payout_method.value
            }
    
    def _get_partner_payout_method(self, partner: Partner) -> PayoutMethod:
        """Get partner's preferred payout method (from partner record)"""
        # TODO: Add payout_method field to Partner model
        # For now, default to manual (safest during development)
        return PayoutMethod.manual
    
    def _payout_via_stripe_connect(self, partner: Partner, amount_cents: int, earnings: dict) -> dict:
        """
        Send payout via Stripe Connect
        
        Requires:
        - Partner has Stripe Connect account linked
        - account_id stored in partner.stripe_account_id
        """
        
        if not partner.stripe_account_id:
            raise ValueError(f"Partner {partner.id} has no Stripe Connect account")
        
        try:
            # Create transfer to partner's Stripe account
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency="usd",
                destination=partner.stripe_account_id,
                description=f"Payout for {earnings['period']}"
            )
            
            return {
                "partner_id": partner.id,
                "partner_name": partner.name,
                "status": "completed",
                "method": "stripe_connect",
                "amount": earnings["total_earnings"],
                "reference_id": transfer.id,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            raise ValueError(f"Stripe transfer failed: {str(e)}")
    
    def _payout_via_bank_transfer(self, partner: Partner, amount_cents: int, earnings: dict) -> dict:
        """
        Send payout via ACH bank transfer
        
        Requires:
        - Partner has ACH info on file (bank account, routing number)
        - Integration with banking API (Stripe Treasury, Plaid, etc.)
        """
        
        if not partner.bank_account_last4:
            raise ValueError(f"Partner {partner.id} has no bank account on file")
        
        # TODO: Implement actual ACH transfer via banking API
        # For now, return pending status
        
        return {
            "partner_id": partner.id,
            "partner_name": partner.name,
            "status": "processing",
            "method": "bank_transfer",
            "amount": earnings["total_earnings"],
            "reference_id": f"ACH-{partner.id}-{datetime.now(timezone.utc).timestamp()}",
            "note": f"Scheduled for next banking day"
        }
    
    def _payout_via_paypal(self, partner: Partner, amount_cents: int, earnings: dict) -> dict:
        """Send payout via PayPal API"""
        
        if not partner.paypal_email:
            raise ValueError(f"Partner {partner.id} has no PayPal email on file")
        
        # TODO: Implement PayPal payout API integration
        
        return {
            "partner_id": partner.id,
            "partner_name": partner.name,
            "status": "pending",
            "method": "paypal",
            "amount": earnings["total_earnings"],
            "reference_id": f"PAYPAL-{partner.id}-{datetime.now(timezone.utc).timestamp()}"
        }
    
    def _payout_manual(self, partner: Partner, amount_cents: int, earnings: dict) -> dict:
        """
        Create manual payout invoice for accounting team
        
        Safe fallback that doesn't automatically send money
        """
        
        return {
            "partner_id": partner.id,
            "partner_name": partner.name,
            "status": "pending",
            "method": "manual",
            "amount": earnings["total_earnings"],
            "note": "Manual payout - review and approve in accounting system",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    def get_partner_payout_history(
        self,
        partner_id: int,
        limit: int = 12
    ) -> List[dict]:
        """Get payout history for a partner (last N periods)"""
        
        # TODO: Query PartnerPayout table for history
        # For now return mock data
        
        return []
