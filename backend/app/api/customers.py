"""
Customer Portal API Endpoints
Handles customer profile, addresses, shipments, billing, and support
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from ..db.base import get_db
from ..db.models import User, Customer, Address, Shipment, ShipmentStatus, Invoice, SupportTicket, TrackingHistory
from ..schemas.customer import (
    CustomerResponse, CustomerUpdate,
    AddressCreate, AddressUpdate, AddressResponse,
    CustomerDashboard, SupportTicketCreate, SupportTicketResponse, SupportTicketUpdate,
)
from ..services.pricing import PricingService
from .deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


def get_customer_from_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Customer:
    """Get or automatically create customer record for authenticated user"""
    customer = db.query(Customer).filter(Customer.user_id == current_user.id).first()
    if not customer:
        customer = Customer(
            user_id=current_user.id,
            company_name=current_user.full_name or "Individual",
            account_type="individual",
            phone=current_user.phone,
            email_verified=bool(current_user.is_email_verified),
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    return customer


def _format_shipment_dict(s: Shipment) -> dict:
    return {
        "id": s.id,
        "tracking_number": s.tracking_number,
        "status": str(s.status),
        "service_type": s.service_type,
        "speed": s.speed,
        "pickup_address": f"{s.pickup_address}, {s.pickup_city}, {s.pickup_state}",
        "delivery_address": f"{s.delivery_address}, {s.delivery_city}, {s.delivery_state}",
        "pickup_city": s.pickup_city,
        "delivery_city": s.delivery_city,
        "pickup_location": {
            "address": s.pickup_address,
            "city": s.pickup_city,
            "state": s.pickup_state,
            "zip": s.pickup_zip,
        },
        "delivery_location": {
            "address": s.delivery_address,
            "city": s.delivery_city,
            "state": s.delivery_state,
            "zip": s.delivery_zip,
        },
        "weight": float(s.package_weight or 0.0),
        "quoted_price": float(s.quoted_price or 0.0),
        "actual_cost": float(s.actual_cost) if s.actual_cost is not None else float(s.quoted_price or 0.0),
        "total_price": s.total_price,
        "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
        "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


# ==================== PROFILE ENDPOINTS ====================

@router.get("/profile", response_model=CustomerResponse)
async def get_customer_profile(customer: Customer = Depends(get_customer_from_user)):
    """Get customer profile with addresses and account stats"""
    return customer


@router.put("/profile", response_model=CustomerResponse)
async def update_customer_profile(
    updates: CustomerUpdate,
    customer: Customer = Depends(get_customer_from_user),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update customer profile information"""
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(customer, field) and value is not None:
            setattr(customer, field, value)
    if "phone" in update_data and update_data["phone"]:
        current_user.phone = update_data["phone"]
        db.add(current_user)

    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)
    return customer


# ==================== ADDRESS ENDPOINTS ====================

@router.get("/addresses", response_model=List[AddressResponse])
async def list_customer_addresses(customer: Customer = Depends(get_customer_from_user)):
    """Get all saved addresses for customer"""
    return customer.addresses


@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_customer_address(
    address_data: AddressCreate,
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Create new saved address"""
    if address_data.is_default:
        db.query(Address).filter(
            Address.customer_id == customer.id,
            Address.is_default == True
        ).update({Address.is_default: False})

    new_address = Address(
        customer_id=customer.id,
        **address_data.model_dump()
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address


@router.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_customer_address(
    address_id: int,
    updates: AddressUpdate,
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Update customer address"""
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.customer_id == customer.id
    ).first()
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )

    if updates.is_default:
        db.query(Address).filter(
            Address.customer_id == customer.id,
            Address.id != address_id,
            Address.is_default == True
        ).update({Address.is_default: False})

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(address, field, value)

    address.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(address)
    return address


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer_address(
    address_id: int,
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Delete saved address"""
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.customer_id == customer.id
    ).first()
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found"
        )
    db.delete(address)
    db.commit()


# ==================== DASHBOARD ENDPOINT ====================

@router.get("/dashboard", response_model=CustomerDashboard)
async def get_customer_dashboard(
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive customer dashboard data"""
    shipments = db.query(Shipment).filter(
        Shipment.customer_id == customer.id
    ).order_by(Shipment.created_at.desc()).all()

    recent_shipments = [_format_shipment_dict(s) for s in shipments[:5]]

    month_ago = datetime.utcnow() - timedelta(days=30)
    month_shipments = [s for s in shipments if s.created_at and s.created_at >= month_ago]

    invoices = db.query(Invoice).filter(Invoice.customer_id == customer.id).all()
    pending_invoices = [i for i in invoices if i.status in ("sent", "overdue", "partial")]
    outstanding_balance = sum(float(i.amount_due or 0) - float(i.amount_paid or 0) for i in pending_invoices)

    total_shipments_count = len(shipments)
    total_spent = sum(s.total_price for s in shipments)
    delivered_count = len([s for s in shipments if str(s.status) == "delivered"])
    on_time_rate = round((delivered_count / total_shipments_count) * 100, 1) if total_shipments_count > 0 else 100.0

    customer.total_shipments = total_shipments_count
    customer.total_spent = round(total_spent, 2)
    customer.account_balance = round(outstanding_balance, 2)

    avg_value = (total_spent / total_shipments_count) if total_shipments_count > 0 else 0.0

    return CustomerDashboard(
        customer_info=CustomerResponse.model_validate(customer),
        recent_shipments=recent_shipments,
        pending_invoices=len(pending_invoices),
        outstanding_balance=round(outstanding_balance, 2),
        total_shipments_month=len(month_shipments),
        stats={
            "total_shipments": total_shipments_count,
            "total_spent": round(total_spent, 2),
            "avg_shipment_value": round(avg_value, 2),
            "on_time_rate": on_time_rate,
        }
    )


# ==================== SHIPMENT ENDPOINTS ====================

@router.get("/shipments")
async def list_customer_shipments(
    customer: Customer = Depends(get_customer_from_user),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get customer's shipments with filtering and pagination"""
    query = db.query(Shipment).filter(Shipment.customer_id == customer.id)

    if status_filter:
        query = query.filter(Shipment.status == status_filter)
    if search:
        query = query.filter(Shipment.tracking_number.ilike(f"%{search}%"))

    total = query.count()
    shipments = query.order_by(Shipment.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "shipments": [_format_shipment_dict(s) for s in shipments]
    }


@router.get("/shipments/{tracking_number}")
async def get_shipment_details(
    tracking_number: str,
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Get detailed information for specific shipment"""
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number,
        Shipment.customer_id == customer.id
    ).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )

    history = db.query(TrackingHistory).filter(
        TrackingHistory.shipment_id == shipment.id
    ).order_by(TrackingHistory.created_at.desc()).all()

    data = _format_shipment_dict(shipment)
    data["history"] = [h.to_dict() for h in history]
    return data


@router.post("/shipments", status_code=status.HTTP_201_CREATED)
async def create_customer_shipment(
    shipment_data: dict = Body(...),
    customer: Customer = Depends(get_customer_from_user),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new shipment for customer"""
    service_type = shipment_data.get("service_type", "local")
    speed = shipment_data.get("speed", "standard")
    weight = float(shipment_data.get("package_weight", shipment_data.get("weight", 1.0)))
    package_value = float(shipment_data.get("package_value", 0.0))
    pickup_address = shipment_data.get("pickup_address", "100 King St W")
    delivery_address = shipment_data.get("delivery_address", "200 Bay St")

    distance = PricingService.estimate_distance(pickup_address, delivery_address, service_type)
    quote = PricingService.calculate_quote(
        service_type=service_type,
        distance=distance,
        weight=weight,
        speed=speed,
        package_value=package_value,
    )

    tracking_number = PricingService.generate_tracking_number()
    while db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first():
        tracking_number = PricingService.generate_tracking_number()

    shipment = Shipment(
        customer_id=customer.id,
        tracking_number=tracking_number,
        service_type=service_type,
        speed=speed,
        status=ShipmentStatus.ORDER_RECEIVED.value,
        pickup_contact_name=shipment_data.get("pickup_contact", current_user.full_name or "Sender"),
        pickup_phone=shipment_data.get("pickup_phone", customer.phone or "+1-800-555-0100"),
        pickup_address=pickup_address,
        pickup_city=shipment_data.get("pickup_city", "Toronto"),
        pickup_state=shipment_data.get("pickup_state", "ON"),
        pickup_zip=shipment_data.get("pickup_zip", "M5X 1A9"),
        delivery_contact_name=shipment_data.get("delivery_contact", "Recipient"),
        delivery_phone=shipment_data.get("delivery_phone", "+1-800-555-0199"),
        delivery_email=shipment_data.get("delivery_email", current_user.email),
        delivery_address=delivery_address,
        delivery_city=shipment_data.get("delivery_city", "Toronto"),
        delivery_state=shipment_data.get("delivery_state", "ON"),
        delivery_zip=shipment_data.get("delivery_zip", "M5J 2J2"),
        package_type=shipment_data.get("package_type", "box"),
        package_weight=weight,
        package_value=package_value,
        package_description=shipment_data.get("package_description"),
        special_instructions=shipment_data.get("special_instructions"),
        quoted_price=quote["total_price"],
        actual_cost=quote["total_price"],
        base_fare=quote["base_fare"],
        distance_charge=quote["distance_charge"],
        weight_charge=quote["weight_charge"],
        insurance_amount=quote["insurance_charge"],
        partner_payout=round(quote["total_price"] * 0.70, 2),
        estimated_distance_km=distance,
        estimated_delivery=datetime.utcnow() + timedelta(days=2),
        current_location=shipment_data.get("pickup_city", "Toronto"),
    )
    db.add(shipment)
    db.flush()

    history = TrackingHistory(
        shipment_id=shipment.id,
        tracking_number=tracking_number,
        status=ShipmentStatus.ORDER_RECEIVED.value,
        location=shipment.pickup_city,
        notes="Shipment booked via Customer Portal"
    )
    db.add(history)

    invoice = Invoice(
        customer_id=customer.id,
        shipment_id=shipment.id,
        invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{shipment.id:04d}",
        amount_due=quote["total_price"],
        amount_paid=0.0,
        subtotal=quote["subtotal"],
        tax_amount=0.0,
        status="sent",
        due_date=datetime.utcnow() + timedelta(days=14),
        description=f"Shipment {tracking_number}"
    )
    db.add(invoice)
    db.commit()
    db.refresh(shipment)

    return _format_shipment_dict(shipment)


# ==================== BILLING & INVOICES ENDPOINTS ====================

@router.get("/billing")
async def get_customer_billing(
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Get customer billing information, invoices, and payment methods"""
    invoices = db.query(Invoice).filter(Invoice.customer_id == customer.id).order_by(Invoice.created_at.desc()).all()
    outstanding = sum(float(i.amount_due or 0) - float(i.amount_paid or 0) for i in invoices if i.status != "paid")
    return {
        "account_balance": round(outstanding, 2),
        "total_spent": round(sum(float(i.amount_paid or 0) for i in invoices), 2),
        "payment_methods": [
            {
                "id": 1,
                "method_type": customer.preferred_payment_method or "credit_card",
                "last_four": "4242",
                "is_default": True,
                "is_active": True
            }
        ],
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "amount_due": float(inv.amount_due or 0),
                "amount_paid": float(inv.amount_paid or 0),
                "status": inv.status,
                "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "paid_date": inv.paid_at.isoformat() if inv.paid_at else None,
                "description": inv.description
            }
            for inv in invoices
        ],
        "billing_cycle": "monthly",
        "next_billing_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
    }


@router.get("/invoices")
async def list_customer_invoices(
    customer: Customer = Depends(get_customer_from_user),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get customer's invoices with filtering and pagination"""
    query = db.query(Invoice).filter(Invoice.customer_id == customer.id)

    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    total = query.count()
    invoices = query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "amount_due": float(inv.amount_due or 0),
                "amount_paid": float(inv.amount_paid or 0),
                "status": inv.status,
                "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "paid_date": inv.paid_at.isoformat() if inv.paid_at else None,
                "description": inv.description
            }
            for inv in invoices
        ]
    }


@router.get("/invoices/{invoice_id}")
async def get_invoice_details(
    invoice_id: int,
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Get detailed invoice with line items"""
    inv = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.customer_id == customer.id
    ).first()
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "shipment_id": inv.shipment_id,
        "amount_due": float(inv.amount_due or 0),
        "amount_paid": float(inv.amount_paid or 0),
        "subtotal": float(inv.subtotal or inv.amount_due or 0),
        "tax_amount": float(inv.tax_amount or 0),
        "discount_amount": float(inv.discount_amount or 0),
        "status": inv.status,
        "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "paid_date": inv.paid_at.isoformat() if inv.paid_at else None,
        "description": inv.description,
    }


@router.post("/payments")
async def process_payment(
    payment_data: dict = Body(...),
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Process customer payment for invoice or account balance"""
    invoice_id = payment_data.get("invoice_id")
    amount = float(payment_data.get("amount", 0.0))

    if invoice_id:
        inv = db.query(Invoice).filter(
            Invoice.id == int(invoice_id),
            Invoice.customer_id == customer.id
        ).first()
        if not inv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        pay_amount = amount if amount > 0 else float(inv.amount_due or 0) - float(inv.amount_paid or 0)
        inv.amount_paid = float(inv.amount_paid or 0) + pay_amount
        if inv.amount_paid >= float(inv.amount_due or 0):
            inv.status = "paid"
            inv.paid_at = datetime.utcnow()
        else:
            inv.status = "partial"
        inv.payment_method = payment_data.get("payment_method", "payrail")
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return {
            "success": True,
            "message": "Payment processed successfully",
            "invoice_id": inv.id,
            "status": inv.status,
            "amount_paid": inv.amount_paid
        }

    return {
        "success": True,
        "message": "Payment recorded",
        "amount": amount
    }


# ==================== SUPPORT ENDPOINTS ====================

@router.post("/support-tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
@router.post("/support", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_support_ticket(
    ticket_data: SupportTicketCreate,
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Create new customer support ticket"""
    ticket = SupportTicket(
        customer_id=customer.id,
        shipment_id=ticket_data.related_shipment_id,
        subject=ticket_data.subject,
        description=ticket_data.description,
        category=ticket_data.category or "other",
        priority=ticket_data.priority or "normal",
        status="open"
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return SupportTicketResponse(
        id=ticket.id,
        customer_id=ticket.customer_id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        related_shipment_id=ticket.shipment_id,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolution_notes=ticket.resolution_notes,
    )


@router.get("/support-tickets")
@router.get("/support")
async def list_support_tickets(
    customer: Customer = Depends(get_customer_from_user),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get customer's support tickets"""
    query = db.query(SupportTicket).filter(SupportTicket.customer_id == customer.id)
    if status_filter:
        query = query.filter(SupportTicket.status == status_filter)
    total = query.count()
    tickets = query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "tickets": [
            {
                "id": t.id,
                "customer_id": t.customer_id,
                "subject": t.subject,
                "description": t.description,
                "category": t.category,
                "priority": t.priority,
                "status": t.status,
                "related_shipment_id": t.shipment_id,
                "resolution_notes": t.resolution_notes,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in tickets
        ]
    }


@router.get("/support-tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_support_ticket(
    ticket_id: int,
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Get support ticket details and conversation history"""
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.customer_id == customer.id
    ).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )
    return SupportTicketResponse(
        id=ticket.id,
        customer_id=ticket.customer_id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        related_shipment_id=ticket.shipment_id,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolution_notes=ticket.resolution_notes,
    )


@router.put("/support-tickets/{ticket_id}", response_model=SupportTicketResponse)
async def update_support_ticket(
    ticket_id: int,
    updates: SupportTicketUpdate,
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Update support ticket (close, add reply, etc.)"""
    ticket = db.query(SupportTicket).filter(
        SupportTicket.id == ticket_id,
        SupportTicket.customer_id == customer.id
    ).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )
    if updates.status:
        ticket.status = updates.status
        if updates.status in ("resolved", "closed"):
            ticket.resolved_at = datetime.utcnow()
    if updates.resolution_notes is not None:
        ticket.resolution_notes = updates.resolution_notes
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return SupportTicketResponse(
        id=ticket.id,
        customer_id=ticket.customer_id,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category,
        priority=ticket.priority,
        related_shipment_id=ticket.shipment_id,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolution_notes=ticket.resolution_notes,
    )


# ==================== TRACKING ENDPOINT ====================

@router.get("/tracking/{tracking_number}")
async def get_customer_shipment_tracking(
    tracking_number: str,
    customer: Customer = Depends(get_customer_from_user),
    db: Session = Depends(get_db)
):
    """Get real-time tracking for customer's shipment"""
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number,
        Shipment.customer_id == customer.id
    ).first()
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    history = db.query(TrackingHistory).filter(
        TrackingHistory.shipment_id == shipment.id
    ).order_by(TrackingHistory.created_at.desc()).all()

    return {
        **_format_shipment_dict(shipment),
        "current_location": shipment.current_location or shipment.pickup_city,
        "latitude": shipment.latitude,
        "longitude": shipment.longitude,
        "history": [h.to_dict() for h in history]
    }
