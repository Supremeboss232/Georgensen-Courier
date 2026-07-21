"""
Customer API routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.permissions import require_role, require_permission, Role, Permission
from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.db.models.customer import Customer
from app.db.models.address import Address
from app.schemas.customer import (
    CustomerResponse,
    CustomerDashboard,
    AddressResponse,
    AddressCreate,
    AddressUpdate,
    SupportTicketResponse,
    SupportTicketCreate,
    SupportTicketUpdate,
    PaymentMethodResponse,
    InvoiceResponse,
    ShipmentResponse,
)

router = APIRouter(
    prefix="/customer",
    tags=["customer"],
    dependencies=[Depends(get_current_user)]
)


async def get_customer_from_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Customer:
    """Get customer object from authenticated user"""
    customer = db.query(Customer).filter(Customer.user_id == current_user.id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )
    return customer


@router.get("/profile", response_model=CustomerResponse)
async def get_customer_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current customer's profile"""
    customer = await get_customer_from_user(current_user, db)
    return customer


@router.put("/profile", response_model=CustomerResponse)
async def update_customer_profile(
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update customer profile"""
    customer = await get_customer_from_user(current_user, db)
    
    # Allow updates to specific fields
    allowed_fields = ["company_name", "phone", "email_notifications", "sms_notifications"]
    for field, value in update_data.items():
        if field in allowed_fields and value is not None:
            setattr(customer, field, value)
    
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/dashboard", response_model=CustomerDashboard)
async def get_customer_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer dashboard with stats and recent orders"""
    customer = await get_customer_from_user(current_user, db)
    
    # TODO: Fetch recent shipments from orders
    # TODO: Fetch pending invoices
    # TODO: Calculate statistics
    
    dashboard = CustomerDashboard(
        customer_info=customer,
        recent_shipments=[],
        pending_invoices=0,
        outstanding_balance=0.0,
        stats={
            "total_shipments": customer.total_shipments,
            "total_spent": customer.total_spent,
            "avg_shipment_value": customer.total_spent / max(customer.total_shipments, 1),
            "on_time_rate": 0.95
        }
    )
    return dashboard


# Address management
@router.get("/addresses", response_model=List[AddressResponse])
async def list_customer_addresses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all saved addresses for customer"""
    customer = await get_customer_from_user(current_user, db)
    addresses = db.query(Address).filter(Address.customer_id == customer.id).all()
    return addresses


@router.post("/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    address_data: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new saved address"""
    customer = await get_customer_from_user(current_user, db)
    
    # If this is default, unset other defaults
    if address_data.is_default:
        db.query(Address).filter(
            Address.customer_id == customer.id,
            Address.is_default == True
        ).update({"is_default": False})
    
    new_address = Address(
        customer_id=customer.id,
        **address_data.dict()
    )
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address


@router.get("/addresses/{address_id}", response_model=AddressResponse)
async def get_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific address"""
    customer = await get_customer_from_user(current_user, db)
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.customer_id == customer.id
    ).first()
    
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return address


@router.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: int,
    address_data: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update address"""
    customer = await get_customer_from_user(current_user, db)
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.customer_id == customer.id
    ).first()
    
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    if address_data.is_default:
        db.query(Address).filter(
            Address.customer_id == customer.id,
            Address.is_default == True
        ).update({"is_default": False})
    
    update_dict = address_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(address, field, value)
    
    db.commit()
    db.refresh(address)
    return address


@router.delete("/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete address"""
    customer = await get_customer_from_user(current_user, db)
    address = db.query(Address).filter(
        Address.id == address_id,
        Address.customer_id == customer.id
    ).first()
    
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    db.delete(address)
    db.commit()


# Shipment management (stub routes - will be implemented in orders.py)
@router.get("/shipments", response_model=List[ShipmentResponse])
async def list_customer_shipments(
    status: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List customer's shipments"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement shipment query
    return []


@router.get("/shipments/{tracking_number}", response_model=ShipmentResponse)
async def get_shipment(
    tracking_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get shipment by tracking number"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement shipment lookup
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/shipments", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    shipment_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new shipment"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement shipment creation
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


# Billing and invoices
@router.get("/billing")
async def get_billing_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing summary for customer"""
    customer = await get_customer_from_user(current_user, db)
    return {
        "account_balance": customer.account_balance,
        "total_spent": customer.total_spent,
        "pending_invoices": 0,  # TODO: Count actual pending
        "outstanding_balance": 0.0  # TODO: Calculate actual
    }


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    status: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List customer's invoices"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement invoice query
    return []


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific invoice"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement invoice lookup with customer verification
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/payments")
async def process_payment(
    payment_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process payment for invoices"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement payment processing
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


# Support tickets
@router.get("/support-tickets", response_model=List[SupportTicketResponse])
async def list_support_tickets(
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List customer's support tickets"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement ticket query
    return []


@router.post("/support-tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_support_ticket(
    ticket_data: SupportTicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new support ticket"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement ticket creation
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/support-tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_support_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific support ticket"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement ticket lookup
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.put("/support-tickets/{ticket_id}", response_model=SupportTicketResponse)
async def update_support_ticket(
    ticket_id: int,
    update_data: SupportTicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update support ticket"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement ticket update
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# Tracking
@router.get("/tracking/{tracking_number}")
async def track_shipment(
    tracking_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time tracking information"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement tracking lookup
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/tracking/{tracking_number}/events")
async def get_tracking_events(
    tracking_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tracking timeline events"""
    customer = await get_customer_from_user(current_user, db)
    # TODO: Implement event query
    return []
