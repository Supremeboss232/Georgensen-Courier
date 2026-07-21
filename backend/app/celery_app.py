"""
Celery configuration for background job processing
Handles async tasks: email, invoices, payouts, webhooks

Installation:
    pip install celery redis

Run celery worker:
    celery -A app.celery_app worker --loglevel=info

Run celery beat (scheduler):
    celery -A app.celery_app beat --loglevel=info

Monitor with Flower:
    celery -A app.celery_app flower  # http://localhost:5555
"""

from celery import Celery
from celery.schedules import crontab
import os
from typing import Optional

# ============================================================================
# CELERY APP CONFIGURATION
# ============================================================================

# Get configuration from environment
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://localhost:6379/0"
)
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    "redis://localhost:6379/1"
)

# Create Celery app
celery_app = Celery(
    "georgensen-courier",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    
    # Retry settings
    task_autoretry_for=(Exception,),
    task_max_retries=5,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Don't prefetch multiple tasks
    worker_max_tasks_per_child=1000,  # Restart worker every 1000 tasks
    
    # Periodic task settings
    beat_schedule={
        # Daily invoice generation
        "generate-daily-invoices": {
            "task": "app.tasks.invoices.generate_daily_invoices",
            "schedule": crontab(hour=2, minute=0),  # 2 AM UTC
            "options": {"expires": 3600},  # Expire if not run within 1 hour
        },
        
        # Weekly partner payouts
        "partner-weekly-payouts": {
            "task": "app.tasks.payouts.process_weekly_payouts",
            "schedule": crontab(day_of_week=4, hour=23),  # Thursday 11 PM UTC
            "options": {"expires": 3600},
        },
        
        # Hourly: Check for expired international rates
        "expire-international-rates": {
            "task": "app.tasks.rates.expire_old_rates",
            "schedule": crontab(minute=0),  # Every hour
            "options": {"expires": 1800},
        },
        
        # Every 30 minutes: Retry failed webhooks
        "retry-failed-webhooks": {
            "task": "app.tasks.webhooks.retry_failed_webhooks",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
            "options": {"expires": 900},  # Expire after 15 minutes
        },
        
        # Daily: Clean up old logs
        "cleanup-old-logs": {
            "task": "app.tasks.maintenance.cleanup_logs",
            "schedule": crontab(hour=3, minute=0),  # 3 AM UTC
            "options": {"expires": 3600},
        },
    }
)


# ============================================================================
# TASK DEFINITIONS
# ============================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, email: str, subject: str, template: str, context: dict):
    """
    Send email asynchronously
    
    Retries: Up to 3 times, 60 second delay between retries
    
    Args:
        email: Recipient email address
        subject: Email subject
        template: Template name (e.g., "order-confirmation")
        context: Template context variables
    """
    try:
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        service.send_email(email, subject=subject, template=template, context=context)
        
        # Log success
        from app.core.logging_config import setup_json_logging
        logger = setup_json_logging()
        logger.info(
            "Email sent",
            extra={
                "email": email,
                "subject": subject,
                "task_id": self.request.id,
            }
        )
    
    except Exception as exc:
        # Retry with exponential backoff
        countdown = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, max_retries=5, default_retry_delay=5)
def process_stripe_webhook_task(self, event_id: str, event_type: str, event_data: dict):
    """
    Process Stripe webhook events with retry logic
    
    Retries: Up to 5 times with exponential backoff
    
    Args:
        event_id: Stripe event ID (for idempotency)
        event_type: Type of event (payment_intent.succeeded, etc)
        event_data: Event data from Stripe
    """
    try:
        from app.api.webhooks import (
            _handle_payment_succeeded,
            _handle_payment_failed,
            _handle_refund,
            _handle_dispute_created,
        )
        from app.db.base import SessionLocal
        
        db = SessionLocal()
        
        # Check if already processed (idempotency)
        from app.db.models.webhook import WebhookLog
        existing = db.query(WebhookLog).filter(
            WebhookLog.stripe_event_id == event_id
        ).first()
        
        if existing:
            # Already processed, return early
            return {"status": "already_processed"}
        
        # Process event
        if event_type == "payment_intent.succeeded":
            _handle_payment_succeeded(db, event_data)
        elif event_type == "payment_intent.payment_failed":
            _handle_payment_failed(db, event_data)
        elif event_type == "charge.refunded":
            _handle_refund(db, event_data)
        elif event_type == "charge.dispute.created":
            _handle_dispute_created(db, event_data)
        
        # Log success
        from datetime import datetime, timezone
        webhook_log = WebhookLog(
            stripe_event_id=event_id,
            event_type=event_type,
            status="processed",
            processed_at=datetime.now(timezone.utc)
        )
        db.add(webhook_log)
        db.commit()
        
        return {"status": "processed"}
    
    except Exception as exc:
        # Exponential backoff: 5s, 10s, 20s, 40s, 80s
        countdown = 5 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True)
def generate_daily_invoices_task(self):
    """
    Generate daily invoices for all customers
    
    Runs: Daily at 2 AM UTC
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from sqlalchemy.orm import Session
    from collections import defaultdict
    
    from app.db.base import SessionLocal
    from app.db.models.shipment import Shipment
    from app.db.models.invoice import Invoice
    
    db = SessionLocal()
    
    try:
        # Find shipments from yesterday
        yesterday = datetime.now() - timedelta(days=1)
        shipments = db.query(Shipment).filter(
            Shipment.created_at >= yesterday,
            Shipment.status.in_(["delivered", "in_transit"])
        ).all()
        
        # Group by customer
        by_customer = defaultdict(list)
        for shipment in shipments:
            by_customer[shipment.customer_id].append(shipment)
        
        # Create invoices
        created_count = 0
        for customer_id, shipments_list in by_customer.items():
            total = sum(s.total_amount or 0 for s in shipments_list)
            
            invoice = Invoice(
                customer_id=customer_id,
                invoice_number=f"INV-{datetime.now().strftime('%Y%m%d')}-{customer_id}",
                total_amount=total,
                status="issued",
                issued_date=datetime.now()
            )
            db.add(invoice)
            created_count += 1
            
            # Queue email
            send_email_task.delay(
                email="customer@example.com",  # Get from customer
                subject="Your Daily Invoice",
                template="invoice",
                context={"invoice": invoice}
            )
        
        db.commit()
        
        return {"created": created_count, "status": "success"}
    
    except Exception as e:
        db.rollback()
        raise
    
    finally:
        db.close()


@celery_app.task(bind=True)
def process_weekly_payouts_task(self):
    """
    Process partner payouts
    
    Runs: Weekly Thursday 11 PM UTC
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_
    
    from app.db.base import SessionLocal
    from app.db.models.partner import Partner
    from app.db.models.shipment import Shipment
    from app.db.models.invoice import Invoice
    from app.services.payout import PartnerPayout
    
    db = SessionLocal()
    
    try:
        week_start = datetime.now() - timedelta(days=7)
        payout_service = PartnerPayout(db)
        
        # Get payouts (will implement actual logic in PartnerPayout service)
        results = payout_service.process_weekly_payouts()
        
        return {"processed": len(results), "status": "success", "results": results}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
    
    finally:
        db.close()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def send_email_async(
    email: str,
    subject: str,
    template: str,
    context: Optional[dict] = None,
    priority: str = "normal"
):
    """
    Queue email to be sent asynchronously
    
    Usage:
        from celery_app import send_email_async
        send_email_async(
            "user@example.com",
            subject="Welcome!",
            template="welcome",
            context={"name": "John"}
        )
    
    Args:
        email: Recipient email
        subject: Email subject
        template: Template name
        context: Template variables
        priority: "high" for urgent emails (retry more aggressively)
    """
    context = context or {}
    
    if priority == "high":
        # High priority: retry faster, more retries
        send_email_task.apply_async(
            args=(email, subject, template, context),
            retry=True,
            retry_policy={"max_retries": 5, "interval_start": 10}
        )
    else:
        # Normal priority
        send_email_task.delay(email, subject, template, context)


def get_task_status(task_id: str) -> dict:
    """Get status of a celery task"""
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
        "error": str(result.info) if result.failed() else None,
    }


if __name__ == "__main__":
    # For development: Test task
    @celery_app.task
    def test_task(x: int, y: int) -> int:
        """Simple test task"""
        return x + y
    
    # Run test
    result = test_task.delay(4, 6)
    print(f"Task ID: {result.id}")
    print(f"Result: {result.get(timeout=3)}")
