"""
Support & Contact API Router
Handles public contact form submissions, support routing, and inquiry management for Georgensen Courier
Supports department-specific routing (customs, freight, claims, etc.)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import logging
from app.core.config import settings
from app.services.email_service import EmailService

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Support & Contact"])


# ==============================
# Schemas
# ==============================

class ContactFormRequest(BaseModel):
    """Public contact form submission"""
    name: str = Field(..., min_length=2, max_length=100, description="Customer name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number (optional)")
    company: Optional[str] = Field(None, max_length=100, description="Company name (optional)")
    subject: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Contact subject/department"
    )
    message: str = Field(..., min_length=10, max_length=5000, description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Submission timestamp")

    @validator('subject')
    def validate_subject(cls, v):
        """Validate subject is a recognized department"""
        valid_subjects = {
            'general',
            'customs_clearance',
            'international_freight',
            'quote',
            'tracking',
            'claims_insurance',
            'partnership',
            'feedback',
            'complaint'
        }
        if v.lower() not in valid_subjects:
            raise ValueError(f'Invalid subject. Must be one of: {", ".join(valid_subjects)}')
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "name": "Jane Smith",
                "email": "jane@company.com",
                "phone": "+1-416-555-1234",
                "company": "Acme Inc.",
                "subject": "customs_clearance",
                "message": "I have a question about CBSA clearance procedures for my international shipment.",
                "timestamp": "2026-04-17T14:30:00Z"
            }
        }


class ContactFormResponse(BaseModel):
    """Response to contact form submission"""
    success: bool = Field(..., description="Whether submission was successful")
    message: str = Field(..., description="Response message")
    ticket_id: Optional[str] = Field(None, description="Support ticket ID for tracking")
    estimated_response_time: Optional[str] = Field(None, description="Estimated response time")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Thank you! Your message has been received. We'll respond within 2-4 hours.",
                "ticket_id": "TKT-2026-04-17-001",
                "estimated_response_time": "2-4 hours during business hours"
            }
        }


# ==============================
# API Endpoints
# ==============================

@router.post(
    "/contacts",
    response_model=ContactFormResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Contact Form",
    description="Public endpoint for contact form submissions. Supports department routing for customs, freight, and claims.",
    responses={
        201: {"description": "Contact form submitted successfully"},
        400: {"description": "Invalid form data"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "Service temporarily unavailable"}
    }
)
async def submit_contact_form(form_data: ContactFormRequest, background_tasks: BackgroundTasks):
    """
    Submit a public contact form with department-specific routing
    
    **Supported Departments:**
    - `general` - General inquiries
    - `customs_clearance` - CBSA/US Customs support (urgent)
    - `international_freight` - International shipping questions
    - `quote` - Quote request
    - `tracking` - Tracking or delivery issues (urgent)
    - `claims_insurance` - Claims & insurance support (urgent)
    - `partnership` - Partnership opportunities
    - `feedback` - General feedback
    - `complaint` - Formal complaints
    
    **Response Time:**
    - Urgent departments (customs, tracking, claims): 2-4 hours
    - Standard inquiries: 4-24 hours
    - After hours: Next business day
    """
    
    try:
        # Log submission
        logger.info(
            f"Contact form submission received",
            extra={
                "email": form_data.email,
                "subject": form_data.subject,
                "company": form_data.company
            }
        )

        # Determine routing priority
        urgent_subjects = {
            'customs_clearance',
            'tracking',
            'claims_insurance'
        }
        is_urgent = form_data.subject in urgent_subjects

        # Generate ticket ID
        ticket_id = f"TKT-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}-{form_data.subject[:3].upper()}"

        # Prepare email routing
        recipient_email = settings.SUPPORT_EMAIL or "support@georgensen.ca"
        
        # Route to department-specific queue
        department_routing = {
            'customs_clearance': 'customs@georgensen.ca',
            'international_freight': 'freight@georgensen.ca',
            'claims_insurance': 'claims@georgensen.ca',
            'tracking': 'support@georgensen.ca',  # Urgent routing
        }
        
        if form_data.subject in department_routing:
            recipient_email = department_routing[form_data.subject]

        # Send confirmation email to customer (background task)
        background_tasks.add_task(
            send_contact_confirmation_email,
            email=form_data.email,
            name=form_data.name,
            ticket_id=ticket_id,
            is_urgent=is_urgent
        )

        # Send internal notification (background task)
        background_tasks.add_task(
            send_support_notification,
            form_data=form_data,
            ticket_id=ticket_id,
            recipient_email=recipient_email,
            is_urgent=is_urgent
        )

        # Determine estimated response time
        if is_urgent:
            estimated_response = "2-4 hours during business hours, immediate for critical issues"
        else:
            estimated_response = "4-24 hours during business hours"

        logger.info(f"Contact form processed successfully. Ticket: {ticket_id}")

        return ContactFormResponse(
            success=True,
            message=f"Thank you for contacting Georgensen Courier. We've received your message and will respond based on priority.",
            ticket_id=ticket_id,
            estimated_response_time=estimated_response
        )

    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process contact form. Please try again later."
        )


# ==============================
# Background Tasks
# ==============================

async def send_contact_confirmation_email(
    email: str,
    name: str,
    ticket_id: str,
    is_urgent: bool
):
    """Send confirmation email to customer"""
    try:
        priority_text = "URGENT - High Priority" if is_urgent else "Standard Priority"
        
        subject = f"We received your message - Ticket #{ticket_id}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Thank You, {name}!</h2>
            <p>We've received your contact form submission.</p>
            
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Ticket ID:</strong> {ticket_id}<br>
                <strong>Priority:</strong> {priority_text}<br>
                <strong>Submitted:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}
            </div>
            
            <p>A member of our team will review your inquiry and respond as soon as possible.</p>
            
            <div style="font-size: 14px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                <strong>Quick Links:</strong><br>
                <a href="https://georgensen.ca/tracking.html">Track a shipment</a> | 
                <a href="https://georgensen.ca/services.html">View services</a> | 
                <a href="https://georgensen.ca/contact.html">Contact us</a>
            </div>
            
            <footer style="font-size: 12px; color: #999; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <p><strong>Georgensen Courier</strong><br>
                Toronto, Canada (HQ) | Vancouver | Montreal<br>
                Toll-Free: 1-800-GEORGENSEN | International: +1-416-555-1234<br>
                <a href="https://georgensen.ca">georgensen.ca</a>
                </p>
            </footer>
        </div>
        """
        
        email_service = EmailService()
        await email_service.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content
        )
        
        logger.info(f"Confirmation email sent to {email} for ticket {ticket_id}")
        
    except Exception as e:
        logger.error(f"Failed to send confirmation email to {email}: {str(e)}")


async def send_support_notification(
    form_data: ContactFormRequest,
    ticket_id: str,
    recipient_email: str,
    is_urgent: bool
):
    """Send internal notification to support team"""
    try:
        priority_badge = "🚨 URGENT" if is_urgent else "📋 Standard"
        
        subject = f"[{ticket_id}] {priority_badge} New Contact: {form_data.subject.upper().replace('_', ' ')}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
            <h3 style="color: {'#d32f2f' if is_urgent else '#1976d2'};">
                {priority_badge} New Contact Form Submission
            </h3>
            
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Ticket ID:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{ticket_id}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">From:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">
                        {form_data.name} <br>
                        <a href="mailto:{form_data.email}">{form_data.email}</a>
                        {f'<br>Phone: {form_data.phone}' if form_data.phone else ''}
                        {f'<br>Company: {form_data.company}' if form_data.company else ''}
                    </td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Department:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{form_data.subject.upper().replace('_', ' ')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd; vertical-align: top;">Message:</td>
                    <td style="padding: 10px; border: 1px solid #ddd; white-space: pre-wrap;">{form_data.message}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px; font-weight: bold; border: 1px solid #ddd;">Submitted:</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}</td>
                </tr>
            </table>
            
            <a href="https://georgensen.ca/customer/support" style="display: inline-block; background-color: {'#d32f2f' if is_urgent else '#1976d2'}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                View in Support Dashboard
            </a>
            
            <footer style="font-size: 12px; color: #999; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <p>Auto-generated message from Georgensen Courier Contact System</p>
            </footer>
        </div>
        """
        
        email_service = EmailService()
        await email_service.send_email(
            to_email=recipient_email,
            subject=subject,
            html_content=html_content
        )
        
        logger.info(f"Support notification sent to {recipient_email} for ticket {ticket_id}")
        
    except Exception as e:
        logger.error(f"Failed to send support notification: {str(e)}")
