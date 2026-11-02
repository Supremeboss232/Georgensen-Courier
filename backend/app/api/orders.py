from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.base import get_db
from app.db.models import User, Customer, Shipment, ShipmentStatus, Tracking, TrackingHistory, Invoice
from app.schemas.order import (
    QuoteRequest, QuoteResponse, OrderCreate, OrderResponse,
    OrderDetailResponse, OrderListResponse
)
from app.services.pricing import PricingService
from app.services.assignment import AssignmentService
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


def _resolve_customer_id(db: Session, user: User) -> int:
    """Resolve or create Customer profile for user and return Customer.id"""
    customer = db.query(Customer).filter(Customer.user_id == user.id).first()
    if not customer:
        customer = Customer(
            user_id=user.id,
            company_name=user.full_name or "Individual",
            account_type="individual",
            phone=user.phone,
            email_verified=bool(user.is_email_verified),
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    return customer.id


@router.post("/quote", response_model=QuoteResponse)
async def get_quote(quote_req: QuoteRequest):
    """Calculate instant quote (no authentication required)"""
    svc = quote_req.service_type.value if hasattr(quote_req.service_type, "value") else str(quote_req.service_type)
    spd = quote_req.speed.value if hasattr(quote_req.speed, "value") else str(quote_req.speed)
    quote = PricingService.calculate_quote(
        service_type=svc,
        distance=quote_req.distance,
        weight=quote_req.weight,
        speed=spd,
        package_value=quote_req.package_value
    )
    return QuoteResponse(**quote)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new shipment order"""
    customer_id = _resolve_customer_id(db, current_user)

    svc = order_data.service_type.value if hasattr(order_data.service_type, "value") else str(order_data.service_type)
    spd = order_data.speed.value if hasattr(order_data.speed, "value") else str(order_data.speed)

    estimated_distance = PricingService.estimate_distance(
        order_data.pickup_address,
        order_data.delivery_address,
        svc
    )

    quote = PricingService.calculate_quote(
        service_type=svc,
        distance=estimated_distance,
        weight=order_data.package_weight,
        speed=spd,
        package_value=order_data.package_value
    )

    tracking_number = PricingService.generate_tracking_number()
    while db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first():
        tracking_number = PricingService.generate_tracking_number()

    new_shipment = Shipment(
        tracking_number=tracking_number,
        customer_id=customer_id,
        service_type=svc,
        speed=spd,
        status=ShipmentStatus.ORDER_RECEIVED.value,
        pickup_address=order_data.pickup_address,
        pickup_city=order_data.pickup_city,
        pickup_state=getattr(order_data, "pickup_state", "ON") or "ON",
        pickup_zip=order_data.pickup_zip,
        pickup_contact_name=order_data.pickup_contact,
        pickup_phone=order_data.pickup_phone,
        delivery_address=order_data.delivery_address,
        delivery_city=order_data.delivery_city,
        delivery_state=getattr(order_data, "delivery_state", "ON") or "ON",
        delivery_zip=order_data.delivery_zip,
        delivery_contact_name=order_data.delivery_contact,
        delivery_phone=order_data.delivery_phone,
        delivery_email=str(order_data.delivery_email) if order_data.delivery_email else current_user.email,
        package_type=order_data.package_type or "box",
        package_weight=order_data.package_weight,
        package_value=order_data.package_value,
        package_description=order_data.package_description,
        special_instructions=order_data.special_instructions,
        base_fare=quote["base_fare"],
        distance_charge=quote["distance_charge"],
        weight_charge=quote["weight_charge"],
        insurance_amount=quote["insurance_charge"],
        quoted_price=quote["total_price"],
        actual_cost=quote["total_price"],
        partner_payout=round(quote["total_price"] * 0.70, 2),
        estimated_distance_km=estimated_distance,
        estimated_delivery=datetime.utcnow() + timedelta(days=2),
        current_location=order_data.pickup_city,
        payment_status="pending",
    )

    db.add(new_shipment)
    db.flush()

    tracking_entry = TrackingHistory(
        shipment_id=new_shipment.id,
        tracking_number=tracking_number,
        status=ShipmentStatus.ORDER_RECEIVED.value,
        location=order_data.pickup_city,
        notes="Order created and received"
    )
    db.add(tracking_entry)

    # Create corresponding Invoice
    inv_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{new_shipment.id:04d}"
    invoice = Invoice(
        customer_id=customer_id,
        shipment_id=new_shipment.id,
        invoice_number=inv_number,
        amount_due=quote["total_price"],
        amount_paid=0.0,
        subtotal=quote["subtotal"],
        tax_amount=0.0,
        status="sent",
        due_date=datetime.utcnow() + timedelta(days=14),
        description=f"Shipping charge for {tracking_number}"
    )
    db.add(invoice)

    db.commit()
    db.refresh(new_shipment)

    try:
        AssignmentService.auto_assign_shipment(db, new_shipment.id)
        db.refresh(new_shipment)
    except Exception:
        pass

    return OrderResponse.model_validate(new_shipment)


@router.get("", response_model=List[OrderListResponse])
async def list_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List shipments for current customer (or all shipments if admin)"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    query = db.query(Shipment)

    if role_val not in ("admin", "system_admin") and not current_user.is_superuser:
        customer_id = _resolve_customer_id(db, current_user)
        query = query.filter(Shipment.customer_id == customer_id)

    if status_filter:
        query = query.filter(Shipment.status == status_filter)

    shipments = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()
    return [OrderListResponse.model_validate(s) for s in shipments]


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed shipment information with ownership check"""
    shipment = db.query(Shipment).filter(Shipment.id == order_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val not in ("admin", "system_admin") and not current_user.is_superuser:
        customer_id = _resolve_customer_id(db, current_user)
        if shipment.customer_id != customer_id and shipment.assigned_partner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    return OrderDetailResponse.model_validate(shipment)


@router.put("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel shipment (only if not yet picked up or in transit)"""
    shipment = db.query(Shipment).filter(Shipment.id == order_id).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val not in ("admin", "system_admin") and not current_user.is_superuser:
        customer_id = _resolve_customer_id(db, current_user)
        if shipment.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only order owner can cancel"
            )

    if str(shipment.status) not in (
        ShipmentStatus.ORDER_RECEIVED.value,
        ShipmentStatus.PROCESSING.value,
        "pending",
        "confirmed"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in {shipment.status} status"
        )

    shipment.status = ShipmentStatus.CANCELLED.value

    tracking = TrackingHistory(
        shipment_id=shipment.id,
        tracking_number=shipment.tracking_number,
        status=ShipmentStatus.CANCELLED.value,
        notes="Order cancelled by customer"
    )

    db.add(shipment)
    db.add(tracking)
    db.commit()

    return {"message": "Order cancelled successfully", "order_id": str(order_id)}
