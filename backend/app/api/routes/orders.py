from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.base import get_db
from app.db.models import User, Shipment, ShipmentStatus
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderDetailResponse,
    OrderListResponse, QuoteRequest, QuoteResponse,
    TrackingHistoryResponse, ShipmentResponse
)
from app.services.pricing import PricingService
from app.services.assignment import AssignmentService
from app.services.notifications import NotificationService
from app.api.deps import get_current_user, get_current_customer
from datetime import datetime


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
    
    # Get pricing
    pricing = PricingService.calculate_quote(
        service_type=order_data.service_type.value,
        distance=10,  # Default or get from address calculation
        weight=order_data.package_weight,
        speed=order_data.speed.value,
        package_value=order_data.package_value
    )
    
    # Generate tracking number
    tracking_number = PricingService.generate_tracking_number()
    
    # Create order
    order = Order(
        customer_id=current_user.id,
        tracking_number=tracking_number,
        service_type=order_data.service_type.value,
        speed=order_data.speed.value,
        pickup_address=order_data.pickup_address,
        pickup_city=order_data.pickup_address.split(",")[-1].strip() if "," in order_data.pickup_address else "Unknown",
        pickup_zip="0000",
        pickup_contact=order_data.pickup_contact,
        delivery_address=order_data.delivery_address,
        delivery_city=order_data.delivery_address.split(",")[-1].strip() if "," in order_data.delivery_address else "Unknown",
        delivery_zip="0000",
        delivery_contact=order_data.delivery_contact,
        delivery_email=order_data.delivery_email,
        package_type="standard",
        package_weight=order_data.package_weight,
        package_value=order_data.package_value,
        base_fare=pricing["base_fare"],
        distance_charge=pricing["distance_charge"],
        weight_charge=pricing["weight_charge"],
        speed_multiplier=pricing["speed_multiplier"],
        insurance_charge=pricing["insurance_charge"],
        total_price=pricing["total_price"],
        status=OrderStatusEnum.PENDING,
        payment_status=PaymentStatusEnum.PENDING
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Create initial shipment record
    shipment = Shipment(
        order_id=order.id,
        tracking_number=tracking_number,
        current_status=OrderStatusEnum.PENDING
    )
    db.add(shipment)
    db.commit()
    
    # Send confirmation email
    NotificationService.send_order_confirmation_email(
        current_user.email,
        current_user.full_name,
        tracking_number,
        pricing["total_price"]
    )
    
    # Try auto-assign partner
    AssignmentService.auto_assign_order(db, order.id)
    
    return order


@router.get("/", response_model=list[OrderListResponse])
async def list_orders(
    current_user: User = Depends(get_current_user),
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """List orders (filtered by user role)"""
    
    query = db.query(Order)
    
    # Filter by user role
    if current_user.role == "customer":
        query = query.filter(Order.customer_id == current_user.id)
    elif current_user.role == "partner":
        query = query.filter(Order.assigned_partner_id == current_user.id)
    
    # Filter by status if provided
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get order details"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check authorization
    if current_user.role == "customer" and order.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    elif current_user.role == "partner" and order.assigned_partner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    return order


@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: UUID,
    status_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update order status"""
    
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
