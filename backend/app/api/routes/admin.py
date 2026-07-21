from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.base import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.models import User, Shipment, Dispute
from app.api.deps import get_current_user
from app.api.deps import get_current_admin


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"]
)


@router.get("/users")
async def list_users(
    current_user: User = Depends(get_current_admin),
    role: str = Query(None),
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """List all users with regional and compliance details (admin only)"""
    
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.is_active == (status == "active") if status in ["active", "inactive"] else True)
    
    users = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "phone": u.phone,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            # Enhanced fields for Georgensen logistics
            "primary_region": getattr(u, 'primary_region', 'north_america'),
            "compliance_status": getattr(u, 'compliance_status', 'pending'),
            "kyc_status": getattr(u, 'kyc_status', 'pending'),
            "background_check_status": getattr(u, 'background_check_status', 'pending'),
            "document_expiry": getattr(u, 'document_expiry', None),
            "last_verified": getattr(u, 'last_verified', None),
            "timezone": getattr(u, 'timezone', 'UTC'),
            "is_email_verified": u.is_email_verified if hasattr(u, 'is_email_verified') else False
        }
        for u in users
    ]


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed user information"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user statistics
    if user.role == "customer":
        shipments = db.query(Shipment).filter(Shipment.customer_id == user_id).count()
        stats = {"total_shipments": shipments}
    elif user.role == "partner":
        completed = db.query(Shipment).filter(
            Shipment.assigned_handler_id == user_id,
            Shipment.status == "delivered"
        ).count()
        pending = db.query(Shipment).filter(
            Shipment.assigned_handler_id == user_id,
            Shipment.status.in_(["confirmed", "picked_up", "in_transit"])
        ).count()
        stats = {
            "completed_shipments": completed,
            "pending_shipments": pending,
            "total_earned": 0.0,
            "rating": user.profile_data.get("rating", 0) if user.profile_data else 0
        }
    else:
        stats = {}
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "status": user.status,
        "profile_data": user.profile_data,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "statistics": stats
    }


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: UUID,
    status_data: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update user status (active/disabled)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_status = status_data.get("status")
    if new_status not in ["active", "disabled", "suspended"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status"
        )
    
    user.is_active = (new_status == "active")
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"User status updated to {new_status}",
        "user_id": user_id,
        "status": new_status
    }


@router.get("/shipments")
async def list_all_shipments(
    current_user: User = Depends(get_current_admin),
    status: str = Query(None),
    region: str = Query(None),
    customs_status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """List all shipments with global logistics context - regional, customs, and hub tracking"""
    
    query = db.query(Shipment)
    
    if status:
        query = query.filter(Shipment.status == status)
    
    if region:
        query = query.filter(getattr(Shipment, 'region', None) == region)
    
    if customs_status:
        query = query.filter(getattr(Shipment, 'customs_status', None) == customs_status)
    
    shipments = query.offset(skip).limit(limit).all()
    
    shipments_data = []
    for shipment in shipments:
        # Get customer info
        customer = db.query(User).filter(User.id == shipment.customer_id).first() if shipment.customer_id else None
        
        # Get handler/partner info
        handler = db.query(User).filter(User.id == shipment.assigned_handler_id).first() if shipment.assigned_handler_id else None
        
        shipments_data.append({
            "id": str(shipment.id),
            "tracking_number": shipment.tracking_number or f"TRK{shipment.id}",
            "customer": customer.full_name if customer else "Unknown",
            "region": getattr(shipment, 'region', 'north_america'),
            "dest_region": getattr(shipment, 'dest_region', 'europe'),
            "status": shipment.status,
            "amount_usd": float(getattr(shipment, 'total_price', 0) or 0),
            "customs_status": getattr(shipment, 'customs_status', 'pending'),
            "hub": getattr(shipment, 'hub', 'Toronto Hub'),
            "route_type": getattr(shipment, 'route_type', 'Domestic'),
            "hs_code": getattr(shipment, 'hs_code', 'HS621711'),
            "declared_value": float(getattr(shipment, 'declared_value', 0) or 0),
            "current_handler": handler.full_name if handler else None,
            "origin_timezone": getattr(shipment, 'origin_timezone', 'EST'),
            "dest_timezone": getattr(shipment, 'dest_timezone', 'CET'),
            "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
            "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None
        })
    
    return shipments_data


@router.get("/shipments/statistics")
async def get_shipment_statistics(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get shipment statistics"""
    
    total_shipments = db.query(Shipment).count()
    delivered = db.query(Shipment).filter(Shipment.status == "delivered").count()
    pending = db.query(Shipment).filter(Shipment.status == "pending").count()
    in_transit = db.query(Shipment).filter(Shipment.status == "in_transit").count()
    cancelled = db.query(Shipment).filter(Shipment.status == "cancelled").count()
    
    return {
        "total_shipments": total_shipments,
        "delivered": delivered,
        "pending": pending,
        "in_transit": in_transit,
        "cancelled": cancelled,
        "delivery_rate": round((delivered / total_shipments * 100), 1) if total_shipments > 0 else 0
    }


@router.get("/disputes")
async def list_disputes(
    current_user: User = Depends(get_current_admin),
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """List all disputes"""
    
    query = db.query(Dispute)
    
    if status:
        query = query.filter(Dispute.status == status)
    
    disputes = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": d.id,
            "tracking_number": d.tracking_number,
            "dispute_type": d.dispute_type,
            "status": d.status,
            "filed_by": d.filed_by_user.full_name if d.filed_by_user else "Unknown",
            "created_at": d.created_at
        }
        for d in disputes
    ]


@router.patch("/disputes/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: UUID,
    resolution_data: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Resolve a dispute"""
    
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    resolution = resolution_data.get("resolution")
    refund_amount = resolution_data.get("refund_amount", 0)
    
    dispute.status = "resolved"
    dispute.resolution = resolution
    dispute.refund_amount = refund_amount
    
    db.commit()
    db.refresh(dispute)
    
    return {
        "message": "Dispute resolved",
        "dispute_id": dispute_id,
        "resolution": resolution,
        "refund_amount": refund_amount
    }


@router.get("/partners")
async def list_partners(
    current_user: User = Depends(get_current_admin),
    region: str = Query(None),
    tier: str = Query(None),
    compliance_status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """List all partners with regional and compliance details (admin only)"""
    
    query = db.query(User).filter(User.role == "partner")
    
    if region:
        query = query.filter(getattr(User, 'primary_region', None) == region)
    
    partners = query.offset(skip).limit(limit).all()
    
    partners_data = []
    for p in partners:
        # Calculate tier based on completed shipments and rating
        completed_shipments = db.query(Shipment).filter(
            Shipment.assigned_handler_id == p.id,
            Shipment.status == "delivered"
        ).count()
        rating = getattr(p, 'rating', 4.0) or 4.0
        
        # Tier calculation: elite (>500 orders, >4.8), gold (>100 orders, >4.5), standard
        if completed_shipments >= 500 and rating >= 4.8:
            partner_tier = "elite"
        elif completed_shipments >= 100 and rating >= 4.5:
            partner_tier = "gold"
        else:
            partner_tier = "standard"
        
        # Calculate pending earnings
        pending_earnings = db.query(Shipment).filter(
            Shipment.assigned_handler_id == p.id,
            Shipment.status.in_(["confirmed", "picked_up", "in_transit"])
        ).count()
        
        # Calculate total earnings
        delivered_orders = db.query(Shipment).filter(
            Shipment.assigned_handler_id == p.id,
            Shipment.status == "delivered"
        ).all()
        total_earnings = sum(o.total_price * 0.8 for o in delivered_orders) if delivered_orders else 0
        
        partners_data.append({
            "id": str(p.id),
            "name": p.full_name or "Unknown",
            "email": p.email,
            "phone": p.phone,
            "primary_region": getattr(p, 'primary_region', 'north_america'),
            "completed_shipments": completed_shipments,
            "rating": float(rating),
            "tier": partner_tier,
            "compliance_status": getattr(p, 'compliance_status', 'pending'),
            "documents_status": getattr(p, 'documents_status', 'pending'),
            "kyc_status": getattr(p, 'kyc_status', 'pending'),
            "regional_tax_id": getattr(p, 'regional_tax_id', None),
            "service_zones": getattr(p, 'service_zones', ['Local']),
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "total_earnings": round(total_earnings, 2),
            "pending_payouts": 0.0,
            "last_payout": None,
            "avg_order_value": round(total_earnings / completed_shipments, 2) if completed_shipments > 0 else 0
        })
    
    return {"partners": partners_data}


@router.get("/partners/earnings")
async def get_partner_earnings(
    current_user: User = Depends(get_current_admin),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """Get partner earnings summary (stub - future implementation)"""
    
    # Future: integrate with payment/earnings system
    partners = db.query(User).filter(User.role == "partner").offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(p.id),
            "partner_name": p.full_name or "Unknown",
            "delivery_fee": 0.0,
            "commission_amount": 0.0,
            "net_earnings": 0.0,
            "status": "pending",
            "created_at": p.created_at
        }
        for p in partners
    ]


@router.patch("/partners/{partner_id}/payout")
async def process_payout(
    partner_id: UUID,
    payout_data: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Process partner payout (stub - future implementation)"""
    
    partner = db.query(User).filter(User.id == partner_id).first()
    if not partner or partner.role != "partner":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner not found"
        )
    
    amount = payout_data.get("amount")
    if not amount or amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid amount"
        )
    
    # Future: integrate with payment system
    return {
        "message": "Payout processed",
        "partner_id": str(partner_id),
        "amount": amount,
        "status": "completed"
    }


@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics with regional breakdown and logistics KPIs"""
    
    try:
        from datetime import datetime, timedelta
        
        # User stats
        total_users = db.query(User).count()
        customers = db.query(User).filter(User.role.in_(["customer"])).count()
        partners = db.query(User).filter(User.role.in_(["partner"])).count()
        admins = db.query(User).filter(User.role.in_(["admin", "system_admin"])).count()
        
        # Order stats
        total_orders = db.query(Shipment).count()
        delivered = db.query(Shipment).filter(Shipment.status == "delivered").count()
        in_transit = db.query(Shipment).filter(Shipment.status == "in_transit").count()
        customs_hold = 0  # Would filter by customs status if available
        due_soon = 0  # Would calculate shipments near SLA deadline
        
        # Revenue (simplified)
        all_shipments = db.query(Shipment).all()
        total_revenue = 0  # Would sum from shipment pricing if available
        
        # On-time delivery rate
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_shipments = db.query(Shipment).filter(Shipment.created_at >= thirty_days_ago).all()
        on_time_count = sum(1 for o in recent_shipments if o.status == "delivered")
        on_time_rate = (on_time_count / len(recent_shipments) * 100) if recent_shipments else 0
        
        # Revenue trend (last 7 days)
        revenue_trend = [total_revenue / 7 for _ in range(7)]
        
        return {
            "users": {
                "total": total_users,
                "customers": customers,
                "partners": partners,
                "admins": admins
            },
            "orders": {
                "total": total_orders,
                "delivered": delivered,
                "in_transit": in_transit,
                "customs_hold": customs_hold,
                "sla_breach_risk": due_soon,
                "on_time_rate": round(on_time_rate, 1),
                "delivery_rate": round((delivered / total_orders * 100), 1) if total_orders > 0 else 0
            },
            "revenue": {
                "total": round(total_revenue, 2),
                "average_order": round(total_revenue / total_orders, 2) if total_orders > 0 else 0
            },
            "revenue_trend": revenue_trend,
            "support_tickets": 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dashboard error: {str(e)}"
        )
