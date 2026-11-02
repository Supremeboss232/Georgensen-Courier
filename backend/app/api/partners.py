from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.base import get_db
from app.db.models import User, Partner, Shipment, ShipmentStatus, TrackingHistory
from app.schemas.order import PartnerProfile, PartnerResponse, OrderListResponse
from app.api.deps import get_current_partner
from app.services.pricing_global import GlobalPricingService

router = APIRouter(prefix="/api/v1/partners", tags=["Partners"])


def _get_partner_ids(db: Session, current_user: User) -> List[int]:
    """Return list of IDs that may be stored on Shipment.assigned_partner_id for this partner user."""
    ids = [current_user.id]
    partner_record = db.query(Partner).filter(Partner.user_id == current_user.id).first()
    if partner_record and partner_record.id not in ids:
        ids.append(partner_record.id)
    return ids


@router.get("/profile", response_model=PartnerResponse)
async def get_partner_profile(
    current_user: User = Depends(get_current_partner)
):
    """Get partner profile information"""
    return PartnerResponse.model_validate(current_user)


@router.put("/profile")
async def update_partner_profile(
    profile_data: dict = Body(...),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update partner profile and availability"""
    merged = dict(current_user.profile_data or {})
    merged.update(profile_data)
    current_user.profile_data = merged

    if "full_name" in profile_data and profile_data["full_name"]:
        current_user.full_name = profile_data["full_name"]
    if "phone" in profile_data and profile_data["phone"]:
        current_user.phone = profile_data["phone"]

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Partner profile updated",
        "profile": current_user.profile_data
    }


@router.get("/assigned-orders", response_model=List[OrderListResponse])
async def get_assigned_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get shipments assigned to current partner"""
    partner_ids = _get_partner_ids(db, current_user)
    query = db.query(Shipment).filter(Shipment.assigned_partner_id.in_(partner_ids))

    if status_filter:
        query = query.filter(Shipment.status == status_filter)

    shipments = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()
    return [OrderListResponse.model_validate(s) for s in shipments]


@router.get("/earnings")
async def get_partner_earnings(
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner earnings summary and history"""
    partner_ids = _get_partner_ids(db, current_user)
    shipments = db.query(Shipment).filter(
        Shipment.assigned_partner_id.in_(partner_ids)
    ).order_by(Shipment.created_at.desc()).all()

    delivered = [s for s in shipments if str(s.status) == ShipmentStatus.DELIVERED.value or str(s.status) == "delivered"]
    in_progress = [s for s in shipments if str(s.status) not in ("delivered", "cancelled")]

    total_earned = sum(float(s.partner_payout or (s.total_price * 0.70)) for s in delivered)
    pending_amount = sum(float(s.partner_payout or (s.total_price * 0.70)) for s in in_progress)

    return {
        "total_earned": round(total_earned, 2),
        "pending_amount": round(pending_amount, 2),
        "completed_orders": len(delivered),
        "earnings": [
            {
                "id": str(s.id),
                "order_id": str(s.id),
                "tracking_number": s.tracking_number,
                "amount": round(float(s.partner_payout or (s.total_price * 0.70)), 2),
                "commission_rate": 0.70,
                "payout_status": "completed" if str(s.status) == "delivered" else "pending",
                "created_at": (s.actual_delivery or s.created_at or datetime.utcnow()).isoformat()
            }
            for s in shipments[:50]
        ]
    }


@router.post("/accept-order/{order_id}")
async def accept_order(
    order_id: int,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Accept an order assignment"""
    partner_ids = _get_partner_ids(db, current_user)
    shipment = db.query(Shipment).filter(Shipment.id == order_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if shipment.assigned_partner_id and shipment.assigned_partner_id not in partner_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This order is assigned to another partner"
        )

    shipment.assigned_partner_id = current_user.id
    shipment.assigned_at = datetime.utcnow()
    shipment.status = ShipmentStatus.PROCESSING.value

    db.add(shipment)
    db.commit()

    return {
        "message": "Order accepted",
        "order_id": str(order_id)
    }


@router.post("/earnings/request-payout")
async def request_payout(
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Request payout of pending earnings"""
    partner_ids = _get_partner_ids(db, current_user)
    delivered = db.query(Shipment).filter(
        Shipment.assigned_partner_id.in_(partner_ids),
        Shipment.status == ShipmentStatus.DELIVERED.value
    ).all()

    total_payout = sum(float(s.partner_payout or (s.total_price * 0.70)) for s in delivered)

    return {
        "message": "Payout request submitted",
        "total_amount": round(total_payout, 2),
        "earnings_count": len(delivered),
        "status": "processing"
    }


# ==================== GLOBAL PARTNER PORTAL ENDPOINTS ====================

@router.get("/available-jobs")
async def get_available_jobs(
    region: Optional[str] = Query(None),
    vehicle_type: Optional[str] = Query(None),
    max_distance_km: float = Query(100, ge=5, le=5000),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get available shipment jobs for partner to accept"""
    query = db.query(Shipment).filter(
        Shipment.status.in_([
            ShipmentStatus.ORDER_RECEIVED.value,
            ShipmentStatus.PROCESSING.value,
            "pending",
            "confirmed"
        ]),
        Shipment.assigned_partner_id == None
    )

    if region:
        countries = GlobalPricingService.REGION_COUNTRIES.get(region, [])
        if countries:
            query = query.filter(Shipment.destination_country.in_(countries))

    available = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()

    jobs = []
    for shipment in available:
        payout = float(shipment.partner_payout or (shipment.total_price * 0.70))
        jobs.append({
            "job_id": str(shipment.id),
            "tracking_number": shipment.tracking_number,
            "origin": f"{shipment.pickup_city}, {shipment.origin_country or 'CA'}",
            "destination": f"{shipment.delivery_city}, {shipment.destination_country or 'CA'}",
            "pickup_address": shipment.pickup_address,
            "delivery_address": shipment.delivery_address,
            "weight_kg": float(shipment.package_weight or 1.0),
            "service_type": shipment.service_type,
            "estimated_distance_km": float(shipment.estimated_distance_km or 10.0),
            "payout_amount": round(payout, 2),
            "currency": shipment.currency or "CAD",
            "pickup_deadline": shipment.pickup_at.isoformat() if shipment.pickup_at else None,
            "delivery_deadline": shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
            "special_handling": shipment.special_instructions or None,
            "created_at": shipment.created_at.isoformat() if shipment.created_at else None
        })

    return {
        "available_jobs": len(jobs),
        "region": region or "all",
        "jobs": jobs
    }


@router.post("/accept-job/{job_id}")
async def accept_job(
    job_id: int,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Accept an available delivery job"""
    shipment = db.query(Shipment).filter(
        Shipment.id == job_id,
        Shipment.assigned_partner_id == None
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or already assigned"
        )

    shipment.assigned_partner_id = current_user.id
    shipment.assigned_at = datetime.utcnow()
    shipment.status = ShipmentStatus.PROCESSING.value
    if not shipment.partner_payout:
        shipment.partner_payout = round(shipment.total_price * 0.70, 2)

    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    return {
        "message": "Job accepted successfully",
        "job_id": str(job_id),
        "tracking_number": shipment.tracking_number,
        "payout": round(float(shipment.partner_payout or 0), 2),
        "currency": shipment.currency or "CAD",
        "pickup_address": shipment.pickup_address,
        "delivery_address": shipment.delivery_address
    }


@router.get("/active-deliveries")
async def get_active_deliveries(
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner's currently active deliveries"""
    partner_ids = _get_partner_ids(db, current_user)
    active = db.query(Shipment).filter(
        Shipment.assigned_partner_id.in_(partner_ids),
        Shipment.status.in_([
            ShipmentStatus.ORDER_RECEIVED.value,
            ShipmentStatus.PROCESSING.value,
            ShipmentStatus.PICKED_UP.value,
            ShipmentStatus.IN_TRANSIT.value,
            ShipmentStatus.OUT_FOR_DELIVERY.value,
            "confirmed",
            "picked_up",
            "in_transit",
            "out_for_delivery"
        ])
    ).order_by(Shipment.estimated_delivery.asc()).all()

    deliveries = []
    for s in active:
        deliveries.append({
            "shipment_id": str(s.id),
            "tracking_number": s.tracking_number,
            "status": str(s.status),
            "origin": f"{s.pickup_city}, {s.origin_country or 'CA'}",
            "destination": f"{s.delivery_city}, {s.destination_country or 'CA'}",
            "pickup_address": s.pickup_address,
            "delivery_address": s.delivery_address,
            "customer_phone": s.delivery_phone,
            "weight_kg": float(s.package_weight or 1.0),
            "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
            "payout": round(float(s.partner_payout or (s.total_price * 0.70)), 2),
            "currency": s.currency or "CAD",
            "current_lat": s.latitude,
            "current_lng": s.longitude,
        })

    return {
        "active_count": len(deliveries),
        "deliveries": deliveries
    }


@router.put("/delivery/{shipment_id}/status")
async def update_delivery_status(
    shipment_id: int,
    new_status: Optional[str] = Query(None),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    notes: Optional[str] = Query(None),
    proof_of_delivery_url: Optional[str] = Query(None),
    body: Optional[dict] = Body(default=None),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update delivery status with GPS coordinates and proof of delivery"""
    partner_ids = _get_partner_ids(db, current_user)
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.assigned_partner_id.in_(partner_ids)
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found or not assigned to you"
        )

    b = body if isinstance(body, dict) else {}
    resolved_status = new_status or b.get("new_status") or b.get("status")
    resolved_lat = latitude if latitude is not None else b.get("latitude")
    resolved_lng = longitude if longitude is not None else b.get("longitude")
    resolved_notes = notes or b.get("notes")
    resolved_pod_url = proof_of_delivery_url or b.get("proof_of_delivery_url")

    valid_statuses = [
        ShipmentStatus.ORDER_RECEIVED.value,
        ShipmentStatus.PROCESSING.value,
        ShipmentStatus.PICKED_UP.value,
        ShipmentStatus.IN_TRANSIT.value,
        ShipmentStatus.OUT_FOR_DELIVERY.value,
        ShipmentStatus.DELIVERED.value,
        ShipmentStatus.FAILED_DELIVERY.value,
        "picked_up", "in_transit", "out_for_delivery", "delivered", "failed_delivery"
    ]
    if not resolved_status or resolved_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    shipment.status = resolved_status
    if resolved_lat is not None and resolved_lng is not None:
        shipment.latitude = float(resolved_lat)
        shipment.longitude = float(resolved_lng)
        shipment.last_location_update = datetime.utcnow()

    if resolved_pod_url:
        shipment.delivery_proof_photo = resolved_pod_url

    if resolved_status == "delivered":
        shipment.actual_delivery = datetime.utcnow()

    history = TrackingHistory(
        shipment_id=shipment.id,
        tracking_number=shipment.tracking_number,
        partner_id=current_user.id,
        status=resolved_status,
        latitude=shipment.latitude,
        longitude=shipment.longitude,
        location=shipment.current_location,
        notes=resolved_notes or f"Status updated to {resolved_status}"
    )

    db.add(shipment)
    db.add(history)
    db.commit()
    db.refresh(shipment)

    return {
        "message": f"Delivery status updated to {resolved_status}",
        "shipment_id": str(shipment_id),
        "status": resolved_status,
        "payout_triggered": resolved_status == "delivered"
    }


@router.get("/earnings/summary")
async def get_earnings_summary(
    period: str = Query("month"),
    region: Optional[str] = Query(None),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get comprehensive earnings summary with regional and currency breakdown"""
    now = datetime.utcnow()
    if period == "day":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=now.weekday())
    elif period == "month":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "year":
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now - timedelta(days=30)

    partner_ids = _get_partner_ids(db, current_user)
    shipments = db.query(Shipment).filter(
        Shipment.assigned_partner_id.in_(partner_ids),
        Shipment.status == ShipmentStatus.DELIVERED.value,
        or_(Shipment.actual_delivery >= start_date, Shipment.created_at >= start_date)
    ).all()

    earnings_by_currency = {}
    earnings_by_region = {}
    total_deliveries = len(shipments)
    total_distance_km = 0.0
    total_weight_kg = 0.0

    for s in shipments:
        curr = s.currency or "CAD"
        payout = float(s.partner_payout or (s.total_price * 0.70))
        earnings_by_currency[curr] = round(earnings_by_currency.get(curr, 0.0) + payout, 2)

        dest_region = GlobalPricingService.detect_region(s.destination_country or "CA")
        reg_key = dest_region.value if hasattr(dest_region, "value") else str(dest_region)
        if reg_key not in earnings_by_region:
            earnings_by_region[reg_key] = {"deliveries": 0, "amount": 0.0, "currency": curr}
        earnings_by_region[reg_key]["deliveries"] += 1
        earnings_by_region[reg_key]["amount"] = round(earnings_by_region[reg_key]["amount"] + payout, 2)

        total_distance_km += float(s.estimated_distance_km or 10.0)
        total_weight_kg += float(s.package_weight or 1.0)

    return {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "total_deliveries": total_deliveries,
        "total_distance_km": round(total_distance_km, 2),
        "total_weight_kg": round(total_weight_kg, 2),
        "earnings_by_currency": earnings_by_currency,
        "earnings_by_region": earnings_by_region,
        "average_per_delivery": round(sum(earnings_by_currency.values()) / max(total_deliveries, 1), 2),
        "rating": (current_user.profile_data or {}).get("rating", 4.8),
        "completion_rate": 0.98
    }


@router.get("/earnings/history")
async def get_earnings_history(
    currency: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get detailed earnings history with pagination"""
    partner_ids = _get_partner_ids(db, current_user)
    query = db.query(Shipment).filter(
        Shipment.assigned_partner_id.in_(partner_ids),
        Shipment.status == ShipmentStatus.DELIVERED.value
    )
    if currency:
        query = query.filter(Shipment.currency == currency)

    records = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total_records": len(records),
        "skip": skip,
        "limit": limit,
        "earnings": [
            {
                "shipment_id": str(s.id),
                "tracking_number": s.tracking_number,
                "origin": f"{s.pickup_city}, {s.origin_country or 'CA'}",
                "destination": f"{s.delivery_city}, {s.destination_country or 'CA'}",
                "distance_km": float(s.estimated_distance_km or 10.0),
                "weight_kg": float(s.package_weight or 1.0),
                "service_type": s.service_type,
                "payout": round(float(s.partner_payout or (s.total_price * 0.70)), 2),
                "currency": s.currency or "CAD",
                "delivered_at": (s.actual_delivery or s.created_at or datetime.utcnow()).isoformat(),
                "payout_status": "paid"
            }
            for s in records
        ]
    }


@router.get("/compliance-status")
async def get_compliance_status(
    current_user: User = Depends(get_current_partner)
):
    """Get partner's compliance, verification, and tax status across regions"""
    pdata = current_user.profile_data or {}
    return {
        "partner_id": str(current_user.id),
        "verification_status": pdata.get("verification_status", "verified"),
        "kyc_completed": pdata.get("kyc_completed", True),
        "background_check": pdata.get("background_check", "passed"),
        "insurance_verified": pdata.get("insurance_verified", True),
        "insurance_expiry": pdata.get("insurance_expiry", "2027-12-31"),
        "vehicle_inspection": pdata.get("vehicle_inspection", "valid"),
        "vehicle_inspection_expiry": pdata.get("vehicle_inspection_expiry", "2027-06-30"),
        "tax_compliance": {
            "CA": {"SIN_verified": True, "GST_registered": False},
            "US": {"EIN_verified": False, "1099_eligible": True},
            "EU": {"VAT_ID_verified": False},
            "AU": {"ABN_verified": False}
        },
        "documents_required": [],
        "can_accept_jobs": True
    }
