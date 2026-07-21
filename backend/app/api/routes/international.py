from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.models.order import Order
from app.db.models.tracking import Tracking
from app.api.deps import get_db, get_current_user
from app.db.models.user import User

router = APIRouter(prefix="/international", tags=["international"])


@router.get("/countries")
async def get_supported_countries():
    """Get list of supported countries for international shipping"""
    return {
        "countries": [
            {"code": "US", "name": "United States"},
            {"code": "UK", "name": "United Kingdom"},
            {"code": "CA", "name": "Canada"},
            {"code": "SG", "name": "Singapore"},
            {"code": "NZ", "name": "New Zealand"},
            {"code": "JP", "name": "Japan"},
            {"code": "AU", "name": "Australia"}
        ]
    }


@router.get("/rates/{country_code}")
async def get_international_rates(country_code: str):
    """Get shipping rates to a specific country"""
    rates = {
        "US": {"base_fee": 45.00, "per_kg": 5.50},
        "UK": {"base_fee": 40.00, "per_kg": 4.50},
        "CA": {"base_fee": 50.00, "per_kg": 6.00},
        "SG": {"base_fee": 30.00, "per_kg": 3.50},
        "NZ": {"base_fee": 25.00, "per_kg": 3.00},
        "JP": {"base_fee": 55.00, "per_kg": 7.00}
    }
    
    if country_code not in rates:
        raise HTTPException(status_code=404, detail="Country not found")
    
    return {"country_code": country_code, "rates": rates[country_code]}


@router.post("/calculate-customs/{order_id}")
async def calculate_customs(
    order_id: int,
    country_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Calculate customs duty and fees for international shipment"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Simplified customs calculation
    customs_rate = 0.10  # 10% duty
    customs_fee = order.total_amount * customs_rate
    handling_fee = 25.00  # Fixed handling fee
    
    return {
        "order_id": order_id,
        "declared_value": order.total_amount,
        "customs_duty": customs_fee,
        "handling_fee": handling_fee,
        "total_customs_fees": customs_fee + handling_fee
    }


@router.get("/tracking/{tracking_number}/customs")
async def get_customs_status(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """Get customs clearance status for international shipment"""
    tracking = db.query(Tracking).filter(
        Tracking.tracking_number == tracking_number
    ).first()
    
    if not tracking:
        raise HTTPException(status_code=404, detail="Tracking not found")
    
    return {
        "tracking_number": tracking_number,
        "customs_status": "cleared",
        "cleared_date": "2026-02-03",
        "reference_number": "CUST-12345"
    }


@router.post("/validate-address/{country_code}")
async def validate_international_address(
    country_code: str,
    address: str
):
    """Validate international delivery address"""
    # This would call an address validation service
    return {
        "address": address,
        "country_code": country_code,
        "is_valid": True,
        "formatted_address": address
    }
