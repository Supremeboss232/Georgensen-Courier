"""
Role-based permission system for Georgensen Courier
"""
from enum import Enum
from typing import List
from functools import wraps
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from ..api.deps import get_current_user


class Role(str, Enum):
    """System roles"""
    ADMIN = "admin"
    CUSTOMER = "customer"
    PARTNER = "partner"
    SUPPORT = "support"


class Permission(str, Enum):
    """Fine-grained permissions"""
    # Customer permissions
    CREATE_SHIPMENT = "create_shipment"
    VIEW_SHIPMENT = "view_shipment"
    UPDATE_SHIPMENT = "update_shipment"
    CANCEL_SHIPMENT = "cancel_shipment"
    VIEW_INVOICE = "view_invoice"
    PAY_INVOICE = "pay_invoice"
    VIEW_TRACKING = "view_tracking"
    CREATE_SUPPORT_TICKET = "create_support_ticket"
    
    # Partner permissions
    VIEW_ASSIGNED_DELIVERY = "view_assigned_delivery"
    UPDATE_DELIVERY_STATUS = "update_delivery_status"
    VIEW_EARNINGS = "view_earnings"
    
    # Admin permissions
    MANAGE_CUSTOMERS = "manage_customers"
    MANAGE_PARTNERS = "manage_partners"
    MANAGE_PRICING = "manage_pricing"
    VIEW_REPORTS = "view_reports"
    MANAGE_DISPUTES = "manage_disputes"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.CUSTOMER: [
        Permission.CREATE_SHIPMENT,
        Permission.VIEW_SHIPMENT,
        Permission.UPDATE_SHIPMENT,
        Permission.CANCEL_SHIPMENT,
        Permission.VIEW_INVOICE,
        Permission.PAY_INVOICE,
        Permission.VIEW_TRACKING,
        Permission.CREATE_SUPPORT_TICKET,
    ],
    Role.PARTNER: [
        Permission.VIEW_ASSIGNED_DELIVERY,
        Permission.UPDATE_DELIVERY_STATUS,
        Permission.VIEW_EARNINGS,
    ],
    Role.SUPPORT: [
        Permission.VIEW_SHIPMENT,
        Permission.VIEW_INVOICE,
        Permission.CREATE_SUPPORT_TICKET,
        Permission.MANAGE_DISPUTES,
    ],
    Role.ADMIN: [
        Permission.MANAGE_CUSTOMERS,
        Permission.MANAGE_PARTNERS,
        Permission.MANAGE_PRICING,
        Permission.VIEW_REPORTS,
        Permission.MANAGE_DISPUTES,
        Permission.VIEW_SHIPMENT,
        Permission.VIEW_INVOICE,
    ],
}


def get_user_permissions(role: Role) -> List[Permission]:
    """Get all permissions for a role"""
    return ROLE_PERMISSIONS.get(role, [])


def require_role(*roles: Role):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
            if current_user.role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {current_user.role} not authorized for this action"
                )
            kwargs['current_user'] = current_user
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(*permissions: Permission):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
            user_permissions = get_user_permissions(Role(current_user.role))
            if not any(p in user_permissions for p in permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            kwargs['current_user'] = current_user
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_customer_ownership(customer_id: int):
    """Decorator to verify customer can only access their own data"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
            if current_user.role == Role.CUSTOMER:
                # Verify customer owns this resource
                # This would typically fetch from DB to get customer_id from user_id
                pass
            kwargs['current_user'] = current_user
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def verify_resource_ownership(resource_type: str, user_id_field: str = "user_id"):
    """
    Decorator to verify user owns the resource they're accessing
    
    Args:
        resource_type: Type of resource (shipment, invoice, etc)
        user_id_field: Field name containing owner user_id in the resource
    
    Usage:
        @router.get("/shipments/{shipment_id}")
        @verify_resource_ownership("shipment")
        async def get_shipment(
            shipment_id: int,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from sqlalchemy.orm import Session
            from sqlalchemy import inspect
            
            # Extract current_user and db from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not current_user or not db:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Admin and support can access anything
            if current_user.role in [Role.ADMIN, Role.SUPPORT]:
                return await func(*args, **kwargs)
            
            # For customers: verify ownership
            if current_user.role == Role.CUSTOMER:
                # Get the resource_id from function arguments
                resource_id = kwargs.get(f"{resource_type}_id")
                
                if not resource_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing {resource_type}_id"
                    )
                
                # Fetch resource based on type
                resource = _fetch_resource(db, resource_type, resource_id)
                
                if not resource:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{resource_type.capitalize()} not found"
                    )
                
                # Check ownership
                owner_id = getattr(resource, user_id_field, None)
                if owner_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"You do not have access to this {resource_type}"
                    )
            
            # For partners: verify if resource is assigned to them
            elif current_user.role == Role.PARTNER:
                resource_id = kwargs.get(f"{resource_type}_id")
                if not resource_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing {resource_type}_id"
                    )
                
                resource = _fetch_resource(db, resource_type, resource_id)
                if not resource:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{resource_type.capitalize()} not found"
                    )
                
                # Check if partner is assigned (for shipments, check tracking entries)
                if resource_type == "shipment":
                    tracking = db.query(db.metadata.tables.get('tracking')).filter(
                        db.metadata.tables.get('tracking').c.shipment_id == resource_id,
                        db.metadata.tables.get('tracking').c.partner_id == current_user.partner_id
                    ).first()
                    if not tracking:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not assigned to this shipment"
                        )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def _fetch_resource(db: Session, resource_type: str, resource_id: int):
    """Helper to fetch resource by type"""
    from app.db.models.shipment import Shipment
    from app.db.models.invoice import Invoice
    from app.db.models.dispute import Dispute
    from app.db.models.support_ticket import SupportTicket
    
    resource_map = {
        "shipment": Shipment,
        "invoice": Invoice,
        "dispute": Dispute,
        "support_ticket": SupportTicket,
    }
    
    model = resource_map.get(resource_type)
    if not model:
        return None
    
    return db.query(model).get(resource_id)