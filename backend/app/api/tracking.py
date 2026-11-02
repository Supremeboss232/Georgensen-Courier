from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.db.base import get_db
from app.db.models import User, Shipment, ShipmentStatus, TrackingHistory, POD
from app.schemas.order import ProofOfDeliverySubmit
from app.api.deps import get_current_user, get_current_partner

router = APIRouter(prefix="/api/v1/tracking", tags=["Tracking"])


@router.get("/{tracking_number}")
async def track_shipment(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """Public endpoint to track shipment by tracking number"""
    shipment = db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    history = db.query(TrackingHistory).filter(
        TrackingHistory.shipment_id == shipment.id
    ).order_by(TrackingHistory.created_at.desc()).all()

    return {
        "id": str(shipment.id),
        "shipment_id": shipment.id,
        "tracking_number": shipment.tracking_number,
        "status": str(shipment.status),
        "current_status": str(shipment.status),
        "current_location": shipment.current_location or shipment.pickup_city,
        "latitude": shipment.latitude,
        "longitude": shipment.longitude,
        "pickup_address": shipment.pickup_address,
        "pickup_city": shipment.pickup_city,
        "delivery_address": shipment.delivery_address,
        "delivery_city": shipment.delivery_city,
        "service_type": shipment.service_type,
        "speed": shipment.speed,
        "estimated_delivery": shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
        "actual_delivery": shipment.actual_delivery.isoformat() if shipment.actual_delivery else None,
        "history": [
            {
                "id": str(h.id),
                "status": str(h.status),
                "location": h.location,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "notes": h.notes,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in history
        ]
    }


@router.post("/{order_id}/update-status")
async def update_tracking_status(
    order_id: int,
    new_status: str,
    location: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Update shipment status (partner/admin only)"""
    shipment = db.query(Shipment).filter(Shipment.id == order_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val not in ("admin", "system_admin") and not current_user.is_superuser:
        if shipment.assigned_partner_id and shipment.assigned_partner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not assigned to this order"
            )

    shipment.status = new_status
    if location:
        shipment.current_location = location

    if new_status == ShipmentStatus.PICKED_UP.value or new_status == "picked_up":
        shipment.pickup_at = datetime.utcnow()
    elif new_status == ShipmentStatus.DELIVERED.value or new_status == "delivered":
        shipment.actual_delivery = datetime.utcnow()

    tracking = TrackingHistory(
        shipment_id=shipment.id,
        tracking_number=shipment.tracking_number,
        partner_id=current_user.id,
        status=new_status,
        location=location or shipment.current_location,
        notes=notes
    )

    db.add(shipment)
    db.add(tracking)
    db.commit()
    db.refresh(shipment)

    return {
        "message": "Status updated",
        "order_id": str(order_id),
        "new_status": new_status
    }


@router.post("/{order_id}/pod")
async def submit_proof_of_delivery(
    order_id: int,
    pod_data: ProofOfDeliverySubmit,
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """Submit proof of delivery (partner/admin only)"""
    shipment = db.query(Shipment).filter(Shipment.id == order_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val not in ("admin", "system_admin") and not current_user.is_superuser:
        if shipment.assigned_partner_id and shipment.assigned_partner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not assigned to this order"
            )

    existing_pod = db.query(POD).filter(POD.shipment_id == order_id).first()
    if existing_pod:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="POD already submitted for this order"
        )

    pod = POD(
        shipment_id=order_id,
        recipient_name=pod_data.recipient_name,
        delivery_notes=pod_data.notes,
        signature_url=pod_data.signature_path,
        photo_url=pod_data.photo_path,
        delivery_time=datetime.utcnow(),
        items_verified=True
    )

    shipment.status = ShipmentStatus.DELIVERED.value
    shipment.actual_delivery = datetime.utcnow()

    tracking = TrackingHistory(
        shipment_id=order_id,
        tracking_number=shipment.tracking_number,
        partner_id=current_user.id,
        status=ShipmentStatus.DELIVERED.value,
        notes=f"Delivered to {pod_data.recipient_name}"
    )

    db.add(pod)
    db.add(shipment)
    db.add(tracking)
    db.commit()
    db.refresh(pod)

    return {
        "message": "Proof of delivery submitted",
        "pod_id": str(pod.id),
        "order_id": str(order_id)
    }
