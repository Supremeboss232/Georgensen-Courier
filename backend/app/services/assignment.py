from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from app.db.models import User, Shipment, ShipmentStatus
from datetime import datetime


class AssignmentService:
    """Service for assigning shipments to delivery partners"""
    
    @staticmethod
    def assign_shipment_to_partner(
        db: Session,
        shipment_id: int,
        partner_id: int
    ) -> Optional[Shipment]:
        """Assign shipment to delivery partner"""
        
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return None
        
        partner = db.query(User).filter(User.id == partner_id).first()
        if not partner or partner.role != "partner":
            return None
        
        # Update shipment assignment
        shipment.partner_id = partner_id
        shipment.status = ShipmentStatus.PROCESSING
        
        db.add(shipment)
        db.commit()
        db.refresh(shipment)
        
        return shipment
    
    @staticmethod
    def find_available_partners(
        db: Session,
        service_type: str,
        location_city: str
    ) -> list:
        """Find available partners for assignment"""
        
        # Get partners with status active
        partners = db.query(User).filter(
            User.role == "partner",
            User.is_active == True
        ).all()
        
        # Filter by service type and location if profile_data exists
        available = []
        for partner in partners:
            # Check pending shipments count (simple availability check)
            pending_shipments = db.query(Shipment).filter(
                Shipment.partner_id == partner.id,
                Shipment.status.in_([
                    ShipmentStatus.PROCESSING,
                    ShipmentStatus.PICKED_UP,
                    ShipmentStatus.IN_TRANSIT
                ])
            ).count()
            
            # Allow assignment if less than 5 active shipments
            if pending_shipments < 5:
                available.append({
                    "id": partner.id,
                    "name": partner.full_name,
                    "active_shipments": pending_shipments,
                    "rating": partner.profile_data.get("rating", 4.5) if partner.profile_data else 4.5
                })
        
        # Sort by active shipments (least busy first) then rating (highest first)
        available.sort(key=lambda x: (x["active_shipments"], -x["rating"]))
        
        return available
    
    @staticmethod
    def auto_assign_shipment(db: Session, shipment_id: int) -> Optional[Shipment]:
        """Automatically assign shipment to most suitable partner"""
        
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment or shipment.partner_id:
            return None
        
        # Find available partners
        available_partners = AssignmentService.find_available_partners(
            db,
            shipment.service_type,
            shipment.pickup_city
        )
        
        if not available_partners:
            return None
        
        # Assign to best available partner
        best_partner_id = available_partners[0]["id"]
        return AssignmentService.assign_shipment_to_partner(db, shipment_id, best_partner_id)
