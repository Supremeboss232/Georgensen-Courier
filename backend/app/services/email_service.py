"""
Email Service for Georgensen Courier

Handles integration with Celery tasks for async email delivery.
Manages password reset, order confirmation, and other transactional emails.
"""

from app.celery_app import celery_app
import logging
from typing import Optional

logger = logging.getLogger("services.email")


class EmailService:
    """Service for sending emails via Celery tasks"""
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> dict:
        """
        Send an email asynchronously via Celery
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML email body
            plain_content: Plain text email body (optional)
            
        Returns:
            dict: Task status
        """
        try:
            # Queue the email task asynchronously
            task = send_transactional_email.delay(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content or ""
            )
            
            logger.info(f"Email queued for {to_email} - Task ID: {task.id}")
            return {
                "status": "queued",
                "to": to_email,
                "subject": subject,
                "task_id": str(task.id)
            }
        except Exception as exc:
            logger.error(f"Failed to queue email: {str(exc)}")
            return {
                "status": "error",
                "to": to_email,
                "error": str(exc)
            }


@celery_app.task(
    name="send_password_reset_email",
    bind=True,
    retry_policy={
        'max_retries': 3,
        'default_retry_delay': 60,
    }
)
def send_password_reset_email(self, email: str, full_name: str, reset_token: str):
    """
    Send password reset email asynchronously.
    
    This task is triggered immediately when a user requests password reset,
    but the email delivery happens in the background via Celery worker.
    The HTTP response is returned to the user without waiting for this to complete.
    
    Args:
        email: User's email address
        full_name: User's full name (for greeting)
        reset_token: Unique reset token for URL construction
        
    Returns:
        dict: Task status and email metadata
    """
    try:
        logger.info(f"Password reset email queued for {email}")
        
        # Construct password reset URL
        # In production, use your actual domain
        reset_url = f"https://georgensen.app/auth/reset-password?token={reset_token}"
        
        # Email subject
        subject = "Password Reset Request - Georgensen Courier"
        
        # Plain text email body
        plain_body = f"""
Hello {full_name},

You requested to reset your password for your Georgensen Courier account.

Click the link below to set a new password (valid for 24 hours):
{reset_url}

If you didn't request this reset, you can safely ignore this email.
Your password remains unchanged.

Best regards,
Georgensen Courier Team
https://georgensen.app
"""
        
        # HTML email body (more professional)
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .button {{ background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
        .footer {{ background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚚 Georgensen Courier</h1>
            <p>Password Reset Request</p>
        </div>
        
        <div class="content">
            <p>Hello {full_name},</p>
            
            <p>You requested to reset your password for your Georgensen Courier account.</p>
            
            <p>Click the button below to set a new password (valid for 24 hours):</p>
            
            <a href="{reset_url}" class="button">Reset Your Password</a>
            
            <p><strong>Or copy this link:</strong></p>
            <p style="background: #f0f0f0; padding: 10px; word-break: break-all; font-size: 12px;">{reset_url}</p>
            
            <p><strong>Didn't request this?</strong><br>
            You can safely ignore this email if you didn't request a password reset. Your password will remain unchanged.</p>
            
            <hr>
            
            <p style="color: #666; font-size: 12px;">
                This link will expire in 24 hours.<br>
                If you have any questions, please contact our support team.
            </p>
        </div>
        
        <div class="footer">
            <p>&copy; 2026 Georgensen Courier. All rights reserved.</p>
            <p>Keep your password safe and never share reset links with others.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # TODO: Implement actual email sending via SendGrid, Mailgun, AWS SES, etc.
        # For now, log the email operation
        logger.info(
            f"Password reset email would be sent",
            extra={
                "to": email,
                "user": full_name,
                "token_prefix": reset_token[:8],
            }
        )
        
        return {
            "status": "success",
            "to": email,
            "subject": subject,
            "user": full_name,
            "task_id": self.request.id
        }
        
    except Exception as exc:
        logger.error(
            f"Password reset email failed: {str(exc)}",
            extra={
                "to": email,
                "attempt": self.request.retries + 1
            }
        )
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


def queue_password_reset_email(email: str, full_name: str, reset_token: str):
    """
    Synchronously queue password reset email task.
    
    This function returns immediately after queueing,
    allowing the HTTP response to be sent without waiting for email delivery.
    
    Args:
        email: User's email address
        full_name: User's full name
        reset_token: Reset token for password URL
        
    Returns:
        Celery AsyncResult or None
    """
    try:
        # Queue the async task
        task = send_password_reset_email.delay(email, full_name, reset_token)
        logger.info(f"Password reset task queued: {task.id}")
        return task
    except Exception as e:
        logger.error(f"Failed to queue password reset email: {str(e)}")
        # Don't raise - continue execution even if task queueing fails
        return None


@celery_app.task(
    name="send_verification_email",
    bind=True,
    retry_policy={
        'max_retries': 3,
        'default_retry_delay': 60,
    }
)
def send_verification_email(self, email: str, full_name: str, verification_token: str):
    """
    Send email verification code asynchronously.
    
    This task is triggered after user registration to verify their email address.
    The email delivery happens in the background via Celery worker.
    
    Args:
        email: User's email address
        full_name: User's full name (for greeting)
        verification_token: Unique verification token (use first 6 chars as code)
        
    Returns:
        dict: Task status and email metadata
    """
    try:
        logger.info(f"Email verification code queued for {email}")
        
        # Extract first 6 characters as the verification code
        verification_code = verification_token[:6].upper()
        
        # Email subject
        subject = "Verify Your Email - Georgensen Courier"
        
        # Plain text email body
        plain_body = f"""
Hello {full_name},

Thank you for registering with Georgensen Courier!

Your email verification code is:

    {verification_code}

This code is valid for 24 hours. Enter this code in the verification form to complete your registration.

If you didn't create this account, you can safely ignore this email.

Best regards,
Georgensen Courier Team
https://georgensen.app
"""
        
        # HTML email body (more professional)
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .code-box {{ 
            background: #f0f0f0; 
            border: 2px dashed #667eea; 
            padding: 20px; 
            text-align: center; 
            border-radius: 5px; 
            margin: 20px 0;
        }}
        .code {{ 
            font-size: 2.5rem; 
            font-weight: bold; 
            color: #667eea; 
            letter-spacing: 0.5rem;
            font-family: monospace;
        }}
        .expiry {{ 
            font-size: 0.9rem; 
            color: #999; 
            text-align: center; 
            margin: 15px 0;
        }}
        .footer {{ background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚚 Georgensen Courier</h1>
            <p>Email Verification</p>
        </div>
        
        <div class="content">
            <p>Hello {full_name},</p>
            
            <p>Thank you for registering with Georgensen Courier! We're excited to have you join our logistics network.</p>
            
            <p>To complete your registration, please verify your email address using the code below:</p>
            
            <div class="code-box">
                <div class="code">{verification_code}</div>
            </div>
            
            <p style="text-align: center;">
                <strong>Enter this code in the verification form to confirm your email.</strong>
            </p>
            
            <div class="expiry">
                This code is valid for 24 hours.
            </div>
            
            <p><strong>Didn't create this account?</strong><br>
            If you didn't register for a Georgensen Courier account, you can safely ignore this email. No action is required.</p>
            
            <hr>
            
            <p style="color: #666; font-size: 12px;">
                Your security is important to us. Never share your verification code with anyone.
            </p>
        </div>
        
        <div class="footer">
            <p>&copy; 2026 Georgensen Courier. All rights reserved.</p>
            <p>Keep your account secure by using a strong password and protecting your verification codes.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # TODO: Implement actual email sending via SendGrid, Mailgun, AWS SES, etc.
        # For now, log the email operation
        logger.info(
            f"Email verification code would be sent",
            extra={
                "to": email,
                "user": full_name,
                "code": verification_code,
            }
        )
        
        return {
            "status": "success",
            "to": email,
            "subject": subject,
            "user": full_name,
            "code": verification_code,
            "task_id": self.request.id
        }
        
    except Exception as exc:
        logger.error(
            f"Email verification failed: {str(exc)}",
            extra={
                "to": email,
                "attempt": self.request.retries + 1
            }
        )
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@celery_app.task(
    name="send_transactional_email",
    bind=True,
    retry_policy={
        'max_retries': 3,
        'default_retry_delay': 60,
    }
)
def send_transactional_email(self, to_email: str, subject: str, html_content: str, plain_content: str = ""):
    """
    Send a transactional email asynchronously.
    
    This task handles generic transactional emails (contact forms, support tickets, confirmations, etc.).
    The email delivery happens in the background via Celery worker.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML email body
        plain_content: Plain text email body (optional)
        
    Returns:
        dict: Task status and email metadata
    """
    try:
        logger.info(f"Transactional email queued for {to_email} - Subject: {subject}")
        
        # TODO: Implement actual email sending via SendGrid, Mailgun, AWS SES, etc.
        # For now, log the email operation
        logger.info(
            f"Transactional email would be sent",
            extra={
                "to": to_email,
                "subject": subject,
                "content_length": len(html_content),
            }
        )
        
        return {
            "status": "success",
            "to": to_email,
            "subject": subject,
            "task_id": self.request.id
        }
        
    except Exception as exc:
        logger.error(
            f"Transactional email failed: {str(exc)}",
            extra={
                "to": to_email,
                "subject": subject,
                "attempt": self.request.retries + 1
            }
        )
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)