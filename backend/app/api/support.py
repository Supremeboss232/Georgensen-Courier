"""
Support and Contact Ticket Management API
Handles customer support tickets, inquiries, and contact submissions
"""
from fastapi import APIRouter, HTTPException, Depends, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

from app.db.base import get_db
from app.db.models import SupportTicket
from app.services.email import EmailService
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["support"])


class ContactSubmissionRequest(BaseModel):
    """Schema for contact form submissions"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1 (800) 123-4567",
                "company": "Acme Corp",
                "subject": "quote",
                "message": "I need a quote for shipping 100 boxes across Canada"
            }
        }
    )

    name: Optional[str] = Field(default="Visitor", max_length=255)
    email: Optional[EmailStr] = Field(default="visitor@georgensencourier.com")
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=255)
    subject: str = Field(..., min_length=2, max_length=255)
    message: Optional[str] = Field(default=None, max_length=5000)
    description: Optional[str] = Field(default=None, max_length=5000)
    category: Optional[str] = Field(default="other")


class ContactSubmissionResponse(BaseModel):
    """Response after contact submission"""
    ticket_id: str
    status: str
    message: str
    timestamp: datetime


class ContactTicketStatus(BaseModel):
    """Get status of a support ticket"""
    ticket_id: str
    name: str
    email: str
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime
    response: Optional[str] = None


_contact_tickets = {}


def _process_contact_submission(submission: ContactSubmissionRequest, db: Session) -> ContactSubmissionResponse:
    msg_body = submission.message or submission.description or submission.subject
    if len(msg_body.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message must be at least 3 characters"
        )

    ticket_id = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    # Persist in DB SupportTicket table as well
    try:
        db_ticket = SupportTicket(
            customer_id=None,
            subject=f"[{submission.subject}] from {submission.name} ({submission.email})",
            description=msg_body,
            category=submission.category or "other",
            priority="normal",
            status="open"
        )
        db.add(db_ticket)
        db.commit()
    except Exception:
        db.rollback()

    ticket_data = {
        "ticket_id": ticket_id,
        "name": submission.name or "Visitor",
        "email": str(submission.email),
        "phone": submission.phone,
        "company": submission.company,
        "subject": submission.subject,
        "message": msg_body,
        "status": "new",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "response": None
    }
    _contact_tickets[ticket_id] = ticket_data

    return ContactSubmissionResponse(
        ticket_id=ticket_id,
        status="received",
        message=f"Thank you for contacting Georgensen Courier! Your ticket ID is {ticket_id}. We'll respond within 24 business hours.",
        timestamp=datetime.utcnow()
    )


@router.post("/contacts", response_model=ContactSubmissionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/v1/contacts", response_model=ContactSubmissionResponse, status_code=status.HTTP_201_CREATED)
@router.post("/v1/support/tickets", response_model=ContactSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    submission: ContactSubmissionRequest,
    db: Session = Depends(get_db)
):
    """Submit a contact form / public support inquiry"""
    return _process_contact_submission(submission, db)


@router.get("/contacts/{ticket_id}", response_model=ContactTicketStatus)
@router.get("/v1/contacts/{ticket_id}", response_model=ContactTicketStatus)
async def get_ticket_status(ticket_id: str):
    """Get status of a support ticket by ID"""
    if ticket_id not in _contact_tickets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    return ContactTicketStatus(**_contact_tickets[ticket_id])


@router.get("/contacts", tags=["admin"])
@router.get("/v1/contacts", tags=["admin"])
async def list_contact_tickets(
    status_filter: Optional[str] = None,
    subject_filter: Optional[str] = None,
    limit: int = 50
):
    """List all contact submissions"""
    tickets = list(_contact_tickets.values())
    if status_filter:
        tickets = [t for t in tickets if t["status"] == status_filter]
    if subject_filter:
        tickets = [t for t in tickets if t["subject"] == subject_filter]
    tickets.sort(key=lambda x: x["created_at"], reverse=True)
    return {
        "total": len(tickets),
        "limit": limit,
        "tickets": tickets[:limit]
    }


@router.patch("/contacts/{ticket_id}", tags=["admin"])
async def update_contact_ticket(
    ticket_id: str,
    status_update: Optional[str] = None,
    response_text: Optional[str] = None
):
    """Update a support ticket status and add response"""
    if ticket_id not in _contact_tickets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    ticket = _contact_tickets[ticket_id]
    if status_update:
        ticket["status"] = status_update
    if response_text:
        ticket["response"] = response_text
    ticket["updated_at"] = datetime.utcnow()
    return {
        "ticket_id": ticket_id,
        "status": ticket["status"],
        "updated_at": ticket["updated_at"],
        "message": "Ticket updated successfully"
    }
