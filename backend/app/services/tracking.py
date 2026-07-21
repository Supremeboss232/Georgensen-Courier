"""
Real-time tracking service
Handles GPS updates, location broadcasting, and tracking history
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Dict
import logging
from app.db.models import Shipment, TrackingHistory, Tracking, Partner

logger = logging.getLogger(__name__)


class TrackingService:
    """Service for managing real-time shipment tracking"""
    
    # In-memory store for active connections (WebSocket)
    # In production: use Redis for multi-server setup
    _active_shipments = {}  # tracking_number -> {connections, last_update}
    
    @staticmethod
    def record_tracking_update(
        db: Session,
        shipment_id: int,
        tracking_number: str,
        status: str,
        latitude: float,
        longitude: float,
        location: str = None,
        notes: str = None,
        partner_id: int = None,
        distance_traveled: float = None
    ) -> TrackingHistory:
        """
        Record a GPS/status update for a shipment
        
        Args:
            db: Database session
            shipment_id: Shipment ID
            tracking_number: Tracking number
            status: Current status (picked_up, in_transit, etc.)
            latitude: Current latitude
            longitude: Current longitude
            location: Human-readable location name
            notes: Additional notes
            partner_id: Partner ID (if relevant)
            distance_traveled: Distance since last update (km)
        
        Returns:
            TrackingHistory record
        """
        try:
            # Create tracking history entry
            history = TrackingHistory(
                shipment_id=shipment_id,
                tracking_number=tracking_number,
                partner_id=partner_id,
                status=status,
                location=location,
                latitude=latitude,
                longitude=longitude,
                notes=notes,
                distance_traveled=distance_traveled
            )
            
            db.add(history)
            
            # Update the main Tracking record
            tracking = db.query(Tracking).filter(
                Tracking.shipment_id == shipment_id
            ).first()
            
            if tracking:
                tracking.current_status = status
                tracking.latitude = latitude
                tracking.longitude = longitude
                tracking.current_location = location or f"{latitude},{longitude}"
                tracking.updated_at = datetime.utcnow()
                db.add(tracking)
            
            # Update Shipment status
            shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
            if shipment:
                shipment.status = status
                shipment.latitude = latitude
                shipment.longitude = longitude
                shipment.current_location = location or f"{latitude},{longitude}"
                shipment.updated_at = datetime.utcnow()
                db.add(shipment)
            
            db.commit()
            
            logger.info(f"✓ Tracking update recorded: {tracking_number} - {status} @ ({latitude}, {longitude})")
            
            return history
            
        except Exception as e:
            db.rollback()
            logger.error(f"✗ Error recording tracking update: {str(e)}")
            raise
    
    @staticmethod
    def get_shipment_tracking_history(
        db: Session,
        shipment_id: int,
        limit: int = 50
    ) -> List[TrackingHistory]:
        """Get tracking history for a shipment"""
        return db.query(TrackingHistory).filter(
            TrackingHistory.shipment_id == shipment_id
        ).order_by(TrackingHistory.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_tracking_status(
        db: Session,
        tracking_number: str
    ) -> Optional[Dict]:
        """Get current tracking status by tracking number"""
        try:
            # Find shipment by tracking number
            shipment = db.query(Shipment).filter(
                Shipment.tracking_number == tracking_number
            ).first()
            
            if not shipment:
                return None
            
            # Get latest tracking update
            latest_update = db.query(TrackingHistory).filter(
                TrackingHistory.shipment_id == shipment.id
            ).order_by(TrackingHistory.created_at.desc()).first()
            
            return {
                "tracking_number": tracking_number,
                "shipment_id": shipment.id,
                "status": latest_update.status if latest_update else "pending",
                "latitude": shipment.latitude,
                "longitude": shipment.longitude,
                "location": shipment.current_location,
                "pickup_address": shipment.pickup_address,
                "delivery_address": shipment.delivery_address,
                "estimated_delivery": shipment.estimated_delivery,
                "partner_id": shipment.assigned_partner_id,
                "last_update": latest_update.created_at.isoformat() if latest_update else None,
                "raw_history": [h.to_dict() for h in TrackingService.get_shipment_tracking_history(db, shipment.id, 10)]
            }
            
        except Exception as e:
            logger.error(f"Error getting tracking status: {str(e)}")
            return None
    
    @classmethod
    def register_tracking_connection(cls, tracking_number: str, connection_id: str):
        """Register a WebSocket connection for a tracking number"""
        if tracking_number not in cls._active_shipments:
            cls._active_shipments[tracking_number] = {"connections": set(), "last_update": None}
        
        cls._active_shipments[tracking_number]["connections"].add(connection_id)
        logger.info(f"✓ Registered connection {connection_id} for tracking {tracking_number}")
    
    @classmethod
    def unregister_tracking_connection(cls, tracking_number: str, connection_id: str):
        """Unregister a WebSocket connection"""
        if tracking_number in cls._active_shipments:
            cls._active_shipments[tracking_number]["connections"].discard(connection_id)
            
            if not cls._active_shipments[tracking_number]["connections"]:
                del cls._active_shipments[tracking_number]
            
            logger.info(f"✓ Unregistered connection {connection_id} for tracking {tracking_number}")
    
    @classmethod
    def get_active_connections(cls, tracking_number: str) -> set:
        """Get all active WebSocket connections for a tracking number"""
        if tracking_number in cls._active_shipments:
            return cls._active_shipments[tracking_number]["connections"]
        return set()
    
    @classmethod
    def has_active_listeners(cls, tracking_number: str) -> bool:
        """Check if there are active listeners for a tracking number"""
        return bool(cls.get_active_connections(tracking_number))
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates in km
        Using Haversine formula
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth radius in km
        
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        return R * c
