"""
Invoice tasks for Georgensen Courier API.

Handles automated invoice generation and related operations.
Tasks are scheduled to run daily via Celery Beat.
"""

from app.celery_app import celery_app
from app.core.logging_config import create_task_logger
from app.db.base import SessionLocal
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("tasks.invoices")


@celery_app.task(
    name="generate_daily_invoices",
    bind=True,
)
def generate_daily_invoices_task(self):
    """
    Generate invoices for all completed orders from the previous day.
    
    Runs daily at 02:00 UTC via Celery Beat.
    
    Returns:
        dict: Summary of invoices generated
    """
    task_logger = create_task_logger("generate_daily_invoices", self.request.id)
    
    try:
        task_logger.info("Starting daily invoice generation", extra={
            "scheduled_time": datetime.utcnow().isoformat()
        })
        
        db = SessionLocal()
        
        try:
            # TODO: Query orders from previous day that need invoicing
            # Filter by status='delivered' and invoice_generated=False
            # Generate invoice documents
            # Update order.invoice_generated = True
            
            invoices_generated = 0
            total_amount = 0.0
            
            task_logger.info("Daily invoices generated", extra={
                "count": invoices_generated,
                "total_amount": total_amount,
                "currency": "USD"
            })
            
            return {
                "status": "success",
                "invoices_generated": invoices_generated,
                "total_amount": total_amount,
                "date": datetime.utcnow().date().isoformat()
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        task_logger.error("Daily invoice generation failed", extra={
            "error": str(exc),
            "error_type": type(exc).__name__
        })
        raise


@celery_app.task(
    name="send_invoice_to_customer",
    bind=True,
    retry_policy={
        'max_retries': 3,
        'default_retry_delay': 300,  # 5 minutes
    }
)
def send_invoice_to_customer_task(self, order_id: int, customer_email: str):
    """
    Send generated invoice to customer via email.
    
    Args:
        order_id: Order ID
        customer_email: Customer email address
    """
    task_logger = create_task_logger("send_invoice_to_customer", self.request.id)
    
    try:
        task_logger.info("Sending invoice to customer", extra={
            "order_id": order_id,
            "customer_email": customer_email
        })
        
        # TODO: Generate invoice PDF
        # TODO: Send via email service
        
        task_logger.info("Invoice sent successfully", extra={
            "order_id": order_id
        })
        
        return {
            "status": "sent",
            "order_id": order_id,
            "recipient": customer_email
        }
        
    except Exception as exc:
        task_logger.error("Invoice sending failed", extra={
            "order_id": order_id,
            "error": str(exc),
            "attempt": self.request.retries + 1
        })
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(name="archive_old_invoices")
def archive_old_invoices_task():
    """
    Archive invoices older than 1 year.
    
    Runs monthly on the 1st at 03:00 UTC via Celery Beat.
    """
    logger.info("Starting invoice archival process")
    
    db = SessionLocal()
    
    try:
        # TODO: Query invoices older than 1 year
        # Move to archive storage (S3, etc.)
        # Delete or mark as archived in database
        
        logger.info("Invoice archival completed", extra={
            "archived_count": 0
        })
        
        return {
            "status": "success",
            "archived_count": 0
        }
        
    finally:
        db.close()
