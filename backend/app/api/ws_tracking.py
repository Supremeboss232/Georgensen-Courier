"""
WebSocket endpoints for real-time tracking
Enables live GPS updates and shipment status monitoring
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.models import Shipment, User
from app.api.deps import get_current_user
from app.services.tracking import TrackingService
import json
import logging
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/tracking",
    tags=["Tracking - Real-time"]
)


class ConnectionManager:
    """Manage WebSocket connections for tracking"""
    
    def __init__(self):
        # tracking_number -> list of (connection, user_id, connection_id)
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, tracking_number: str, user_id: int):
        """Register a new WebSocket connection for tracking"""
        await websocket.accept()
        connection_id = str(uuid4())
        
        if tracking_number not in self.active_connections:
            self.active_connections[tracking_number] = []
        
        self.active_connections[tracking_number].append({
            "ws": websocket,
            "user_id": user_id,
            "connection_id": connection_id,
            "connected_at": datetime.utcnow()
        })
        
        logger.info(f"✓ Client connected to tracking {tracking_number}: {connection_id}")
        return connection_id
    
    async def disconnect(self, tracking_number: str, connection_id: str):
        """Remove a disconnected WebSocket"""
        if tracking_number in self.active_connections:
            self.active_connections[tracking_number] = [
                conn for conn in self.active_connections[tracking_number]
                if conn["connection_id"] != connection_id
            ]
            
            if not self.active_connections[tracking_number]:
                del self.active_connections[tracking_number]
            
            logger.info(f"✓ Client disconnected from tracking {tracking_number}: {connection_id}")
    
    async def broadcast(self, tracking_number: str, message: dict):
        """Send a message to all connected clients for a tracking number"""
        if tracking_number not in self.active_connections:
            return
        
        message["timestamp"] = datetime.utcnow().isoformat()
        
        # Track failed connections to remove them
        failed = []
        
        for conn in self.active_connections.get(tracking_number, []):
            try:
                await conn["ws"].send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {conn['connection_id']}: {str(e)}")
                failed.append(conn["connection_id"])
        
        # Remove failed connections
        for connection_id in failed:
            await self.disconnect(tracking_number, connection_id)
    
    def get_active_count(self, tracking_number: str) -> int:
        """Get number of active listeners for a tracking"""
        return len(self.active_connections.get(tracking_number, []))


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/{tracking_number}")
async def websocket_tracking(
    websocket: WebSocket,
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time shipment tracking
    
    Usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/tracking/ws/GEO-26-ABC123');
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log(`Shipment at ${data.location}: ${data.latitude}, ${data.longitude}`);
    };
    ```
    """
    
    # PUBLIC endpoint - no authentication required
    # In production, add authentication token check if desired
    
    connection_id = await manager.connect(websocket, tracking_number, user_id=None)
    
    # Verify tracking number exists
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number
    ).first()
    
    if not shipment:
        await websocket.send_json({
            "error": "Tracking number not found",
            "tracking_number": tracking_number
        })
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        # Send initial status
        tracking_status = TrackingService.get_tracking_status(db, tracking_number)
        if tracking_status:
            await websocket.send_json({
                "event": "connected",
                "status": tracking_status,
                "message": f"Connected to tracking for {tracking_number}. You will receive live updates."
            })
        
        # Keep connection open and listen for messages
        while True:
            data = await websocket.receive_text()
            
            # Clients can optionally send heartbeat or other messages
            # For now, we just keep the connection alive
            logger.debug(f"Received message from {connection_id}: {data}")
    
    except WebSocketDisconnect:
        await manager.disconnect(tracking_number, connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {tracking_number}: {str(e)}")
        await manager.disconnect(tracking_number, connection_id)


@router.post("/{tracking_number}/update")
async def update_tracking(
    tracking_number: str,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update shipment tracking (called by partner app)
    
    Only partners can update tracking
    
    Request body:
    ```json
    {
        "status": "in_transit",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "location": "Manhattan, NYC",
        "notes": "On the way to delivery address"
    }
    ```
    """
    
    # Verify user is a partner
    if current_user.role != "partner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only partners can update tracking"
        )
    
    # Find shipment
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number
    ).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    # Verify partner is assigned to this shipment
    if shipment.assigned_partner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this shipment"
        )
    
    try:
        # Record the update
        history = TrackingService.record_tracking_update(
            db=db,
            shipment_id=shipment.id,
            tracking_number=tracking_number,
            status=update_data.get("status"),
            latitude=float(update_data.get("latitude", 0)),
            longitude=float(update_data.get("longitude", 0)),
            location=update_data.get("location"),
            notes=update_data.get("notes"),
            partner_id=current_user.id,
            distance_traveled=update_data.get("distance_traveled")
        )
        
        # Broadcast to all connected clients
        broadcast_message = {
            "event": "location_update",
            "tracking_number": tracking_number,
            "status": update_data.get("status"),
            "latitude": float(update_data.get("latitude", 0)),
            "longitude": float(update_data.get("longitude", 0)),
            "location": update_data.get("location"),
            "notes": update_data.get("notes"),
            "active_listeners": manager.get_active_count(tracking_number)
        }
        
        await manager.broadcast(tracking_number, broadcast_message)
        
        return {
            "success": True,
            "message": f"Tracking updated and broadcasted to {manager.get_active_count(tracking_number)} listeners",
            "tracking_update": history.to_dict()
        }
    
    except Exception as e:
        logger.error(f"Error updating tracking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tracking: {str(e)}"
        )


@router.get("/{tracking_number}")
async def get_tracking_public(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """
    Get current tracking status (public endpoint, no auth required)
    
    Returns current status, location, and last 10 updates
    """
    tracking_status = TrackingService.get_tracking_status(db, tracking_number)
    
    if not tracking_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking number not found"
        )
    
    return {
        **tracking_status,
        "active_listeners": manager.get_active_count(tracking_number)
    }


@router.get("/{tracking_number}/history")
async def get_tracking_history(
    tracking_number: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get full tracking history for a shipment (public endpoint)
    
    Returns list of all tracking updates in reverse chronological order
    """
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number
    ).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tracking number not found"
        )
    
    history = TrackingService.get_shipment_tracking_history(db, shipment.id, limit)
    
    return {
        "tracking_number": tracking_number,
        "total_updates": len(history),
        "updates": [h.to_dict() for h in history]
    }
