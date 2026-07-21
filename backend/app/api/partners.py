from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from uuid import UUID
from app.db.base import get_db
from app.db.models import User, Shipment, Partner
from app.schemas.order import PartnerResponse, PartnerRegister
from app.core.security import SecurityUtils
from app.api.deps import get_current_partner, get_current_user
from app.services.notifications import NotificationService
from datetime import datetime, timedelta
from decimal import Decimal
import pytz
from enum import Enum


router = APIRouter(
    prefix="/api/v1/partners",
    tags=["Partners"]
)


@router.post("/register", response_model=PartnerResponse)
async def register_partner(
    partner_data: PartnerRegister,
    db: Session = Depends(get_db)
):
    """Register as delivery partner"""
    
    # Check if already exists
    existing = db.query(User).filter(User.email == partner_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create partner user
    partner = User(
        email=partner_data.email,
        hashed_password=SecurityUtils.get_password_hash(partner_data.password),
        full_name=partner_data.full_name,
        phone=partner_data.phone,
        role="partner",
        is_active=True,
        profile_data={
            "vehicle_type": partner_data.profile.vehicle_type if partner_data.profile else "motorbike",
            "services": [partner_data.profile.services[0] if partner_data.profile and partner_data.profile.services else "local"],
            "rating": 4.5,
            "completed_orders": 0
        }
    )
    
    db.add(partner)
    db.commit()
    db.refresh(partner)
    
    return partner


@router.get("/me", response_model=PartnerResponse)
async def get_profile(
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner profile"""
    
    return current_user


@router.patch("/me")
async def update_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update partner profile"""
    
    # Update basic info
    if "phone" in profile_data:
        current_user.phone = profile_data["phone"]
    if "full_name" in profile_data:
        current_user.full_name = profile_data["full_name"]
    
    # Update profile data
    if not current_user.profile_data:
        current_user.profile_data = {}
    
    if "vehicle_type" in profile_data:
        current_user.profile_data["vehicle_type"] = profile_data["vehicle_type"]
    if "services" in profile_data:
        current_user.profile_data["services"] = profile_data["services"]
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Profile updated successfully"}


@router.get("/available-shipments")
async def get_available_shipments(
    current_user: User = Depends(get_current_partner),
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get available shipments for partner assignment"""
    
    # Get shipments pending assignment
    shipments = db.query(Shipment).filter(
        Shipment.assigned_partner_id == None,
        Shipment.status == "order_received"
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": s.id,
            "tracking_number": s.tracking_number,
            "service_type": s.service_type,
            "pickup_address": s.pickup_address,
            "delivery_address": s.delivery_address,
            "quoted_price": s.quoted_price,
            "created_at": s.created_at
        }
        for s in shipments
    ]


@router.get("/assigned-orders")
async def get_assigned_orders(
    current_user: User = Depends(get_current_partner),
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get orders assigned to partner"""
    
    query = db.query(Order).filter(Order.assigned_partner_id == current_user.id)
    
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": order.id,
            "tracking_number": order.tracking_number,
            "customer_name": order.customer.full_name if order.customer else "Unknown",
            "status": order.status,
            "pickup_address": order.pickup_address,
            "delivery_address": order.delivery_address,
            "total_price": order.total_price,
            "created_at": order.created_at,
            "assigned_at": order.assigned_at
        }
        for order in orders
    ]


@router.get("/earnings")
async def get_earnings(
    current_user: User = Depends(get_current_partner),
    period: str = Query("monthly"),
    db: Session = Depends(get_db)
):
    """Get partner earnings summary"""
    
    earnings = db.query(PartnerEarning).filter(
        PartnerEarning.partner_id == current_user.id
    ).all()
    
    total_earnings = sum(e.net_earnings for e in earnings if e.status == PaymentStatusEnum.COMPLETED)
    pending_earnings = sum(e.net_earnings for e in earnings if e.status == PaymentStatusEnum.PENDING)
    completed_orders = len([e for e in earnings if e.status == PaymentStatusEnum.COMPLETED])
    
    return {
        "partner_id": current_user.id,
        "total_earnings": round(total_earnings, 2),
        "pending_earnings": round(pending_earnings, 2),
        "completed_orders": completed_orders,
        "average_per_order": round(total_earnings / completed_orders, 2) if completed_orders > 0 else 0,
        "period": period,
        "earnings_list": [
            {
                "order_id": e.order_id,
                "delivery_fee": e.delivery_fee,
                "commission_amount": e.commission_amount,
                "net_earnings": e.net_earnings,
                "status": e.status,
                "created_at": e.created_at
            }
            for e in earnings
        ]
    }


@router.post("/accept-order/{order_id}")
async def accept_order(
    order_id: UUID,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Partner accepts order assignment"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Already assigned to someone else
    if order.assigned_partner_id and order.assigned_partner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already assigned to another partner"
        )
    
    # Assign to current partner
    order.assigned_partner_id = current_user.id
    order.status = "confirmed"
    
    db.commit()
    db.refresh(order)
    
    # Send notification
    customer = order.customer
    if customer:
        NotificationService.send_order_assigned_email(
            customer.email,
            customer.full_name,
            current_user.full_name,
            current_user.phone,
            order.tracking_number
        )
    
    return {
        "message": "Order accepted",
        "order_id": order_id,
        "tracking_number": order.tracking_number
    }


@router.post("/earnings/request-payout")
async def request_payout(
    payout_data: dict,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Request payout for earnings"""
    
    amount = payout_data.get("amount")
    if not amount or amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payout amount"
        )
    
    # Get completed earnings
    earnings = db.query(PartnerEarning).filter(
        PartnerEarning.partner_id == current_user.id,
        PartnerEarning.status == PaymentStatusEnum.COMPLETED
    ).all()
    
    available = sum(e.net_earnings for e in earnings)
    if amount > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient earnings for payout"
        )
    
    # Log payout request
    NotificationService.log_notification(
        "PAYOUT_REQUEST",
        current_user.email,
        {"amount": amount, "available": available}
    )
    
    return {
        "message": "Payout request submitted",
        "amount": amount,
        "status": "pending",
        "estimated_days": 1
    }


# ==================== GLOBAL DASHBOARD ENDPOINTS ====================

@router.get("/profile")
async def get_global_profile(
    region: str = Query("NA", description="Partner's operating region: NA, EU, APAC, LATAM, MEA"),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get partner profile with regional context and multi-currency earnings"""
    
    # Define region-specific currency mappings
    REGION_CURRENCIES = {
        "NA": ["CAD", "USD"],
        "EU": ["EUR", "GBP"],
        "APAC": ["AUD", "SGD", "JPY"],
        "LATAM": ["MXN", "BRL", "ARS"],
        "MEA": ["AED", "SAR", "ZAR"]
    }
    
    # Get today's completed deliveries
    today = datetime.utcnow().date()
    completed_today = db.query(Shipment).filter(
        Shipment.assigned_partner_id == current_user.id,
        Shipment.status == "delivered",
        Shipment.delivered_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    # Get active deliveries (in transit or picked up)
    active_deliveries = db.query(Shipment).filter(
        Shipment.assigned_partner_id == current_user.id,
        Shipment.status.in_(["picked_up", "in_transit"])
    ).count()
    
    # Get partner rating (from profile data)
    profile_data = current_user.profile_data or {}
    rating = profile_data.get("rating", 4.8)
    review_count = profile_data.get("review_count", 0)
    
    # Get earnings by currency for this region
    currencies = REGION_CURRENCIES.get(region, ["CAD", "USD"])
    earnings_by_currency = {}
    
    for currency in currencies:
        # Query today's earnings in this currency
        today_start = datetime.combine(today, datetime.min.time())
        earnings = db.query(Shipment).filter(
            Shipment.assigned_partner_id == current_user.id,
            Shipment.status == "delivered",
            Shipment.delivered_at >= today_start,
            Shipment.currency == currency
        ).all()
        
        total = sum(Decimal(str(s.partner_payout)) for s in earnings if s.partner_payout)
        earnings_by_currency[currency] = float(total)
    
    return {
        "id": str(current_user.id),
        "name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "region": region,
        "active_deliveries": active_deliveries,
        "completed_today": completed_today,
        "rating": {
            "score": rating,
            "review_count": review_count
        },
        "earnings_by_currency": earnings_by_currency,
        "vehicle_type": profile_data.get("vehicle_type", "motorbike"),
        "services": profile_data.get("services", ["local"]),
        "compliance_verified": profile_data.get("compliance_verified", False),
        "customs_certified": profile_data.get("customs_certified", False)
    }


@router.get("/available-jobs")
async def get_available_jobs(
    region: str = Query("NA", description="Filter jobs by region: NA, EU, APAC, LATAM, MEA"),
    limit: int = Query(50),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get available jobs filtered by region with regional compliance info and multi-currency payouts"""
    
    # Region-to-country mapping with regional currencies
    REGION_CONFIG = {
        "NA": {
            "countries": ["CA", "US"],
            "currencies": ["CAD", "USD"],
            "timezone": "America/Toronto"
        },
        "EU": {
            "countries": ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH", "SE", "NO", "DK", "FI", "PL", "CZ", "IE"],
            "currencies": ["EUR", "GBP"],
            "timezone": "Europe/London"
        },
        "APAC": {
            "countries": ["AU", "SG", "JP", "HK", "NZ", "IN", "TH", "MY", "ID", "PH"],
            "currencies": ["AUD", "SGD", "JPY"],
            "timezone": "Asia/Singapore"
        },
        "LATAM": {
            "countries": ["MX", "BR", "AR", "CL", "CO", "PE", "VE", "EC"],
            "currencies": ["MXN", "BRL", "ARS"],
            "timezone": "America/Sao_Paulo"
        },
        "MEA": {
            "countries": ["AE", "SA", "KW", "QA", "BH", "ZA", "EG", "MA", "NG", "KE"],
            "currencies": ["AED", "SAR", "ZAR"],
            "timezone": "Asia/Dubai"
        }
    }
    
    config = REGION_CONFIG.get(region, REGION_CONFIG["NA"])
    countries = config["countries"]
    
    # Query available jobs in the region (unassigned and still pending)
    available_jobs = db.query(Shipment).filter(
        Shipment.assigned_partner_id == None,
        Shipment.status.in_(["order_received", "confirmed"]),
        Shipment.destination_country.in_(countries)
    ).limit(limit).all()
    
    jobs = []
    for shipment in available_jobs:
        # Determine shipment type (critical for SLA and logistics)
        is_international = shipment.origin_country != shipment.destination_country
        
        # Regional compliance flags
        requires_customs = is_international and shipment.package_weight > 50
        requires_vat = (
            shipment.destination_country in ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH"] 
            and shipment.total_value > 150
        )
        
        # Currency selection (use destination region's primary currency)
        primary_currency = config["currencies"][0]
        if shipment.destination_country == "US" and region == "NA":
            primary_currency = "USD"
        elif shipment.destination_country == "GB" and region == "EU":
            primary_currency = "GBP"
        
        # Recalculate payout in regional currency
        payout = float(shipment.partner_payout or 0)
        
        # Distance estimation
        distance_km = shipment.estimated_distance_km or 50
        
        # ETA calculation based on service type
        pickup_time = shipment.created_at or datetime.utcnow()
        if shipment.service_type == "express":
            delivery_days = 1
        elif shipment.service_type == "standard":
            delivery_days = 2
        else:  # economy
            delivery_days = 3
        eta = pickup_time + timedelta(days=delivery_days)
        
        job = {
            "id": str(shipment.id),
            "tracking_number": shipment.tracking_number,
            "pickup_location": f"{shipment.pickup_city}, {shipment.origin_country}",
            "delivery_location": f"{shipment.delivery_city}, {shipment.destination_country}",
            "pickup_city": shipment.pickup_city,
            "delivery_city": shipment.delivery_city,
            "distance_km": distance_km,
            "payout": payout,
            "currency": primary_currency,
            "service_type": shipment.service_type,
            "destination_region": region,
            "origin_country": shipment.origin_country,
            "destination_country": shipment.destination_country,
            "is_international": is_international,
            "requires_customs": requires_customs,
            "requires_vat": requires_vat,
            "package_weight": shipment.package_weight,
            "total_value": float(shipment.total_value or 0),
            "package_description": shipment.package_description or "Standard Package",
            "eta": eta.isoformat(),
            "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
            "status": shipment.status
        }
        jobs.append(job)
    
    return jobs


@router.get("/available-jobs-filtered")
async def get_filtered_jobs(
    region: str = Query("NA"),
    service_type: str = Query(None, description="Filter by service type: economy, standard, express"),
    min_payout: float = Query(0),
    is_international: bool = Query(None),
    limit: int = Query(50),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get jobs with advanced filtering (service type, payout range, international status)"""
    
    REGION_CONFIG = {
        "NA": {"countries": ["CA", "US"], "currencies": ["CAD", "USD"]},
        "EU": {"countries": ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH", "SE", "NO", "DK", "FI", "PL", "CZ", "IE"], "currencies": ["EUR", "GBP"]},
        "APAC": {"countries": ["AU", "SG", "JP", "HK", "NZ", "IN", "TH", "MY", "ID", "PH"], "currencies": ["AUD", "SGD", "JPY"]},
        "LATAM": {"countries": ["MX", "BR", "AR", "CL", "CO", "PE", "VE", "EC"], "currencies": ["MXN", "BRL", "ARS"]},
        "MEA": {"countries": ["AE", "SA", "KW", "QA", "BH", "ZA", "EG", "MA", "NG", "KE"], "currencies": ["AED", "SAR", "ZAR"]}
    }
    
    config = REGION_CONFIG.get(region, REGION_CONFIG["NA"])
    countries = config["countries"]
    
    # Build query
    query = db.query(Shipment).filter(
        Shipment.assigned_partner_id == None,
        Shipment.status.in_(["order_received", "confirmed"]),
        Shipment.destination_country.in_(countries),
        Shipment.partner_payout >= min_payout
    )
    
    # Apply service type filter
    if service_type:
        query = query.filter(Shipment.service_type == service_type)
    
    # Apply international status filter
    if is_international is not None:
        if is_international:
            query = query.filter(Shipment.origin_country != Shipment.destination_country)
        else:
            query = query.filter(Shipment.origin_country == Shipment.destination_country)
    
    jobs_list = query.limit(limit).all()
    
    return [{
        "id": str(j.id),
        "tracking_number": j.tracking_number,
        "pickup_location": f"{j.pickup_city}, {j.origin_country}",
        "delivery_location": f"{j.delivery_city}, {j.destination_country}",
        "distance_km": j.estimated_distance_km or 50,
        "payout": float(j.partner_payout or 0),
        "currency": config["currencies"][0],
        "service_type": j.service_type,
        "is_international": j.origin_country != j.destination_country,
        "requires_customs": (j.origin_country != j.destination_country) and j.package_weight > 50,
        "package_weight": j.package_weight
    } for j in jobs_list]


@router.post("/accept-job/{job_id}")
async def accept_job(
    job_id: str,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Partner accepts a job"""
    
    try:
        shipment = db.query(Shipment).filter(Shipment.id == job_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if shipment.assigned_partner_id:
            raise HTTPException(status_code=400, detail="Job already assigned")
        
        shipment.assigned_partner_id = current_user.id
        shipment.status = "confirmed"
        
        db.commit()
        db.refresh(shipment)
        
        return {
            "message": "Job accepted successfully",
            "job_id": job_id,
            "tracking_number": shipment.tracking_number
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings-summary")
async def get_earnings_summary(
    region: str = Query("NA"),
    period: str = Query("today", description="today, week, month, year"),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get earnings summary by currency for the specified period"""
    
    # Calculate date range based on period
    now = datetime.utcnow()
    if period == "today":
        start_date = datetime.combine(now.date(), datetime.min.time())
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:
        start_date = datetime.combine(now.date(), datetime.min.time())
    
    # Get earnings for the period
    shipments = db.query(Shipment).filter(
        Shipment.assigned_partner_id == current_user.id,
        Shipment.status == "delivered",
        Shipment.delivered_at >= start_date
    ).all()
    
    # Group by currency
    earnings_by_currency = {}
    for shipment in shipments:
        currency = shipment.currency or "CAD"
        payout = float(shipment.partner_payout or 0)
        
        if currency not in earnings_by_currency:
            earnings_by_currency[currency] = {
                "total": 0,
                "count": 0,
                "average": 0
            }
        
        earnings_by_currency[currency]["total"] += payout
        earnings_by_currency[currency]["count"] += 1
    
    # Calculate averages
    for currency in earnings_by_currency:
        count = earnings_by_currency[currency]["count"]
        if count > 0:
            earnings_by_currency[currency]["average"] = earnings_by_currency[currency]["total"] / count
    
    return {
        "period": period,
        "region": region,
        "earnings_by_currency": earnings_by_currency,
        "total_deliveries": len(shipments)
    }


@router.get("/earnings-transactions")
async def get_earnings_transactions(
    region: str = Query("NA"),
    period: str = Query("month", description="today, week, month, year"),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Get detailed transaction-level earnings with tax breakdown per transaction"""
    
    # Regional tax configuration
    TAX_CONFIG = {
        "NA": {"rate": 0.07, "type": "GST", "range": "7-13%"},
        "EU": {"rate": 0.19, "type": "VAT", "range": "15-27%"},
        "APAC": {"rate": 0.10, "type": "GST", "range": "0-10%"},
        "LATAM": {"rate": 0.17, "type": "VAT", "range": "15-19%"},
        "MEA": {"rate": 0.05, "type": "VAT", "range": "0-15%"}
    }
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "today":
        start_date = datetime.combine(now.date(), datetime.min.time())
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:
        start_date = datetime.combine(now.date(), datetime.min.time())
    
    # Get all shipments for this period
    shipments = db.query(Shipment).filter(
        Shipment.assigned_partner_id == current_user.id,
        Shipment.status == "delivered",
        Shipment.delivered_at >= start_date
    ).all()
    
    # Build transaction details with tax breakdown
    tax_info = TAX_CONFIG.get(region, TAX_CONFIG["NA"])
    transactions = []
    total_tax = 0
    
    for shipment in shipments:
        payout_amount = float(shipment.partner_payout or 0)
        # Calculate tax based on regional rate
        tax_amount = round(payout_amount * tax_info["rate"], 2)
        total_tax += tax_amount
        
        transaction = {
            "id": str(shipment.id),
            "order_id": shipment.tracking_number,
            "date": shipment.delivered_at.isoformat() if shipment.delivered_at else shipment.created_at.isoformat(),
            "amount": payout_amount,
            "currency": shipment.currency or "CAD",
            "tax_amount": tax_amount,
            "tax_type": tax_info["type"],
            "payout_amount": payout_amount - tax_amount,
            "origin": f"{shipment.pickup_city}, {shipment.origin_country}",
            "destination": f"{shipment.delivery_city}, {shipment.destination_country}",
            "service_type": shipment.service_type,
            "status": "completed"
        }
        transactions.append(transaction)
    
    # Calculate totals
    total_gross = sum(t["amount"] for t in transactions)
    total_payout = sum(t["payout_amount"] for t in transactions)
    
    return {
        "transactions": transactions,
        "tax_summary": {
            "total_gross": total_gross,
            "total_tax_withheld": total_tax,
            "total_payout": total_payout,
            "tax_rate_applied": tax_info["rate"] * 100,
            "tax_jurisdiction": region,
            "tax_type": tax_info["type"]
        },
        "period": period,
        "region": region,
        "transaction_count": len(transactions)
    }


@router.post("/update-payout-method")
async def update_payout_method(
    payout_data: dict,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update partner's preferred payout method for a region"""
    
    region = payout_data.get("region")
    method = payout_data.get("method")
    
    if not region or not method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Region and method are required"
        )
    
    # Valid methods per region
    VALID_METHODS = {
        "NA": ["Interac Transfer", "Direct Deposit", "Check"],
        "EU": ["SEPA Transfer", "Bank Transfer", "Check"],
        "APAC": ["PayNow (Singapore)", "Bank Transfer", "Wise"],
        "LATAM": ["Bank Transfer", "Check", "Wire Transfer"],
        "MEA": ["Bank Transfer", "Wire Transfer", "Check"]
    }
    
    valid_for_region = VALID_METHODS.get(region, [])
    if method not in valid_for_region:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid method for region {region}"
        )
    
    # Update profile data
    if not current_user.profile_data:
        current_user.profile_data = {}
    
    if "payout_methods" not in current_user.profile_data:
        current_user.profile_data["payout_methods"] = {}
    
    current_user.profile_data["payout_methods"][region] = method
    current_user.profile_data["preferred_payout_method"] = method
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Payout method updated successfully",
        "region": region,
        "method": method
    }


# ==================== GLOBAL SETTINGS ENDPOINTS ====================

@router.post("/update-profile")
async def update_profile_global(
    profile_data: dict,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update partner profile with global region context"""
    
    current_user.full_name = profile_data.get("full_name", current_user.full_name)
    current_user.email = profile_data.get("email", current_user.email)
    current_user.phone = profile_data.get("phone", current_user.phone)
    
    if not current_user.profile_data:
        current_user.profile_data = {}
    
    current_user.profile_data.update({
        "emergency_contact": profile_data.get("emergency_contact"),
        "address": profile_data.get("address"),
        "city": profile_data.get("city"),
        "state": profile_data.get("state"),
        "country": profile_data.get("country"),
        "postal_code": profile_data.get("postal_code"),
        "primary_region": profile_data.get("primary_region", "NA")
    })
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Profile updated successfully",
        "user_id": str(current_user.id),
        "primary_region": current_user.profile_data.get("primary_region")
    }


@router.post("/update-vehicle")
async def update_vehicle(
    vehicle_data: dict,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update vehicle information"""
    
    if not current_user.profile_data:
        current_user.profile_data = {}
    
    current_user.profile_data["vehicle"] = {
        "type": vehicle_data.get("vehicle_type"),
        "registration_number": vehicle_data.get("registration_number"),
        "make_model": vehicle_data.get("make_model"),
        "license_plate": vehicle_data.get("license_plate"),
        "cargo_capacity": vehicle_data.get("cargo_capacity"),
        "color": vehicle_data.get("color")
    }
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Vehicle information updated successfully"}


@router.post("/add-banking-account")
async def add_banking_account(
    banking_data: dict,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Add a new banking account for multi-currency payouts"""
    
    if not current_user.profile_data:
        current_user.profile_data = {}
    
    if "banking_accounts" not in current_user.profile_data:
        current_user.profile_data["banking_accounts"] = []
    
    account = {
        "currency": banking_data.get("currency"),
        "bank_name": banking_data.get("bank_name"),
        "account_number": banking_data.get("account_number"),
        "account_name": banking_data.get("account_name"),
        "swift_code": banking_data.get("swift_code"),
        "iban": banking_data.get("iban"),
        "is_primary": banking_data.get("is_primary", False),
        "region": banking_data.get("region"),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # If marked as primary, unset other primary accounts
    if account["is_primary"]:
        for existing in current_user.profile_data["banking_accounts"]:
            if existing.get("region") == account["region"]:
                existing["is_primary"] = False
    
    current_user.profile_data["banking_accounts"].append(account)
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Banking account added successfully",
        "currency": account["currency"],
        "region": account["region"]
    }


@router.post("/update-compliance")
async def update_compliance(
    compliance_data: dict,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update compliance and tax residency settings"""
    
    if not current_user.profile_data:
        current_user.profile_data = {}
    
    current_user.profile_data["compliance"] = {
        "tax_residency": compliance_data.get("tax_residency"),
        "tax_id": compliance_data.get("tax_id"),
        "customs_certified": compliance_data.get("customs_certified", False),
        "international_ready": compliance_data.get("international_ready", False),
        "fast_card_certified": compliance_data.get("fast_card", False),
        "vat_registered": compliance_data.get("vat_registered", False),
        "region": compliance_data.get("region"),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "message": "Compliance information updated successfully",
        "compliance_status": current_user.profile_data["compliance"]
    }


@router.post("/update-preferences")
async def update_preferences(
    pref_data: dict,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update delivery preferences based on region"""
    
    if not current_user.profile_data:
        current_user.profile_data = {}
    
    current_user.profile_data["preferences"] = {
        "accepted_services": pref_data.get("accepted_services", []),
        "max_jobs_per_day": pref_data.get("max_jobs_per_day", 10),
        "available_nights": pref_data.get("available_nights", False),
        "available_weekends": pref_data.get("available_weekends", True),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Delivery preferences updated successfully"}


@router.post("/update-global-settings")
async def update_global_settings(
    settings_data: dict,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update global localization and notification settings"""
    
    if not current_user.profile_data:
        current_user.profile_data = {}
    
    current_user.profile_data["global_settings"] = {
        "preferred_language": settings_data.get("preferred_language", "en"),
        "distance_unit": settings_data.get("distance_unit", "km"),
        "timezone": settings_data.get("timezone", "UTC"),
        "display_currency": settings_data.get("display_currency"),
        "notifications": {
            "email": settings_data.get("email_notifications", True),
            "sms": settings_data.get("sms_notifications", True),
            "push": settings_data.get("push_notifications", True)
        },
        "updated_at": datetime.utcnow().isoformat()
    }
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Global settings updated successfully"}
