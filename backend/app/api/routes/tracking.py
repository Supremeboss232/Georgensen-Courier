from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.base import get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.models import Shipment, Tracking, POD, User
from app.api.deps import get_current_user
from app.schemas.tracking import Tracking as TrackingResponse
from app.schemas.order import ShipmentResponse, TrackingHistoryResponse
from app.api.deps import get_current_user


router = APIRouter(
    prefix="/api/v1/tracking",
    tags=["Tracking"]
)


@router.get("/{tracking_number}")
async def get_tracking_by_number(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """Get tracking information by tracking number (public endpoint)"""
    
    order = db.query(Order).filter(Order.tracking_number == tracking_number).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking number not found"
        )
    
    shipment = db.query(Shipment).filter(Shipment.order_id == order.id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment information not found"
        )
    
    # Get tracking history
    history = db.query(TrackingHistory).filter(
        TrackingHistory.shipment_id == shipment.id
    ).order_by(TrackingHistory.created_at.desc()).all()
    
    # Get proof of delivery if delivered
    pod = db.query(ProofOfDelivery).filter(
        ProofOfDelivery.shipment_id == shipment.id
    ).first()
    
    return {
        "tracking_number": tracking_number,
        "status": order.status,
        "service_type": order.service_type,
        "speed": order.speed,
        "pickup_address": order.pickup_address,
        "delivery_address": order.delivery_address,
        "current_location": shipment.current_location or "In transit",
        "estimated_delivery": None,
        "last_update": shipment.updated_at,
        "history": [
            {
                "status": h.status,
                "location": h.location,
                "timestamp": h.created_at,
                "notes": h.notes
            }
            for h in history[:10]  # Last 10 updates
        ],
        "proof_of_delivery": {
            "recipient_name": pod.recipient_name,
            "delivery_notes": pod.delivery_notes,
            "delivery_time": pod.created_at,
            "signature_path": pod.signature_path,
            "photo_path": pod.photo_path
        } if pod else None
    }


@router.get("/shipment/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment_details(
    shipment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed shipment information"""
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    # Check authorization
    order = shipment.order
    if current_user.role == "customer" and order.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    elif current_user.role == "partner" and order.assigned_partner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return shipment


@router.get("/history/{shipment_id}")
async def get_tracking_history(
    shipment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete tracking history for shipment"""
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    # Get history entries
    history = db.query(TrackingHistory).filter(
        TrackingHistory.shipment_id == shipment_id
    ).order_by(TrackingHistory.created_at).all()
    
    return {
        "shipment_id": shipment_id,
        "tracking_number": shipment.tracking_number,
        "total_updates": len(history),
        "history": [
            {
                "id": h.id,
                "status": h.status,
                "location": h.location,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "notes": h.notes,
                "updated_by": h.updated_by,
                "timestamp": h.created_at
            }
            for h in history
        ]
    }


@router.post("/update-location")
async def update_location(
    location_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update shipment location (partner only)"""
    
    if current_user.role != "partner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only partners can update location"
        )
    
    shipment_id = location_data.get("shipment_id")
    latitude = location_data.get("latitude")
    longitude = location_data.get("longitude")
    location = location_data.get("location", "Unknown")
    notes = location_data.get("notes", "")
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    # Check authorization
    order = shipment.order
    if order.assigned_partner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this shipment"
        )
    
    # Update shipment location
    shipment.current_location = location
    if latitude:
        shipment.latitude = latitude
    if longitude:
        shipment.longitude = longitude
    
    # Add to history
    history = TrackingHistory(
        shipment_id=shipment.id,
        tracking_number=shipment.tracking_number,
        status=shipment.current_status,
        location=location,
        latitude=latitude,
        longitude=longitude,
        notes=notes,
        updated_by=current_user.id
    )
    
    db.add(history)
    db.commit()
    db.refresh(shipment)
    
    return {
        "message": "Location updated",
        "shipment_id": shipment_id,
        "current_location": location,
        "coordinates": {
            "latitude": latitude,
            "longitude": longitude
        }
    }


@router.post("/update-status")
async def update_shipment_status(
    status_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update shipment status (partner only)"""
    
    if current_user.role != "partner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only partners can update status"
        )
    
    shipment_id = status_data.get("shipment_id")
    new_status = status_data.get("status")
    notes = status_data.get("notes", "")
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    # Check authorization
    order = shipment.order
    if order.assigned_partner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Update shipment and order
    shipment.current_status = new_status
    order.status = new_status
    
    # Add to history
    history = TrackingHistory(
        shipment_id=shipment.id,
        tracking_number=shipment.tracking_number,
        status=new_status,
        location=shipment.current_location,
        latitude=shipment.latitude,
        longitude=shipment.longitude,
        notes=notes,
        updated_by=current_user.id
    )
    
    db.add(history)
    db.commit()
    
    return {
        "message": "Status updated",
        "shipment_id": shipment_id,
        "status": new_status
    }


@router.post("/submit-proof-of-delivery")
async def submit_proof_of_delivery(
    delivery_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit proof of delivery (partner only)"""
    
    if current_user.role != "partner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only partners can submit delivery proof"
        )
    
    shipment_id = delivery_data.get("shipment_id")
    recipient_name = delivery_data.get("recipient_name")
    delivery_notes = delivery_data.get("delivery_notes", "")
    signature_path = delivery_data.get("signature_path")
    photo_path = delivery_data.get("photo_path")
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    # Check if already submitted
    existing_pod = db.query(ProofOfDelivery).filter(
        ProofOfDelivery.shipment_id == shipment_id
    ).first()
    if existing_pod:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proof of delivery already submitted"
        )
    
    # Create proof of delivery
    pod = ProofOfDelivery(
        shipment_id=shipment.id,
        tracking_number=shipment.tracking_number,
        signature_path=signature_path,
        photo_path=photo_path,
        recipient_name=recipient_name,
        delivery_notes=delivery_notes
    )
    
    # Update shipment and order status
    shipment.current_status = "delivered"
    shipment.order.status = "delivered"
    
    db.add(pod)
    db.commit()
    
    return {
        "message": "Proof of delivery submitted",
        "shipment_id": shipment_id,
        "recipient_name": recipient_name,
        "delivery_time": pod.created_at
    }
