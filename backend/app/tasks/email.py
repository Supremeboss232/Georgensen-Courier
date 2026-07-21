"""
Email tasks for Georgensen Courier API.

Handles async email sending operations like order confirmations,
shipping notifications, and quote responses.
"""

from app.celery_app import celery_app
from app.core.logging_config import create_task_logger
import logging

logger = logging.getLogger("tasks.email")


@celery_app.task(
    name="send_email",
    bind=True,
    retry_policy={
        'max_retries': 3,
        'default_retry_delay': 60,  # 1 minute
        'autoretry_for': (Exception,),
    }
)
def send_email_task(self, to_email: str, subject: str, body: str, html_body: str = None):
    """
    Send email asynchronously.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
        
    Returns:
        dict: Email send status and message ID
        
    Raises:
        Exception: On email service errors (will retry)
    """
    task_logger = create_task_logger("send_email", self.request.id)
    
    try:
        task_logger.info("Sending email", extra={
            "to": to_email,
            "subject": subject[:50],
            "attempt": self.request.retries + 1
        })
        
        # TODO: Integrate with email service (SendGrid, Mailgun, AWS SES)
        # For now, log the email sending
        task_logger.info("Email sent successfully", extra={
            "to": to_email,
            "message_id": f"msg_{self.request.id}"
        })
        
        return {
            "status": "success",
            "to": to_email,
            "subject": subject,
            "message_id": f"msg_{self.request.id}"
        }
        
    except Exception as exc:
        task_logger.error("Email sending failed", extra={
            "error": str(exc),
            "attempt": self.request.retries + 1,
            "to": to_email
        })
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(
    name="send_order_confirmation",
    bind=True,
    retry_policy={
        'max_retries': 3,
        'default_retry_delay': 60,
    }
)
def send_order_confirmation_task(self, order_id: int, customer_email: str):
    """
    Send order confirmation email to customer.
    
    Args:
        order_id: Order ID
        customer_email: Customer email address
    """
    task_logger = create_task_logger("send_order_confirmation", self.request.id)
    
    try:
        task_logger.info("Sending order confirmation", extra={
            "order_id": order_id,
            "customer_email": customer_email
        })
        
        # TODO: Fetch order details and render email template
        subject = f"Order Confirmation - #{order_id}"
        
        result = send_email_task(
            to_email=customer_email,
            subject=subject,
            body=f"Your order {order_id} has been confirmed",
            html_body=f"<h1>Order Confirmation</h1><p>Order ID: {order_id}</p>"
        )
        
        task_logger.info("Order confirmation email sent", extra={
            "order_id": order_id,
            "result": result
        })
        
        return result
        
    except Exception as exc:
        task_logger.error("Order confirmation email failed", extra={
            "order_id": order_id,
            "error": str(exc)
        })
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(name="send_shipping_notification")
def send_shipping_notification_task(order_id: int, tracking_number: str):
    """
    Send shipping notification email with tracking info.
    
    Args:
        order_id: Order ID
        tracking_number: Tracking number for the shipment
    """
    logger.info("Sending shipping notification", extra={
        "order_id": order_id,
        "tracking_number": tracking_number
    })
    
    # TODO: Implement shipping notification email
    return {
        "status": "sent",
        "order_id": order_id,
        "tracking_number": tracking_number
    }
