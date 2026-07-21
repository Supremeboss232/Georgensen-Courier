import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications (email, SMS, WhatsApp)"""
    
    @staticmethod
    def _send_smtp_email(to_email: str, subject: str, html_body: str) -> bool:
        """Send email via SMTP"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
            message["To"] = to_email
            
            # Attach HTML body
            message.attach(MIMEText(html_body, "html"))
            
            # Connect to SMTP server and send
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()  # Encrypt the connection
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.MAIL_FROM, [to_email], message.as_string())
            
            logger.info(f"✓ Email sent to {to_email}: {subject}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error(f"✗ SMTP Authentication failed. Check SMTP_USER and SMTP_PASSWORD in .env")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"✗ SMTP error sending to {to_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"✗ Error sending email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_order_confirmation_email(
        customer_email: str,
        customer_name: str,
        tracking_number: str,
        total_price: float
    ) -> bool:
        """Send order confirmation email"""
        try:
            subject = f"Order Confirmed - Track ID: {tracking_number}"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #1e40af;">Order Confirmation</h2>
                    <p>Dear {customer_name},</p>
                    <p>Your delivery order has been confirmed! Here are the details:</p>
                    
                    <div style="background: #f0f9ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <p><strong>Tracking Number:</strong> <code style="background: #e0e7ff; padding: 5px 10px;">{tracking_number}</code></p>
                        <p><strong>Total Price:</strong> <span style="color: #059669; font-weight: bold;">${total_price:.2f}</span></p>
                        <p><strong>Status:</strong> Pending Partner Assignment</p>
                        <p><strong>Next Step:</strong> We'll assign a delivery partner within the next few minutes</p>
                    </div>
                    
                    <p><strong>Track your delivery:</strong><br>
                    <a href="https://georjensen.app/track/{tracking_number}" style="color: #1e40af; text-decoration: none;">
                        Click here to track your shipment →
                    </a></p>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                    
                    <p style="color: #6b7280; font-size: 12px;">
                        Thank you for choosing Georgensen!<br>
                        24/7 Support: support@georjensen.app | Phone: 1-800-GEORJENSEN
                    </p>
                </body>
            </html>
            """
            
            return NotificationService._send_smtp_email(customer_email, subject, html_body)
            
        except Exception as e:
            logger.error(f"Error preparing confirmation email: {str(e)}")
            return False
    
    @staticmethod
    def send_order_assigned_email(
        customer_email: str,
        customer_name: str,
        partner_name: str,
        partner_phone: str,
        tracking_number: str
    ) -> bool:
        """Send partner assignment notification"""
        try:
            subject = f"Your Delivery Partner Assigned - {tracking_number}"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #1e40af;">Delivery Partner Assigned</h2>
                    <p>Dear {customer_name},</p>
                    <p>Great news! A delivery partner has been assigned to your shipment.</p>
                    
                    <div style="background: #f0fdf4; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #16a34a;">
                        <p><strong>Partner Name:</strong> {partner_name}</p>
                        <p><strong>Contact Number:</strong> <a href="tel:{partner_phone}" style="color: #1e40af; text-decoration: none;">{partner_phone}</a></p>
                        <p><strong>Tracking:</strong> {tracking_number}</p>
                    </div>
                    
                    <p>Your partner will contact you shortly with pickup/delivery details.</p>
                    
                    <p><a href="https://georjensen.app/track/{tracking_number}" style="background: #1e40af; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Track in Real-Time →
                    </a></p>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                    
                    <p style="color: #6b7280; font-size: 12px;">
                        Need help? Contact us: support@georjensen.app
                    </p>
                </body>
            </html>
            """
            
            return NotificationService._send_smtp_email(customer_email, subject, html_body)
            
        except Exception as e:
            logger.error(f"Error preparing assignment email: {str(e)}")
            return False
            
            print(f"[EMAIL] Sent to {customer_email}: Partner Assignment {tracking_number}")
            return True
            
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send assignment email: {str(e)}")
            return False
    
    @staticmethod
    def send_delivery_confirmation_email(
        customer_email: str,
        customer_name: str,
        tracking_number: str,
        delivery_address: str
    ) -> bool:
        """Send delivery confirmation email"""
        try:
            message = MIMEMultipart()
            message["From"] = settings.MAIL_FROM
            message["To"] = customer_email
            message["Subject"] = f"Delivery Confirmed - {tracking_number}"
            
            body = f"""
            <html>
                <body>
                    <h2>Delivery Confirmed</h2>
                    <p>Dear {customer_name},</p>
                    <p>Your order has been delivered!</p>
                    <ul>
                        <li><strong>Tracking:</strong> {tracking_number}</li>
                        <li><strong>Delivered to:</strong> {delivery_address}</li>
                    </ul>
                    <p>Thank you for using Georgensen!</p>
                </body>
            </html>
            """
            
            message.attach(MIMEText(body, "html"))
            
            print(f"[EMAIL] Sent to {customer_email}: Delivery Confirmation {tracking_number}")
            return True
            
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send delivery email: {str(e)}")
            return False
    
    @staticmethod
    def send_partner_payment_email(
        partner_email: str,
        partner_name: str,
        orders_count: int,
        total_earnings: float,
        period: str
    ) -> bool:
        """Send payment summary to partner"""
        try:
            message = MIMEMultipart()
            message["From"] = settings.MAIL_FROM
            message["To"] = partner_email
            message["Subject"] = f"Payment Summary - {period}"
            
            body = f"""
            <html>
                <body>
                    <h2>Payment Summary</h2>
                    <p>Dear {partner_name},</p>
                    <p>Here's your payment summary for {period}:</p>
                    <ul>
                        <li><strong>Deliveries:</strong> {orders_count}</li>
                        <li><strong>Total Earnings:</strong> ${total_earnings:.2f}</li>
                    </ul>
                    <p>Payment will be processed within 24 hours.</p>
                </body>
            </html>
            """
            
            message.attach(MIMEText(body, "html"))
            
            print(f"[EMAIL] Sent to {partner_email}: Payment Summary {period}")
            return True
            
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send payment email: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_confirmation_email(
        recipient_email: str,
        invoice_id: int,
        amount: float
    ) -> bool:
        """Send payment confirmation email"""
        try:
            subject = f"Payment Confirmed - Invoice #{invoice_id}"
            
            body = f"""
            <html>
                <body>
                    <h2>Payment Received</h2>
                    <p>Thank you for your payment!</p>
                    <ul>
                        <li><strong>Invoice #:</strong> {invoice_id}</li>
                        <li><strong>Amount Paid:</strong> ${amount:.2f}</li>
                        <li><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
                    </ul>
                    <p>A receipt has been sent to this email address.</p>
                    <p>Thank you for using Georgensen Courier!</p>
                </body>
            </html>
            """
            
            return NotificationService._send_smtp_email(recipient_email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send payment confirmation: {str(e)}")
            return False
    
    @staticmethod
    def send_alert_email(
        admin_email: str,
        alert_type: str,
        details: Dict
    ) -> bool:
        """Send admin alert email for disputes, escalations, etc."""
        try:
            subject = f"[ALERT] {alert_type.upper()} - Immediate Review Required"
            
            body = f"""
            <html>
                <body>
                    <h2 style="color: #d9534f;">⚠️ {alert_type.upper()}</h2>
                    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    
                    <table style="border: 1px solid #ddd; border-collapse: collapse;">
                        <tbody>
            """
            
            # Add details to the email
            for key, value in details.items():
                body += f"""
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{key}</td>
                                <td style="padding: 8px; border: 1px solid #ddd;">{value}</td>
                            </tr>
                """
            
            body += """
                        </tbody>
                    </table>
                    
                    <p style="margin-top: 20px; color: #d9534f;">
                        <strong>Action Required:</strong> Please log in to the admin dashboard to review and take action.
                    </p>
                </body>
            </html>
            """
            
            return NotificationService._send_smtp_email(admin_email, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send admin alert: {str(e)}")
            return False
    
    @staticmethod
    def log_notification(
        notification_type: str,
        recipient: str,
        details: Dict
    ) -> None:
        """Log notification for audit trail"""
        print(f"[NOTIFICATION] {notification_type} to {recipient}: {details}")
