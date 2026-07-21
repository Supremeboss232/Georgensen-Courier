"""
Background tasks for Georgensen Courier API.

This module contains all async task definitions using Celery.
Tasks are registered with the celery_app and scheduled via Celery Beat.
"""

from app.celery_app import celery_app

# Import all task modules to ensure registration
from . import email  # noqa
from . import invoices  # noqa
from . import webhooks  # noqa
from . import payouts  # noqa
from . import maintenance  # noqa

__all__ = [
    "celery_app",
    "email",
    "invoices", 
    "webhooks",
    "payouts",
    "maintenance"
]
