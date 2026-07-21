"""
Logistics API routes for handling shipment tracking and operations
Includes scan-and-sync endpoints, webhook receivers, and tracking endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.db.models import User, Shipment, ShipmentLog, LogAction, Handler, UserRole
from app.services.logistics import LogisticsService
from app.services.eta import update_shipment_eta
from app.core.rbac import RBACService, Permission

router = APIRouter(prefix="/api/v1/logistics", tags=["Logistics"])


# ==================== Pydantic Models ====================

class ScanCheckpointRequest(BaseModel):
    """Request model for scanning a package checkpoint"""
    tracking_number: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    barcode_scanned: Optional[str] = None
    device_id: Optional[str] = None
    notes: Optional[str] = None


class ShipmentLogResponse(BaseModel):
    """Response model for shipment log entry"""
    id: int
    shipment_id: int
    tracking_number: str
    action: str
    previous_status: Optional[str]
    new_status: Optional[str]
    handler_name: Optional[str]
    hub_name: Optional[str]
    location_name: Optional[str]
    timestamp: datetime
    is_verified: bool
    verification_method: str
    
    class Config:
        from_attributes = True


class ChainOfCustodyResponse(BaseModel):
    """Response model for full chain of custody"""
    tracking_number: str
    status: str
    is_locked: bool
    logs: List[ShipmentLogResponse]
    current_location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


class ShipmentETAResponse(BaseModel):
    """Response model for shipment ETA"""
    tracking_number: str
    estimated_delivery: Optional[datetime]
    estimated_hours: int
    distance_km: float
    current_location: Optional[str]


class WebhookEventRequest(BaseModel):
    """Request model for webhook events from third-party carriers"""
    tracking_number: str
    status: str
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: Optional[datetime] = None
    carrier: str = "external"
    notes: Optional[str] = None


# ==================== Scan & Sync Endpoints ====================

@router.post("/scan", response_model=dict)
async def scan_checkpoint(
    request: ScanCheckpointRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Scan a package at a checkpoint (hub, dispatch, delivery)
    This is the core "Scan-and-Sync" endpoint for handlers and drivers
    
    Requires: driver or handler role
    """
    # RBAC: Verify user is authorized to scan
    RBACService.require_permission(current_user, Permission.SCAN_PACKAGES)
    
    # Find shipment by tracking number
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == request.tracking_number
    ).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment {request.tracking_number} not found"
        )
    
    # Check if shipment is locked (already delivered)
    LogisticsService.validate_state_lock(shipment)
    
    # Create log entry for the scan
    try:
        # Get handler ID if user is a handler/driver
        handler_id = None
        if current_user.role in [UserRole.driver, UserRole.handler]:
            handler_id = current_user.id
        
        log = LogisticsService.log_shipment_action(
            db=db,
            shipment_id=shipment.id,
            action=LogAction.scanned,
            handler_id=handler_id,
            hub_id=current_user.assigned_hub_id,
            latitude=request.latitude,
            longitude=request.longitude,
            location_name=request.location_name,
            barcode_scanned=request.barcode_scanned or request.tracking_number,
            device_id=request.device_id,
            notes=request.notes,
            verification_method="barcode_scan",
        )
        
        return {
            "success": True,
            "message": f"Shipment {request.tracking_number} scanned successfully",
            "tracking_number": shipment.tracking_number,
            "status": shipment.status,
            "log_id": log.id,
            "timestamp": log.timestamp,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error scanning shipment: {str(e)}"
        )


@router.post("/dispatch/{shipment_id}", response_model=dict)
async def dispatch_shipment(
    shipment_id: int,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark shipment as dispatched (leaving warehouse for delivery)
    
    Requires: warehouse_manager or system_admin role
    """
    RBACService.require_permission(current_user, Permission.MANAGE_HUB_SHIPMENTS)
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    LogisticsService.validate_state_lock(shipment)
    
    log = LogisticsService.log_shipment_action(
        db=db,
        shipment_id=shipment_id,
        action=LogAction.dispatched,
        handler_id=current_user.id,
        hub_id=current_user.assigned_hub_id,
        latitude=latitude,
        longitude=longitude,
        notes=notes,
        verification_method="manual",
    )
    
    # Update ETA
    update_shipment_eta(db, shipment_id)
    
    return {
        "success": True,
        "message": "Shipment dispatched",
        "status": shipment.status,
        "log_id": log.id,
    }


@router.post("/deliver/{shipment_id}", response_model=dict)
async def mark_delivered(
    shipment_id: int,
    signature_blob: Optional[str] = None,
    photo_url: Optional[str] = None,
    recipient_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark shipment as delivered with proof of delivery
    This requires signature or photo proof
    Once marked delivered, shipment becomes locked (read-only)
    
    Requires: driver role and assigned to shipment
    """
    RBACService.require_permission(current_user, Permission.UPLOAD_POD)
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Proof of delivery is mandatory
    if not signature_blob and not photo_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proof of delivery required: signature or photo"
        )
    
    log = LogisticsService.log_shipment_action(
        db=db,
        shipment_id=shipment_id,
        action=LogAction.delivered,
        handler_id=current_user.id,
        hub_id=current_user.assigned_hub_id,
        proof_image_url=photo_url,
        verification_method="manual",
    )
    
    # Lock shipment and store proof
    shipment.is_locked = True
    shipment.delivery_proof_signature = signature_blob
    shipment.delivery_proof_photo = photo_url
    shipment.actual_delivery = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Shipment delivered and locked",
        "tracking_number": shipment.tracking_number,
        "status": shipment.status,
        "is_locked": True,
    }


# ==================== Chain of Custody Endpoints ====================

@router.get("/chain-of-custody/{tracking_number}", response_model=ChainOfCustodyResponse)
async def get_chain_of_custody(
    tracking_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get complete chain of custody (audit trail) for a shipment
    Shows every touch point, scan, and status change
    """
    RBACService.require_permission(current_user, Permission.TRACK_SHIPMENT)
    
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    logs = LogisticsService.get_shipment_chain_of_custody(db, shipment.id)
    
    return ChainOfCustodyResponse(
        tracking_number=shipment.tracking_number,
        status=shipment.status,
        is_locked=shipment.is_locked,
        current_location=shipment.current_location,
        latitude=shipment.latitude,
        longitude=shipment.longitude,
        logs=[ShipmentLogResponse.from_orm(log) for log in logs],
    )


# ==================== ETA & Tracking Endpoints ====================

@router.get("/eta/{tracking_number}", response_model=ShipmentETAResponse)
async def get_eta(
    tracking_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get estimated time of arrival for a shipment"""
    RBACService.require_permission(current_user, Permission.TRACK_SHIPMENT)
    
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Update ETA if needed
    update_shipment_eta(db, shipment.id)
    shipment = db.query(Shipment).filter(Shipment.id == shipment.id).first()
    
    estimated_hours = 0
    distance_km = 0.0
    if shipment.estimated_delivery:
        estimated_hours = int(
            (shipment.estimated_delivery - datetime.utcnow()).total_seconds() / 3600
        )
    
    return ShipmentETAResponse(
        tracking_number=shipment.tracking_number,
        estimated_delivery=shipment.estimated_delivery,
        estimated_hours=max(0, estimated_hours),
        distance_km=distance_km,
        current_location=shipment.current_location,
    )


# ==================== Webhook Endpoints (Third-Party Integration) ====================

@router.post("/webhook/carrier-update", response_model=dict)
async def webhook_carrier_update(
    event: WebhookEventRequest,
    db: Session = Depends(get_db),
):
    """
    Receive tracking update from third-party carrier (FedEx, UPS, etc.)
    This endpoint requires API key authentication in production
    """
    # In production, verify webhook signature/API key here
    
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == event.tracking_number
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Map carrier status to our status
    action = LogisticsService._action_to_status(LogAction.in_transit)  # Default mapping
    
    try:
        log = LogisticsService.log_shipment_action(
            db=db,
            shipment_id=shipment.id,
            action=LogAction.in_transit,
            latitude=event.latitude,
            longitude=event.longitude,
            location_name=event.location_name,
            notes=f"Update from {event.carrier}: {event.notes}",
            verification_method="webhook",
        )
        
        return {
            "success": True,
            "message": "Carrier update received",
            "tracking_number": event.tracking_number,
            "log_id": log.id,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing webhook: {str(e)}"
        )


# ==================== Hub Activity Endpoints ====================

@router.get("/hub/{hub_id}/activity", response_model=dict)
async def get_hub_activity(
    hub_id: int,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get activity statistics for a hub"""
    RBACService.require_permission(current_user, Permission.VIEW_HUB_ANALYTICS)
    
    activity = LogisticsService.get_hub_activity(db, hub_id, hours)
    return activity


@router.get("/handler/{handler_id}/stats", response_model=dict)
async def get_handler_stats(
    handler_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get performance statistics for a handler"""
    RBACService.require_permission(current_user, Permission.VIEW_HUB_ANALYTICS)
    
    stats = LogisticsService.get_handler_statistics(db, handler_id)
    return stats
