from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.base import get_db
from app.db.models import User, Shipment, Partner
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
    """List all users (admin only)"""
    
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
            "role": u.role,
            "status": "active" if u.is_active else "inactive",
            "phone": u.phone,
            "created_at": u.created_at,
            "updated_at": u.updated_at
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
        shipments = db.query(Shipment).filter(Shipment.customer_id == user.id).count()
        stats = {"total_shipments": shipments}
    elif user.role == "partner":
        completed = db.query(Shipment).filter(
            Shipment.assigned_partner_id == user.id,
            Shipment.status == "delivered"
        ).count()
        pending = db.query(Shipment).filter(
            Shipment.assigned_partner_id == user.id,
            Shipment.status.in_(["confirmed", "picked_up", "in_transit"])
        ).count()
        partner_record = db.query(Partner).filter(Partner.user_id == user.id).first()
        total_earned = partner_record.total_earnings if partner_record else 0
        stats = {
            "completed_shipments": completed,
            "pending_shipments": pending,
            "total_earned": round(total_earned, 2),
            "rating": partner_record.rating if partner_record else 0
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
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """List all shipments in the system"""
    
    query = db.query(Shipment)
    
    if status:
        query = query.filter(Shipment.status == status)
    
    shipments = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": s.id,
            "tracking_number": s.tracking_number,
            "customer_id": s.customer_id,
            "status": s.status,
            "quoted_price": s.quoted_price,
            "assigned_partner_id": s.assigned_partner_id,
            "created_at": s.created_at,
            "updated_at": s.updated_at
        }
        for s in shipments
    ]


@router.get("/shipments/statistics")
async def get_shipment_statistics(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get shipment statistics"""
    
    total_shipments = db.query(Shipment).count()
    delivered = db.query(Shipment).filter(Shipment.status == "delivered").count()
    pending = db.query(Shipment).filter(Shipment.status == "order_received").count()
    in_transit = db.query(Shipment).filter(Shipment.status == "in_transit").count()
    cancelled = db.query(Shipment).filter(Shipment.status == "cancelled").count()
    
    all_shipments = db.query(Shipment).all()
    total_revenue = sum(s.quoted_price for s in all_shipments)
    
    return {
        "total_shipments": total_shipments,
        "delivered": delivered,
        "pending": pending,
        "in_transit": in_transit,
        "cancelled": cancelled,
        "total_revenue": round(total_revenue, 2),
        "average_shipment_value": round(total_revenue / total_shipments, 2) if total_shipments > 0 else 0,
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
    dispute_id: int,
    resolution_data: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Resolve a dispute with optional refund
    
    Admin endpoint to mark dispute as resolved and process refunds
    """
    
    from app.db.models import Dispute, Invoice
    from app.services.stripe_payment import payment_service
    from app.services.notifications import NotificationService
    
    try:
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise HTTPException(
                status_code=404,
                detail="Dispute not found"
            )
        
        resolution = resolution_data.get("resolution", "Resolved by admin")
        refund_amount = resolution_data.get("refund_amount", 0)
        refund_reason = resolution_data.get("refund_reason", "customer_request")
        
        # Find associated invoice
        invoice = db.query(Invoice).filter(
            Invoice.shipment_id == dispute.shipment_id
        ).first()
        
        # Process refund if amount specified
        if refund_amount > 0 and invoice and invoice.transaction_id:
            refund_result = await payment_service.refund_payment(
                intent_id=invoice.transaction_id,
                amount_cents=int(refund_amount * 100),
                reason=refund_reason
            )
            
            if not refund_result["success"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Refund failed: {refund_result.get('error')}"
                )
        
        # Update dispute
        dispute.status = "resolved"
        dispute.resolution = resolution
        dispute.refund_amount = refund_amount
        dispute.resolved_at = datetime.now()
        
        db.commit()
        db.refresh(dispute)
        
        # Send notification to customer
        try:
            customer = db.query(User).filter(User.id == dispute.reported_by_id).first()
            if customer:
                await NotificationService.send_alert_email(
                    recipient_email=customer.email,
                    alert_type="dispute_resolved",
                    details=f"Your dispute #{dispute.dispute_number} has been resolved. Refund: ${refund_amount:.2f}"
                )
        except:
            pass
        
        return {
            "success": True,
            "message": "Dispute resolved",
            "dispute_id": dispute_id,
            "resolution": resolution,
            "refund_amount": refund_amount,
            "resolved_at": dispute.resolved_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve dispute: {str(e)}"
        )


@router.get("/partners/earnings")
async def get_partner_earnings(
    current_user: User = Depends(get_current_admin),
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """Get partner earnings summary"""
    
    query = db.query(PartnerEarning)
    
    if status:
        query = query.filter(PartnerEarning.status == status)
    
    earnings = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "partner_name": e.partner.full_name if e.partner else "Unknown",
            "delivery_fee": e.delivery_fee,
            "commission_amount": e.commission_amount,
            "net_earnings": e.net_earnings,
            "status": e.status,
            "created_at": e.created_at
        }
        for e in earnings
    ]


@router.patch("/partners/{partner_id}/payout")
async def process_payout(
    partner_id: UUID,
    payout_data: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Process partner payout"""
    
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
    
    # Get pending earnings
    pending_earnings = db.query(PartnerEarning).filter(
        PartnerEarning.partner_id == partner_id,
        PartnerEarning.status == PaymentStatusEnum.PENDING
    ).all()
    
    total_pending = sum(e.net_earnings for e in pending_earnings)
    if amount > total_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payout amount exceeds pending earnings"
        )
    
    # Update earnings status (simplified - in production use transaction)
    paid_amount = 0
    for earning in pending_earnings:
        if paid_amount + earning.net_earnings <= amount:
            earning.status = PaymentStatusEnum.COMPLETED
            paid_amount += earning.net_earnings
    
    db.commit()
    
    return {
        "message": "Payout processed",
        "partner_id": partner_id,
        "amount": amount,
        "status": "completed"
    }


@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    
    # User stats
    total_users = db.query(User).count()
    customers = db.query(User).filter(User.role == "customer").count()
    partners = db.query(User).filter(User.role == "partner").count()
    admins = db.query(User).filter(User.role == "admin").count()
    
    # Order stats
    total_orders = db.query(Order).count()
    delivered = db.query(Order).filter(Order.status == "delivered").count()
    
    # Revenue
    all_orders = db.query(Order).all()
    total_revenue = sum(o.total_price for o in all_orders)
    
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
            "delivery_rate": round((delivered / total_orders * 100), 1) if total_orders > 0 else 0
        },
        "revenue": {
            "total": round(total_revenue, 2),
            "average_order": round(total_revenue / total_orders, 2) if total_orders > 0 else 0
        }
    }
