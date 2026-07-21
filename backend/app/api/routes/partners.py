from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.base import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.models import User, Shipment
from app.api.deps import get_current_user
from app.schemas.order import PartnerResponse, PartnerRegister
from app.core.security import SecurityUtils
from app.api.deps import get_current_partner, get_current_user
from app.services.notifications import NotificationService


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


@router.get("/available-orders")
async def get_available_orders(
    current_user: User = Depends(get_current_partner),
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get available orders for partner assignment"""
    
    # Get orders pending assignment
    orders = db.query(Order).filter(
        Order.assigned_partner_id == None,
        Order.status == "pending"
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": order.id,
            "tracking_number": order.tracking_number,
            "service_type": order.service_type,
            "pickup_address": order.pickup_address,
            "delivery_address": order.delivery_address,
            "total_price": order.total_price,
            "created_at": order.created_at
        }
        for order in orders
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
