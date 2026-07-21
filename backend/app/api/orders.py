from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.models import User, Shipment
from app.db.models.shipment import ShipmentStatus
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderDetailResponse,
    OrderListResponse, QuoteRequest, QuoteResponse,
    TrackingHistoryResponse, ShipmentResponse
)
from app.services.pricing import PricingService
from app.services.assignment import AssignmentService
from app.services.notifications import NotificationService
from app.api.deps import get_current_user, get_current_customer
from datetime import datetime, timedelta


router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"]
)


@router.post("/quote", response_model=QuoteResponse)
async def get_quote(
    quote_request: QuoteRequest,
    db: Session = Depends(get_db)
):
    """Get shipping quote"""
    
    pricing = PricingService.calculate_quote(
        service_type=quote_request.service_type.value,
        distance=quote_request.distance,
        weight=quote_request.weight,
        speed=quote_request.speed.value,
        package_value=quote_request.package_value
    )
    
    return pricing


@router.post("/", response_model=OrderDetailResponse)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Create new delivery order"""
    
    # Calculate distance between pickup and delivery (simple estimation)
    distance = PricingService.estimate_distance(
        order_data.pickup_address,
        order_data.delivery_address,
        order_data.service_type.value
    )
    
    # Get pricing
    pricing = PricingService.calculate_quote(
        service_type=order_data.service_type.value,
        distance=distance,
        weight=order_data.package_weight,
        speed=order_data.speed.value,
        package_value=order_data.package_value
    )
    
    # Generate tracking number
    tracking_number = PricingService.generate_tracking_number()
    
    # Create shipment
    shipment = Shipment(
        customer_id=current_user.id,
        tracking_number=tracking_number,
        service_type=order_data.service_type.value,
        speed=order_data.speed.value,
        pickup_contact_name=order_data.pickup_contact,
        pickup_phone=order_data.pickup_phone,
        pickup_address=order_data.pickup_address,
        pickup_city=order_data.pickup_city or "Local",
        pickup_state="NY",  # Extract from address or make optional
        pickup_zip=order_data.pickup_zip,
        delivery_contact_name=order_data.delivery_contact,
        delivery_phone=order_data.delivery_phone,
        delivery_email=order_data.delivery_email,
        delivery_address=order_data.delivery_address,
        delivery_city=order_data.delivery_city or "Local",
        delivery_state="NY",  # Extract from address or make optional
        delivery_zip=order_data.delivery_zip,
        package_type=order_data.package_type or "standard",
        package_weight=order_data.package_weight,
        package_value=order_data.package_value,
        package_description=order_data.package_description,
        quoted_price=pricing["total_price"],
        insurance_amount=pricing["insurance_charge"],
        special_instructions=order_data.special_instructions,
        status=ShipmentStatus.ORDER_RECEIVED
    )
    
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    
    # Send confirmation email
    NotificationService.send_order_confirmation_email(
        current_user.email,
        current_user.full_name,
        tracking_number,
        pricing["total_price"]
    )
    
    # Try auto-assign partner
    AssignmentService.assign_shipment_to_partner(db, shipment.id, None)
    
    return shipment


@router.get("/", response_model=list[OrderListResponse])
async def list_orders(
    current_user: User = Depends(get_current_user),
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """List shipments (filtered by user role)"""
    
    query = db.query(Shipment)
    
    # Filter by user role
    if current_user.role == "customer":
        query = query.filter(Shipment.customer_id == current_user.id)
    elif current_user.role == "partner":
        query = query.filter(Shipment.assigned_partner_id == current_user.id)
    
    # Filter by status if provided
    if status:
        query = query.filter(Shipment.status == status)
    
    shipments = query.offset(skip).limit(limit).all()
    return shipments


@router.get("/{shipment_id}", response_model=OrderDetailResponse)
async def get_shipment(
    shipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get shipment details"""
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    # Check authorization
    if current_user.role == "customer" and shipment.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this shipment"
        )
    elif current_user.role == "partner" and shipment.assigned_partner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this shipment"
        )
    
    return shipment


@router.patch("/{shipment_id}/status")
async def update_shipment_status(
    shipment_id: int,
    status_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update shipment status"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check authorization (partner or admin)
    if current_user.role not in ["admin", "partner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    new_status = status_data.get("status")
    if new_status:
        order.status = OrderStatusEnum[new_status.upper()]
        
        # Update shipment status too
        shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
        if shipment:
            shipment.current_status = new_status
        
        db.commit()
        db.refresh(order)
    
    return {"order_id": order_id, "status": new_status}


@router.get("/{order_id}/shipment", response_model=ShipmentResponse)
async def get_shipment(
    order_id: UUID,
    db: Session = Depends(get_db)
):
    """Get shipment tracking information"""
    
    shipment = db.query(Shipment).filter(Shipment.order_id == order_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    return shipment


@router.get("/{tracking_number}/track")
async def track_by_number(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """Track order by tracking number (public)"""
    
    order = db.query(Order).filter(Order.tracking_number == tracking_number).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    shipment = db.query(Shipment).filter(Shipment.order_id == order.id).first()
    
    return {
        "tracking_number": tracking_number,
        "status": order.status,
        "current_location": shipment.current_location if shipment else "Unknown",
        "pickup_address": order.pickup_address,
        "delivery_address": order.delivery_address,
        "created_at": order.created_at,
        "updated_at": order.updated_at
    }


# ==================== GLOBAL DELIVERY TRACKING ====================

@router.get("/{shipment_id}/global-milestones")
async def get_global_milestones(
    shipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dynamic milestones for shipment based on type and region"""
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Determine shipment type
    shipment_type = shipment.service_type
    is_international = shipment.origin_country != shipment.destination_country
    
    # Define milestone flows by type
    milestone_flows = {
        "local": [
            {"step": 1, "name": "Pickup Ready", "icon": "📦"},
            {"step": 2, "name": "At Pickup", "icon": "🚗"},
            {"step": 3, "name": "In Transit", "icon": "🛣️"},
            {"step": 4, "name": "Delivery Ready", "icon": "🚪"},
            {"step": 5, "name": "Delivered", "icon": "✅"}
        ],
        "international": [
            {"step": 1, "name": "Pickup Ready", "icon": "📦"},
            {"step": 2, "name": "At Origin Hub", "icon": "🏢"},
            {"step": 3, "name": "At Export Hub", "icon": "📍"},
            {"step": 4, "name": "Customs Clearing", "icon": "🛂"},
            {"step": 5, "name": "At Destination Hub", "icon": "🏬"},
            {"step": 6, "name": "Delivery Ready", "icon": "🚪"},
            {"step": 7, "name": "Delivered", "icon": "✅"}
        ],
        "air": [
            {"step": 1, "name": "Pickup Ready", "icon": "📦"},
            {"step": 2, "name": "Awaiting Air Transport", "icon": "✈️"},
            {"step": 3, "name": "In Air", "icon": "☁️"},
            {"step": 4, "name": "Landed", "icon": "🛬"},
            {"step": 5, "name": "Customs Clearing", "icon": "🛂"},
            {"step": 6, "name": "Delivery Ready", "icon": "🚪"},
            {"step": 7, "name": "Delivered", "icon": "✅"}
        ],
        "sea": [
            {"step": 1, "name": "Pickup Ready", "icon": "📦"},
            {"step": 2, "name": "At Port", "icon": "⚓"},
            {"step": 3, "name": "Port Processing", "icon": "📋"},
            {"step": 4, "name": "In Transit (Sea)", "icon": "🌊"},
            {"step": 5, "name": "Port of Destination", "icon": "🏖️"},
            {"step": 6, "name": "Customs Clearing", "icon": "🛂"},
            {"step": 7, "name": "Delivery Ready", "icon": "🚪"},
            {"step": 8, "name": "Delivered", "icon": "✅"}
        ]
    }
    
    # Choose milestone flow based on shipment characteristics
    if shipment_type == "sea":
        milestones = milestone_flows["sea"]
    elif shipment_type == "air":
        milestones = milestone_flows["air"]
    elif is_international:
        milestones = milestone_flows["international"]
    else:
        milestones = milestone_flows["local"]
    
    return {
        "shipment_id": shipment_id,
        "shipment_type": shipment_type,
        "is_international": is_international,
        "current_status": shipment.status,
        "milestones": milestones
    }


@router.get("/{shipment_id}/compliance-info")
async def get_compliance_info(
    shipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get compliance and regulatory requirements for shipment"""
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    is_international = shipment.origin_country != shipment.destination_country
    
    # Determine compliance requirements
    requires_vat = shipment.destination_country in ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH"]
    requires_customs = is_international and shipment.package_value > 150
    requires_bol = shipment.service_type == "sea" or (is_international and shipment.package_weight > 100)
    
    compliance_badges = []
    if requires_vat:
        compliance_badges.append({"type": "vat", "label": "VAT Filing Required", "region": "EU"})
    if requires_customs:
        compliance_badges.append({"type": "customs", "label": "Customs Documentation Required", "region": "International"})
    if requires_bol:
        compliance_badges.append({"type": "bol", "label": "Bill of Lading Required", "region": "Shipping"})
    
    return {
        "shipment_id": shipment_id,
        "is_international": is_international,
        "requires_vat": requires_vat,
        "requires_customs": requires_customs,
        "requires_bol": requires_bol,
        "compliance_badges": compliance_badges,
        "documents_available": {
            "commercial_invoice": is_international,
            "bill_of_lading": requires_bol,
            "customs_declaration": requires_customs,
            "certificate_of_origin": is_international and shipment.package_value > 500
        }
    }


@router.get("/{shipment_id}/regional-contact")
async def get_regional_contact(
    shipment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get regional contact info for a shipment"""
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Region contact information
    region_contacts = {
        "NA": {
            "region": "North America",
            "name": "North America Support Hub",
            "phone": "+1-888-DELIVER",
            "email": "support-na@georgensen.com",
            "timezone": "America/Toronto",
            "customs_agent": "NA Customs Broker"
        },
        "EU": {
            "region": "Europe",
            "name": "European Operations Center",
            "phone": "+44-20-7946-0522",
            "email": "support-eu@georgensen.com",
            "timezone": "Europe/London",
            "customs_agent": "EMEA Customs Service"
        },
        "APAC": {
            "region": "Asia-Pacific",
            "name": "Singapore Regional Hub",
            "phone": "+65-6732-9700",
            "email": "support-apac@georgensen.com",
            "timezone": "Asia/Singapore",
            "customs_agent": "APAC Customs Team"
        },
        "LATAM": {
            "region": "Latin America",
            "name": "LATAM Operations Center",
            "phone": "+55-11-3555-8000",
            "email": "support-latam@georgensen.com",
            "timezone": "America/Sao_Paulo",
            "customs_agent": "LATAM Aduanas"
        },
        "MEA": {
            "region": "Middle East & Africa",
            "name": "Dubai Operations Hub",
            "phone": "+971-4-308-8888",
            "email": "support-mea@georgensen.com",
            "timezone": "Asia/Dubai",
            "customs_agent": "MEA Customs Broker"
        }
    }
    
    # Determine region code from destination
    dest_country = shipment.destination_country
    region_mapping = {
        "CA": "NA", "US": "NA",
        "GB": "EU", "DE": "EU", "FR": "EU", "IT": "EU", "ES": "EU", "NL": "EU", "BE": "EU", "AT": "EU", "CH": "EU",
        "AU": "APAC", "SG": "APAC", "JP": "APAC", "NZ": "APAC", "HK": "APAC",
        "MX": "LATAM", "BR": "LATAM", "AR": "LATAM", "CL": "LATAM",
        "AE": "MEA", "SA": "MEA", "ZA": "MEA"
    }
    
    region_code = region_mapping.get(dest_country, "NA")
    contact = region_contacts.get(region_code, region_contacts["NA"])
    
    return {
        "shipment_id": shipment_id,
        "destination_region": region_code,
        "contact": contact
    }


@router.get("/{shipment_id}/documents/{doc_type}")
async def download_document(
    shipment_id: int,
    doc_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download regulatory documents (invoice, BOL, customs declaration)"""
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Validate document type
    valid_types = ["invoice", "bol", "customs", "certificate"]
    if doc_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    # In production, generate or fetch document from storage
    document_metadata = {
        "shipment_id": shipment_id,
        "document_type": doc_type,
        "tracking_number": shipment.tracking_number,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    return {
        "status": "document_ready",
        "download_url": f"/api/v1/documents/{shipment_id}/{doc_type}/download",
        "metadata": document_metadata
    }


@router.patch("/{shipment_id}/status")
async def update_delivery_status(
    shipment_id: int,
    status_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update delivery status with validation"""
    
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Verify partner authorization
    if current_user.role == "partner" and shipment.assigned_partner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    new_status = status_data.get("status", "next")
    
    # Status progression mapping
    status_hierarchy = [
        "pickup_ready", "at_pickup", "at_origin_hub", "at_export_hub",
        "customs_clearing", "at_destination_hub", "delivery_ready",
        "in_transit", "in_air", "landed", "at_port", "port_processing",
        "in_transit_sea", "port_destination", "delivered"
    ]
    
    if new_status == "next":
        # Move to next logical step
        try:
            current_idx = status_hierarchy.index(shipment.status)
            if current_idx < len(status_hierarchy) - 1:
                shipment.status = status_hierarchy[current_idx + 1]
        except ValueError:
            shipment.status = "in_transit"
    else:
        shipment.status = new_status
    
    shipment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(shipment)
    
    # Send notification
    NotificationService.send_status_update_notification(
        shipment.customer_id,
        shipment.tracking_number,
        shipment.status
    )
    
    return {
        "shipment_id": shipment_id,
        "tracking_number": shipment.tracking_number,
        "new_status": shipment.status,
        "updated_at": shipment.updated_at
    }
