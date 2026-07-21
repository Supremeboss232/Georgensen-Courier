"""Proof of Delivery API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from typing import Optional

from app.db.base import get_db
from app.db.models import User, Shipment
from app.api.deps import get_current_user, get_current_partner
from app.services.pod import PODService
from app.services.notifications import NotificationService

router = APIRouter(
    prefix="/api/v1/shipments",
    tags=["Proof of Delivery"]
)


@router.post("/{shipment_id}/proof-of-delivery")
async def upload_proof_of_delivery(
    shipment_id: int,
    recipient_name: str = Form(...),
    recipient_email: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    delivery_notes: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    signature: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """
    Upload proof of delivery (photo/signature)
    
    Partner endpoint to confirm delivery with photo and/or signature
    
    Args:
        shipment_id: Shipment to deliver
        recipient_name: Name of delivery recipient
        recipient_email: Email of recipient (optional)
        latitude: Delivery location latitude
        longitude: Delivery location longitude
        delivery_notes: Notes about delivery/condition
        photo: Photo file (jpg, png, gif, pdf - max 5MB)
        signature: Signature file (jpg, png, gif, pdf - max 5MB)
    
    Returns:
        POD confirmation with status
    """
    
    try:
        # Verify shipment exists and is assigned to current partner
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        # Verify partner is assigned to this shipment
        if hasattr(shipment, 'assigned_partner_id') and shipment.assigned_partner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not assigned to this shipment")
        
        # Validate at least photo OR signature provided
        if not photo and not signature:
            raise HTTPException(
                status_code=400,
                detail="At least one of photo or signature required"
            )
        
        photo_filename = None
        signature_filename = None
        
        # Process photo
        if photo:
            # Validate file
            content = await photo.read()
            is_valid, error_msg = PODService.validate_file(photo.filename, len(content))
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Save file
            photo_filename = PODService.save_file(content, photo.filename, shipment_id)
        
        # Process signature
        if signature:
            # Validate file
            content = await signature.read()
            is_valid, error_msg = PODService.validate_file(signature.filename, len(content))
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Save file
            signature_filename = PODService.save_file(content, signature.filename, shipment_id)
        
        # Create POD record
        result = await PODService.create_pod(
            shipment_id=shipment_id,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            delivery_time=datetime.now(),
            latitude=latitude,
            longitude=longitude,
            delivery_notes=delivery_notes,
            photo_filename=photo_filename,
            signature_filename=signature_filename,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
        
        # Send confirmation email to customer if available
        if shipment.customer_id and recipient_email:
            try:
                # You can enhance this with actual email sending
                await NotificationService.send_delivery_confirmation_email(
                    recipient_email=recipient_email,
                    shipment_id=shipment_id,
                    tracking_number=getattr(shipment, 'tracking_number', 'GEO-XXXXX')
                )
            except Exception as e:
                # Log but don't fail on email error
                print(f"Failed to send confirmation email: {str(e)}")
        
        return {
            "success": True,
            "message": "Proof of delivery recorded",
            "pod": result,
            "photo_url": f"/uploads/pod/{photo_filename}" if photo_filename else None,
            "signature_url": f"/uploads/pod/{signature_filename}" if signature_filename else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process proof of delivery: {str(e)}"
        )


@router.get("/{shipment_id}/proof-of-delivery")
async def get_proof_of_delivery(
    shipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve proof of delivery for shipment
    
    Available to customer (owns shipment), partner (delivered it), or admin
    """
    
    try:
        # Verify shipment exists
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        # Check permissions
        is_customer = shipment.customer_id == current_user.id
        is_partner = hasattr(shipment, 'assigned_partner_id') and shipment.assigned_partner_id == current_user.id
        is_admin = current_user.role == "admin"
        
        if not (is_customer or is_partner or is_admin):
            raise HTTPException(status_code=403, detail="Not authorized to view this POD")
        
        # Get POD
        pod = await PODService.get_shipment_pod(shipment_id, db)
        
        if not pod:
            raise HTTPException(status_code=404, detail="Proof of delivery not found")
        
        return {
            "success": True,
            "pod": pod
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve POD: {str(e)}"
        )


@router.delete("/{shipment_id}/proof-of-delivery")
async def delete_proof_of_delivery(
    shipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete POD (admin only)
    
    Can only be used if shipment needs re-delivery
    """
    
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        
        # Verify shipment exists
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        # Get and delete POD
        from app.db.models import POD
        pod = db.query(POD).filter(POD.shipment_id == shipment_id).first()
        
        if not pod:
            raise HTTPException(status_code=404, detail="Proof of delivery not found")
        
        db.delete(pod)
        
        # Reset shipment status back to out_for_delivery
        shipment.status = "out_for_delivery"
        db.commit()
        
        return {
            "success": True,
            "message": "POD deleted, shipment status reset to out_for_delivery"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete POD: {str(e)}"
        )
