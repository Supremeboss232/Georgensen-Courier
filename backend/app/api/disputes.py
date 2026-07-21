from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from datetime import datetime
from app.db.models.dispute import Dispute, DisputeStatus, DisputeType
from app.db.models import Shipment, Invoice, User
from app.db.models.user import User as UserModel
from app.api.deps import get_db, get_current_user, get_current_customer
from app.services.notifications import NotificationService

router = APIRouter(prefix="/api/v1/disputes", tags=["disputes"])


@router.get("/")
async def list_disputes(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all disputes with optional filtering"""
    query = db.query(Dispute)
    
    if status:
        query = query.filter(Dispute.status == status)
    
    disputes = query.offset(skip).limit(limit).all()
    return disputes


@router.get("/{dispute_id}")
async def get_dispute(
    dispute_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dispute details"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute


@router.post("/")
async def create_dispute(
    order_id: int,
    dispute_type: str,
    title: str,
    description: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new dispute"""
    dispute = Dispute(
        order_id=order_id,
        reported_by_id=current_user.id,
        dispute_type=dispute_type,
        title=title,
        description=description,
        dispute_number=f"DSP-{order_id}-{dispute_id}"
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return dispute


@router.put("/{dispute_id}")
async def update_dispute(
    dispute_id: int,
    status: str = None,
    resolution: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update dispute status or resolution"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    if status:
        dispute.status = status
    if resolution:
        dispute.resolution = resolution
    
    db.commit()
    db.refresh(dispute)
    return dispute


@router.delete("/{dispute_id}")
async def delete_dispute(
    dispute_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a dispute"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    db.delete(dispute)
    db.commit()
    return {"message": "Dispute deleted"}


# Customer-facing endpoints

@router.post("/customer/create")
async def create_customer_dispute(
    shipment_id: int,
    dispute_type: str,
    title: str,
    description: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_customer)
):
    """
    Create a dispute against a shipment
    
    Customer endpoint to file disputes for delivery issues
    """
    
    try:
        # Verify shipment exists and belongs to customer
        shipment = db.query(Shipment).filter(
            Shipment.id == shipment_id,
            Shipment.customer_id == current_user.id
        ).first()
        
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found or doesn't belong to you")
        
        # Verify dispute type
        valid_types = [t.value for t in DisputeType]
        if dispute_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid dispute type. Valid: {', '.join(valid_types)}"
            )
        
        # Create dispute
        dispute_number = f"DSP-{shipment_id}-{str(uuid4())[:8]}"
        
        dispute = Dispute(
            shipment_id=shipment_id,
            dispute_number=dispute_number,
            reported_by_id=current_user.id,
            dispute_type=dispute_type,
            title=title,
            description=description,
            status=DisputeStatus.open,
            priority="medium"  # Customer-created disputes are medium priority
        )
        
        db.add(dispute)
        db.commit()
        db.refresh(dispute)
        
        # Send notification to admin
        try:
            from app.services.notifications import NotificationService
            NotificationService.send_alert_email(
                admin_email="support@georgensen.app",
                alert_type="new_dispute",
                details={
                    "Dispute ID": dispute.id,
                    "Dispute Number": dispute_number,
                    "Customer": current_user.email,
                    "Shipment": shipment_id,
                    "Type": dispute_type,
                    "Title": title,
                    "Priority": "medium"
                }
            )
        except Exception:
            pass  # Don't fail on notification error
        
        return {
            "success": True,
            "dispute_id": dispute.id,
            "dispute_number": dispute_number,
            "status": dispute.status,
            "created_at": dispute.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create dispute: {str(e)}"
        )


@router.get("/customer/{dispute_id}")
async def get_customer_dispute(
    dispute_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_customer)
):
    """Get dispute details (customer can only see their own)"""
    
    try:
        dispute = db.query(Dispute).filter(
            Dispute.id == dispute_id,
            Dispute.reported_by_id == current_user.id
        ).first()
        
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        return {
            "success": True,
            "dispute": {
                "id": dispute.id,
                "dispute_number": dispute.dispute_number,
                "shipment_id": dispute.shipment_id,
                "status": dispute.status,
                "dispute_type": dispute.dispute_type,
                "title": dispute.title,
                "description": dispute.description,
                "refund_amount": dispute.refund_amount,
                "created_at": dispute.created_at.isoformat(),
                "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve dispute: {str(e)}"
        )


@router.get("/customer")
async def list_customer_disputes(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_customer)
):
    """List all disputes filed by customer"""
    
    try:
        disputes = db.query(Dispute).filter(
            Dispute.reported_by_id == current_user.id
        ).all()
        
        return {
            "success": True,
            "disputes": [
                {
                    "id": d.id,
                    "dispute_number": d.dispute_number,
                    "shipment_id": d.shipment_id,
                    "status": d.status,
                    "dispute_type": d.dispute_type,
                    "title": d.title,
                    "refund_amount": d.refund_amount,
                    "created_at": d.created_at.isoformat()
                }
                for d in disputes
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve disputes: {str(e)}"
        )
