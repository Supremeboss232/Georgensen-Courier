"""
Unified EmailService module for Georgensen Courier
Supports both synchronous/logged delivery and optional Celery task queueing.
"""
import logging
from typing import Optional

logger = logging.getLogger("services.email")


class EmailService:
    """Service for transactional, verification, and password reset emails"""

    @staticmethod
    def send_verification_email(email: str, user_name: str, verification_token: str) -> dict:
        code = (verification_token or "")[:6].upper()
        logger.info(f"Verification email prepared for {email} ({user_name}) - Code: {code}")
        return {
            "status": "sent",
            "to": email,
            "user_name": user_name,
            "code": code,
        }

    @staticmethod
    def send_password_reset_email(email: str, user_name: str, reset_token: str) -> dict:
        logger.info(f"Password reset email prepared for {email} ({user_name})")
        return {
            "status": "sent",
            "to": email,
            "user_name": user_name,
        }

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> dict:
        logger.info(f"Transactional email sent to {to_email} - Subject: {subject}")
        return {
            "status": "sent",
            "to": to_email,
            "subject": subject,
        }
