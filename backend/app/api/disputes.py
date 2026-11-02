"""Dispute handling API routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import logging

from ..db.base import get_db
from ..db.models import Shipment, Dispute, User, Customer
from ..api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/disputes", tags=["Disputes"])


def _resolve_customer_id(db: Session, user: User) -> int:
    cust = db.query(Customer).filter(Customer.user_id == user.id).first()
    if not cust:
        cust = Customer(
            user_id=user.id,
            company_name=user.full_name or "Individual",
            account_type="individual",
            phone=user.phone
        )
        db.add(cust)
        db.commit()
        db.refresh(cust)
    return cust.id


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_dispute(
    order_id: int,
    reason: str,
    description: str,
    amount_claimed: float,
    evidence_urls: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a dispute for an order/shipment"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == order_id).first()
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        customer_id = _resolve_customer_id(db, current_user)
        role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if role_val not in ("admin", "system_admin") and not current_user.is_superuser:
            if shipment.customer_id not in (customer_id, current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unauthorized to dispute this order"
                )

        existing = db.query(Dispute).filter(
            Dispute.shipment_id == order_id,
            Dispute.status.in_(["open", "in_review"])
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active dispute already exists for this order"
            )

        dispute = Dispute(
            shipment_id=order_id,
            customer_id=customer_id,
            reason=reason,
            description=description,
            amount_claimed=amount_claimed,
            evidence_urls=evidence_urls,
            status="open"
        )
        db.add(dispute)
        db.commit()
        db.refresh(dispute)

        return {
            "id": dispute.id,
            "dispute_id": f"DISP-{dispute.id:05d}",
            "order_id": order_id,
            "shipment_id": order_id,
            "status": dispute.status,
            "amount_claimed": dispute.amount_claimed,
            "created_at": dispute.created_at.isoformat() if dispute.created_at else datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Dispute creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create dispute"
        )


@router.get("/{dispute_id}")
async def get_dispute(
    dispute_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dispute details with ownership check"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val not in ("admin", "system_admin") and not current_user.is_superuser:
        customer_id = _resolve_customer_id(db, current_user)
        if dispute.customer_id not in (customer_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    return {
        "id": dispute.id,
        "dispute_id": f"DISP-{dispute.id:05d}",
        "order_id": dispute.shipment_id,
        "shipment_id": dispute.shipment_id,
        "customer_id": dispute.customer_id,
        "reason": dispute.reason,
        "description": dispute.description,
        "status": dispute.status,
        "amount_claimed": dispute.amount_claimed,
        "approved_amount": dispute.approved_amount,
        "resolution_notes": dispute.resolution_notes,
        "evidence_urls": dispute.evidence_urls,
        "created_at": dispute.created_at.isoformat() if dispute.created_at else None,
        "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None
    }


@router.get("")
async def list_disputes(
    status_filter: Optional[str] = Query(None, alias="status"),
    customer_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List disputes (scoped to customer unless admin)"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    query = db.query(Dispute)

    if role_val in ("admin", "system_admin") or current_user.is_superuser:
        if customer_id:
            query = query.filter(Dispute.customer_id == customer_id)
    else:
        own_customer_id = _resolve_customer_id(db, current_user)
        query = query.filter(Dispute.customer_id.in_([own_customer_id, current_user.id]))

    if status_filter:
        query = query.filter(Dispute.status == status_filter)

    disputes = query.order_by(Dispute.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "dispute_id": f"DISP-{d.id:05d}",
            "order_id": d.shipment_id,
            "shipment_id": d.shipment_id,
            "reason": d.reason,
            "status": d.status,
            "amount_claimed": d.amount_claimed,
            "approved_amount": d.approved_amount,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in disputes
    ]


@router.put("/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: int,
    status_val: str = Query(..., alias="status"),
    approved_amount: Optional[float] = Query(None),
    resolution_notes: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve dispute (Admin only)"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val not in ("admin", "system_admin") and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can resolve disputes"
        )

    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )

    dispute.status = status_val
    dispute.approved_amount = approved_amount
    dispute.resolution_notes = resolution_notes
    dispute.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(dispute)

    return {
        "id": dispute.id,
        "dispute_id": f"DISP-{dispute.id:05d}",
        "status": dispute.status,
        "approved_amount": dispute.approved_amount,
        "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None
    }
