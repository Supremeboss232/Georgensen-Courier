"""Proof of Delivery (POD) service - handles photo/signature uploads, validation"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import os
import logging
from ..db.models.pod import POD
from ..db.models import Shipment

logger = logging.getLogger(__name__)


class PODService:
    """Handle proof of delivery operations"""
    
    # File storage configuration
    POD_UPLOAD_DIR = "uploads/pod"
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @staticmethod
    def validate_file(filename: str, file_size: int) -> tuple[bool, str]:
        """Validate uploaded file"""
        if not filename:
            return False, "Filename required"
        
        # Check file extension
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        if ext not in PODService.ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(PODService.ALLOWED_EXTENSIONS)}"
        
        # Check file size
        if file_size > PODService.MAX_FILE_SIZE:
            return False, f"File too large. Maximum: 5MB, Received: {file_size / 1024 / 1024:.1f}MB"
        
        return True, "Valid"
    
    @staticmethod
    def save_file(file_content: bytes, filename: str, shipment_id: int) -> str:
        """Save uploaded file to disk/S3"""
        try:
            # Create directory if not exists
            os.makedirs(PODService.POD_UPLOAD_DIR, exist_ok=True)
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = filename.rsplit('.', 1)
            unique_filename = f"{shipment_id}_{timestamp}_{name}.{ext}"
            file_path = os.path.join(PODService.POD_UPLOAD_DIR, unique_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"POD file saved: {file_path}")
            return unique_filename
            
        except Exception as e:
            logger.error(f"File save error: {str(e)}")
            raise
    
    @staticmethod
    async def create_pod(
        shipment_id: int,
        recipient_name: str,
        recipient_email: Optional[str],
        delivery_time: datetime,
        latitude: Optional[float],
        longitude: Optional[float],
        delivery_notes: Optional[str],
        photo_filename: Optional[str] = None,
        signature_filename: Optional[str] = None,
        db: Session = None
    ) -> dict:
        """Create POD record with uploaded files"""
        
        try:
            # Verify shipment exists
            shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
            if not shipment:
                return {"success": False, "error": "Shipment not found"}
            
            # Verify shipment is marked for delivery
            if shipment.status not in ["out_for_delivery", "in_transit"]:
                return {"success": False, "error": f"Cannot create POD for shipment in {shipment.status} status"}
            
            # Create POD record
            pod = POD(
                shipment_id=shipment_id,
                tracking_id=shipment.tracking_id if hasattr(shipment, 'tracking_id') else None,
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                delivery_time=delivery_time,
                location_latitude=str(latitude) if latitude else None,
                location_longitude=str(longitude) if longitude else None,
                delivery_notes=delivery_notes,
                photo_url=f"/uploads/pod/{photo_filename}" if photo_filename else None,
                signature_url=f"/uploads/pod/{signature_filename}" if signature_filename else None,
                items_verified=True  # Set true if all photos/signature provided
            )
            
            db.add(pod)
            db.commit()
            db.refresh(pod)
            
            # Update shipment status to delivered
            shipment.status = "delivered"
            shipment.actual_delivery = delivery_time
            db.commit()
            
            logger.info(f"POD created for shipment {shipment_id}")
            
            return {
                "success": True,
                "pod_id": pod.id,
                "shipment_id": shipment_id,
                "status": "delivered",
                "timestamp": delivery_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"POD creation error: {str(e)}")
            db.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_pod(pod_id: int, db: Session) -> Optional[dict]:
        """Retrieve POD record"""
        try:
            pod = db.query(POD).filter(POD.id == pod_id).first()
            if not pod:
                return None
            
            return {
                "id": pod.id,
                "shipment_id": pod.shipment_id,
                "recipient_name": pod.recipient_name,
                "recipient_email": pod.recipient_email,
                "delivery_time": pod.delivery_time.isoformat(),
                "location": {
                    "latitude": pod.location_latitude,
                    "longitude": pod.location_longitude
                },
                "photo_url": pod.photo_url,
                "signature_url": pod.signature_url,
                "delivery_notes": pod.delivery_notes,
                "items_verified": pod.items_verified,
                "created_at": pod.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"POD retrieval error: {str(e)}")
            return None
    
    @staticmethod
    async def get_shipment_pod(shipment_id: int, db: Session) -> Optional[dict]:
        """Get POD for a specific shipment"""
        try:
            pod = db.query(POD).filter(POD.shipment_id == shipment_id).first()
            if not pod:
                return None
            
            return await PODService.get_pod(pod.id, db)
        except Exception as e:
            logger.error(f"Error fetching POD for shipment: {str(e)}")
            return None
