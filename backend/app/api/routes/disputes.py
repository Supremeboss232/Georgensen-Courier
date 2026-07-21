from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.models.dispute import Dispute, DisputeStatus
from app.api.deps import get_db, get_current_user
from app.db.models.user import User

router = APIRouter(prefix="/disputes", tags=["disputes"])


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
