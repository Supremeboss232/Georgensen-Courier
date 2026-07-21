"""
Logistics Service for handling shipments through the supply chain
Manages scanning, status updates, and audit trail (Chain of Custody)
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import (
    Shipment, ShipmentLog, LogAction, Handler, Hub, FleetVehicle,
    ShipmentStatus
)
from app.services.eta import update_shipment_eta


class LogisticsService:
    """Service for managing shipment logistics and audit trail"""
    
    @staticmethod
    def log_shipment_action(
        db: Session,
        shipment_id: int,
        action: LogAction,
        handler_id: Optional[int] = None,
        hub_id: Optional[int] = None,
        vehicle_id: Optional[int] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location_name: Optional[str] = None,
        barcode_scanned: Optional[str] = None,
        device_id: Optional[str] = None,
        notes: Optional[str] = None,
        proof_image_url: Optional[str] = None,
        verification_method: str = "barcode_scan",
    ) -> ShipmentLog:
        """
        Create an audit log entry for a shipment action
        This implements the "Chain of Custody" tracking
        
        Args:
            db: Database session
            shipment_id: ID of the shipment
            action: Type of action (scanned, dispatched, delivered, etc.)
            handler_id: Handler performing the action
            hub_id: Hub where action occurred
            vehicle_id: Vehicle involved
            latitude: Geographic latitude
            longitude: Geographic longitude
            location_name: Human-readable location
            barcode_scanned: Barcode/QR code that was scanned
            device_id: Scanner or device ID
            notes: Additional notes
            proof_image_url: Photo/signature URL
            verification_method: How action was verified (barcode_scan, gps, manual, webhook)
        
        Returns:
            Created ShipmentLog object
        """
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            raise ValueError(f"Shipment {shipment_id} not found")
        
        # Get previous status
        previous_status = shipment.status
        
        # Determine new status based on action
        new_status = LogisticsService._action_to_status(action)
        
        # Get handler info if provided
        handler_name = None
        if handler_id:
            handler = db.query(Handler).filter(Handler.id == handler_id).first()
            if handler:
                handler_name = handler.full_name
        
        # Get hub info if provided
        hub_name = None
        if hub_id:
            hub = db.query(Hub).filter(Hub.id == hub_id).first()
            if hub:
                hub_name = hub.name
        
        # Get vehicle info if provided
        vehicle_plate = None
        if vehicle_id:
            vehicle = db.query(FleetVehicle).filter(FleetVehicle.id == vehicle_id).first()
            if vehicle:
                vehicle_plate = vehicle.plate_number
        
        # Create log entry
        log = ShipmentLog(
            shipment_id=shipment_id,
            tracking_number=shipment.tracking_number,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            handler_id=handler_id,
            handler_name=handler_name,
            hub_id=hub_id,
            hub_name=hub_name,
            vehicle_id=vehicle_id,
            vehicle_plate=vehicle_plate,
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            barcode_scanned=barcode_scanned,
            device_id=device_id,
            notes=notes,
            proof_image_url=proof_image_url,
            is_verified=verification_method != "manual",
            verification_method=verification_method,
            timestamp=datetime.utcnow(),
        )
        
        db.add(log)
        
        # Update shipment status if necessary
        if new_status:
            shipment.status = new_status
            shipment.updated_at = datetime.utcnow()
            
            # Update location if provided
            if latitude and longitude:
                shipment.latitude = latitude
                shipment.longitude = longitude
                shipment.last_location_update = datetime.utcnow()
            
            if location_name:
                shipment.current_location = location_name
            
            if hub_id:
                shipment.current_hub_id = hub_id
            
            if handler_id:
                shipment.assigned_handler_id = handler_id
            
            if vehicle_id:
                shipment.assigned_vehicle_id = vehicle_id
            
            # Check if shipment is delivered - if so, lock it
            if new_status == ShipmentStatus.DELIVERED:
                shipment.is_locked = True
                shipment.actual_delivery = datetime.utcnow()
        
        db.commit()
        return log
    
    @staticmethod
    def _action_to_status(action: LogAction) -> Optional[str]:
        """Convert LogAction to ShipmentStatus"""
        action_to_status_map = {
            LogAction.order_received: ShipmentStatus.ORDER_RECEIVED,
            LogAction.payment_confirmed: ShipmentStatus.PROCESSING,
            LogAction.processing: ShipmentStatus.PROCESSING,
            LogAction.scanned: ShipmentStatus.PROCESSING,
            LogAction.packed: ShipmentStatus.PROCESSING,
            LogAction.sorted: ShipmentStatus.PROCESSING,
            LogAction.dispatched: ShipmentStatus.PICKED_UP,
            LogAction.pickup_started: ShipmentStatus.PICKED_UP,
            LogAction.picked_up: ShipmentStatus.PICKED_UP,
            LogAction.in_transit: ShipmentStatus.IN_TRANSIT,
            LogAction.at_hub: ShipmentStatus.IN_TRANSIT,
            LogAction.departed_hub: ShipmentStatus.IN_TRANSIT,
            LogAction.out_for_delivery: ShipmentStatus.OUT_FOR_DELIVERY,
            LogAction.delivery_attempt: ShipmentStatus.OUT_FOR_DELIVERY,
            LogAction.delivered: ShipmentStatus.DELIVERED,
            LogAction.delivery_failed: ShipmentStatus.FAILED_DELIVERY,
            LogAction.returned: ShipmentStatus.CANCELLED,
        }
        return action_to_status_map.get(action)
    
    @staticmethod
    def get_shipment_chain_of_custody(db: Session, shipment_id: int) -> list:
        """
        Get complete audit trail (Chain of Custody) for a shipment
        
        Args:
            db: Database session
            shipment_id: Shipment ID
        
        Returns:
            List of ShipmentLog entries ordered by timestamp
        """
        logs = (
            db.query(ShipmentLog)
            .filter(ShipmentLog.shipment_id == shipment_id)
            .order_by(ShipmentLog.timestamp.asc())
            .all()
        )
        return logs
    
    @staticmethod
    def lock_shipment_for_delivery(db: Session, shipment_id: int, proof_signature: str) -> bool:
        """
        Lock a shipment as delivered with proof of delivery signature
        Once locked, shipment becomes read-only
        
        Args:
            db: Database session
            shipment_id: Shipment ID
            proof_signature: Base64 encoded signature image
        
        Returns:
            True if locked successfully, False otherwise
        """
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return False
        
        shipment.is_locked = True
        shipment.status = ShipmentStatus.DELIVERED
        shipment.actual_delivery = datetime.utcnow()
        shipment.delivery_proof_signature = proof_signature
        db.commit()
        
        return True
    
    @staticmethod
    def validate_state_lock(shipment: Shipment) -> None:
        """
        Validate that locked shipments cannot be modified
        Should be called before any update to a delivered shipment
        
        Args:
            shipment: Shipment object
        
        Raises:
            RuntimeError if shipment is locked
        """
        if shipment.is_locked:
            raise RuntimeError(
                f"Shipment {shipment.tracking_number} is locked (delivered). "
                "Read-only state enforced."
            )
    
    @staticmethod
    def get_handler_statistics(db: Session, handler_id: int) -> dict:
        """
        Get performance statistics for a handler
        
        Args:
            db: Database session
            handler_id: Handler ID
        
        Returns:
            Dictionary with handler statistics
        """
        logs = (
            db.query(ShipmentLog)
            .filter(ShipmentLog.handler_id == handler_id)
            .all()
        )
        
        total_actions = len(logs)
        deliveries = len([l for l in logs if l.action == LogAction.delivered])
        failed = len([l for l in logs if l.action == LogAction.delivery_failed])
        
        return {
            "handler_id": handler_id,
            "total_actions": total_actions,
            "successful_deliveries": deliveries,
            "failed_deliveries": failed,
            "success_rate": deliveries / total_actions if total_actions > 0 else 0,
        }
    
    @staticmethod
    def get_hub_activity(db: Session, hub_id: int, hours: int = 24) -> dict:
        """
        Get activity statistics for a hub
        
        Args:
            db: Database session
            hub_id: Hub ID
            hours: Time window in hours
        
        Returns:
            Dictionary with hub activity statistics
        """
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        logs = (
            db.query(ShipmentLog)
            .filter(
                ShipmentLog.hub_id == hub_id,
                ShipmentLog.timestamp >= cutoff_time
            )
            .all()
        )
        
        actions_by_type = {}
        for log in logs:
            action = str(log.action.value)
            actions_by_type[action] = actions_by_type.get(action, 0) + 1
        
        return {
            "hub_id": hub_id,
            "hours": hours,
            "total_actions": len(logs),
            "actions_by_type": actions_by_type,
        }
