"""
Database models for Georgensen Courier
"""
from .user import User, UserRole
from .auth import EmailVerification, RefreshToken, AuthAuditLog, PasswordReset, LoginAttempt
from .customer import Customer
from .address import Address
from .partner import Partner
from .shipment import Shipment, ShipmentStatus
from .tracking import Tracking, TrackingStatus
from .tracking_history import TrackingHistory
from .pod import POD
from .dispute import Dispute
from .invoice import Invoice
from .support_ticket import SupportTicket

from .hub import Hub, HubStatus
from .fleet_vehicle import FleetVehicle, VehicleStatus, VehicleType
from .handler import Handler, HandlerType, HandlerStatus
from .shipment_log import ShipmentLog, LogAction
from .webhook import WebhookEvent

__all__ = [
    "User",
    "UserRole",
    "EmailVerification",
    "RefreshToken",
    "AuthAuditLog",
    "PasswordReset",
    "LoginAttempt",
    "Customer",
    "Address",
    "Partner",
    "Shipment",
    "ShipmentStatus",
    "Tracking",
    "TrackingStatus",
    "TrackingHistory",
    "POD",
    "Dispute",
    "Invoice",
    "SupportTicket",
    # Logistics models
    "Hub",
    "HubStatus",
    "FleetVehicle",
    "VehicleStatus",
    "VehicleType",
    "Handler",
    "HandlerType",
    "HandlerStatus",
    "ShipmentLog",
    "LogAction",
    "WebhookEvent",
]

