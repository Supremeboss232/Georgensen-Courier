from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.base import get_db
from app.db.models import Shipment, TrackingHistory, User, POD
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
    """
    Get tracking information by tracking number (public endpoint)
    Supports Canada-global operations with customs tracking, timezone localization
    """
    
    # Query shipment by tracking number
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number
    ).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking number not found"
        )
    
    # Get tracking history
    history = db.query(TrackingHistory).filter(
        TrackingHistory.shipment_id == shipment.id
    ).order_by(TrackingHistory.created_at.desc()).all()
    
    # Get proof of delivery if delivered
    pod = db.query(POD).filter(
        POD.shipment_id == shipment.id
    ).first()
    
    # CANADA-GLOBAL: Extract country codes from postal codes
    def extract_country_code(postal_code):
        """Extract country code from postal code format"""
        if not postal_code:
            return None
        # Canadian postal codes start with letters A-Y (excluding D, F, I, O, Q, U)
        first_char = postal_code[0].upper()
        if first_char in 'ABCEGHJKLMNPRSTVWXYZ':
            return 'CA'
        # US 5-digit zip codes
        elif postal_code.isdigit() and len(postal_code) == 5:
            return 'US'
        return None
    
    origin_country = extract_country_code(shipment.pickup_zip)
    destination_country = extract_country_code(shipment.delivery_zip)
    
    # Determine if international shipment
    is_international = (
        origin_country and destination_country and 
        origin_country != destination_country
    )
    
    # CANADA-GLOBAL: Map postal code first letters to Canadian provinces for timezone
    def get_timezone_from_postal(postal_code, country):
        """Get timezone from postal code"""
        if not postal_code or country != 'CA':
            # US timezones - simplified
            return 'EST'  # Default to Eastern
        
        first_char = postal_code[0].upper()
        timezone_map = {
            'A': 'NST', 'B': 'AST', 'C': 'AST', 'E': 'AST',  # Atlantic provinces
            'G': 'EST', 'H': 'EST', 'J': 'EST',  # Quebec (EST but bilingual)
            'K': 'EST', 'L': 'EST', 'M': 'EST', 'N': 'EST', 'P': 'EST',  # Ontario (EST)
            'R': 'CST', 'S': 'CST',  # Manitoba/Saskatchewan (CST)
            'T': 'MST',  # Alberta (Mountain)
            'V': 'PST',  # BC (Pacific)
            'X': 'CST', 'Y': 'PST',  # Territories (vary, use CST/PST)
        }
        return timezone_map.get(first_char, 'EST')
    
    origin_timezone = get_timezone_from_postal(shipment.pickup_zip, origin_country)
    destination_timezone = get_timezone_from_postal(shipment.delivery_zip, destination_country)
    
    # CANADA-GLOBAL: Determine customs status if international
    customs_status = None
    estimated_clearance_date = None
    customs_fee = 0.0
    
    if is_international:
        # Check if any tracking history shows customs states
        customs_states = ['in_customs', 'cleared_customs', 'duties_pending', 'release_pending']
        
        # Find most recent customs-related event
        for h in history:
            if h.status in customs_states:
                customs_status = h.status
                break
        
        # Default to in_customs if international and no specific status
        if not customs_status:
            customs_status = 'in_customs'
        
        # Calculate estimated clearance (24-48 hours from entry)
        if history:
            latest_event = history[0]
            if latest_event.created_at:
                from datetime import timedelta
                estimated_clearance_date = (
                    latest_event.created_at + timedelta(hours=24)
                ).isoformat()
        
        # CANADA-GLOBAL: Standard customs fee for cross-border shipments
        customs_fee = 50.00  # CAD
    
    # Build response with Canada-global support
    response = {
        "tracking_number": tracking_number,
        "status": shipment.status,
        "service_type": shipment.service_type or "standard",
        "speed": shipment.speed or "standard",
        "pickup_address": shipment.pickup_address,
        "delivery_address": shipment.delivery_address,
        "pickup_zip": shipment.pickup_zip,
        "delivery_zip": shipment.delivery_zip,
        "current_location": shipment.current_location or "In transit",
        "estimated_delivery": shipment.estimated_delivery.isoformat() if shipment.estimated_delivery else None,
        "last_update": shipment.updated_at.isoformat() if shipment.updated_at else None,
        
        # CANADA-GLOBAL: Country and timezone information
        "origin_country": origin_country,
        "destination_country": destination_country,
        "origin_timezone": origin_timezone,
        "destination_timezone": destination_timezone,
        "is_international": is_international,
        
        # Customs information for international shipments
        "customs_status": customs_status,
        "estimated_clearance_date": estimated_clearance_date,
        "customs_fee": customs_fee,
        
        # Service level for display
        "service_display": {
            "zone_1": "Same-Day Courier",
            "zone_2": "Regional (2-3 days)",
            "zone_3": "Continental (3-5 days)",
            "zone_4": "Global Express Air",
            "zone_5": "Ocean Freight",
            "economy": "Economy (5-7 days)",
            "standard": "Standard (2-3 days)",
            "express": "Express (24 hours)",
            "overnight": "Overnight"
        },
        
        # Complete tracking history - formatted for frontend timeline
        "raw_history": [
            {
                "status": h.status,
                "location": h.location,
                "timestamp": h.created_at.isoformat() if h.created_at else None,
                "notes": h.notes,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "country_code": extract_country_code(h.location) if h.location else None,
                "created_at": h.created_at.isoformat() if h.created_at else None,
                "event": "location_update"
            }
            for h in history
        ],
        
        # Proof of delivery if available
        "proof_of_delivery": {
            "recipient_name": pod.recipient_name,
            "delivery_notes": pod.delivery_notes,
            "delivery_time": pod.delivery_time.isoformat() if pod.delivery_time else None,
            "signature_url": pod.signature_url,
            "photo_url": pod.photo_url
        } if pod else None
    }
    
    return response


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
