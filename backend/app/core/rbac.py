"""
Role-Based Access Control (RBAC) utilities for logistics
Enforces role-specific permissions for different user types
"""
from enum import Enum
from typing import List, Optional
from fastapi import HTTPException, status
from app.db.models import User, UserRole


class Permission(str, Enum):
    """Permissions available in the logistics system"""
    # Global permissions (System Admin only)
    VIEW_GLOBAL_ANALYTICS = "view_global_analytics"
    MANAGE_USERS = "manage_users"
    MANAGE_HUBS = "manage_hubs"
    MANAGE_FLEET = "manage_fleet"
    
    # Hub-level permissions (Warehouse Manager)
    VIEW_HUB = "view_hub"
    MANAGE_HUB_SHIPMENTS = "manage_hub_shipments"
    SCHEDULE_STAFF = "schedule_staff"
    VIEW_HUB_ANALYTICS = "view_hub_analytics"
    
    # Driver permissions
    VIEW_ASSIGNED_SHIPMENTS = "view_assigned_shipments"
    SCAN_PACKAGES = "scan_packages"
    UPDATE_LOCATION = "update_location"
    UPLOAD_POD = "upload_pod"
    VIEW_ROUTE = "view_route"
    
    # Handler permissions
    SCAN_AT_HUB = "scan_at_hub"
    SORT_SHIPMENTS = "sort_shipments"
    VIEW_HUB_INVENTORY = "view_hub_inventory"
    
    # Customer permissions
    TRACK_SHIPMENT = "track_shipment"
    VIEW_OWN_SHIPMENTS = "view_own_shipments"
    CREATE_SHIPMENT = "create_shipment"


class RBACService:
    """Service for managing role-based access control"""
    
    # Define role permissions
    ROLE_PERMISSIONS = {
        UserRole.system_admin: [
            Permission.VIEW_GLOBAL_ANALYTICS,
            Permission.MANAGE_USERS,
            Permission.MANAGE_HUBS,
            Permission.MANAGE_FLEET,
            Permission.VIEW_HUB,
            Permission.MANAGE_HUB_SHIPMENTS,
            Permission.VIEW_HUB_ANALYTICS,
            Permission.VIEW_ASSIGNED_SHIPMENTS,
            Permission.SCAN_PACKAGES,
            Permission.UPDATE_LOCATION,
            Permission.UPLOAD_POD,
            Permission.VIEW_ROUTE,
            Permission.SCAN_AT_HUB,
            Permission.SORT_SHIPMENTS,
            Permission.VIEW_HUB_INVENTORY,
            Permission.TRACK_SHIPMENT,
            Permission.VIEW_OWN_SHIPMENTS,
            Permission.CREATE_SHIPMENT,
        ],
        UserRole.warehouse_manager: [
            Permission.VIEW_HUB,
            Permission.MANAGE_HUB_SHIPMENTS,
            Permission.SCHEDULE_STAFF,
            Permission.VIEW_HUB_ANALYTICS,
            Permission.SCAN_AT_HUB,
            Permission.SORT_SHIPMENTS,
            Permission.VIEW_HUB_INVENTORY,
            Permission.VIEW_ASSIGNED_SHIPMENTS,
        ],
        UserRole.driver: [
            Permission.VIEW_ASSIGNED_SHIPMENTS,
            Permission.SCAN_PACKAGES,
            Permission.UPDATE_LOCATION,
            Permission.UPLOAD_POD,
            Permission.VIEW_ROUTE,
            Permission.TRACK_SHIPMENT,  # Can track own assigned shipments
        ],
        UserRole.handler: [
            Permission.SCAN_AT_HUB,
            Permission.SORT_SHIPMENTS,
            Permission.VIEW_HUB_INVENTORY,
            Permission.SCAN_PACKAGES,
        ],
        UserRole.customer: [
            Permission.TRACK_SHIPMENT,
            Permission.VIEW_OWN_SHIPMENTS,
            Permission.CREATE_SHIPMENT,
        ],
        # Legacy roles
        UserRole.admin: [
            Permission.VIEW_GLOBAL_ANALYTICS,
            Permission.MANAGE_USERS,
            Permission.VIEW_HUB,
            Permission.VIEW_ASSIGNED_SHIPMENTS,
        ],
        UserRole.partner: [
            Permission.VIEW_ASSIGNED_SHIPMENTS,
            Permission.SCAN_PACKAGES,
            Permission.UPDATE_LOCATION,
            Permission.UPLOAD_POD,
        ],
        UserRole.support: [
            Permission.VIEW_OWN_SHIPMENTS,
            Permission.TRACK_SHIPMENT,
        ],
    }
    
    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            user: User object
            permission: Permission to check
        
        Returns:
            True if user has permission, False otherwise
        """
        if not user or not user.role:
            return False
        
        permissions = RBACService.ROLE_PERMISSIONS.get(user.role, [])
        return permission in permissions
    
    @staticmethod
    def require_permission(user: User, permission: Permission) -> None:
        """
        Enforce permission requirement - raises exception if user lacks permission
        
        Args:
            user: User object
            permission: Required permission
        
        Raises:
            HTTPException with 403 Forbidden status
        """
        if not RBACService.has_permission(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {permission.value}"
            )
    
    @staticmethod
    def require_role(user: User, allowed_roles: List[UserRole]) -> None:
        """
        Enforce role requirement - raises exception if user is not in allowed roles
        
        Args:
            user: User object
            allowed_roles: List of allowed roles
        
        Raises:
            HTTPException with 403 Forbidden status
        """
        if not user or user.role not in allowed_roles:
            role_names = ", ".join([r.value for r in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to roles: {role_names}"
            )
    
    @staticmethod
    def can_view_hub(user: User, hub_id: Optional[int] = None) -> bool:
        """
        Check if user can view a specific hub
        
        Args:
            user: User object
            hub_id: Hub ID (optional). If provided, user must be assigned to it.
        
        Returns:
            True if user can view, False otherwise
        """
        # System admin can view all hubs
        if user.role == UserRole.system_admin:
            return True
        
        # Warehouse managers/drivers/handlers can only view their assigned hub
        if user.role in [UserRole.warehouse_manager, UserRole.driver, UserRole.handler]:
            if hub_id is None:
                return False
            return user.assigned_hub_id == hub_id
        
        return False
    
    @staticmethod
    def can_manage_shipment(user: User, shipment_hub_id: int) -> bool:
        """
        Check if user can manage a specific shipment
        
        Args:
            user: User object
            shipment_hub_id: Current hub ID of the shipment
        
        Returns:
            True if user can manage, False otherwise
        """
        # System admin can manage all shipments
        if user.role == UserRole.system_admin:
            return True
        
        # Warehouse manager can manage shipments at their hub
        if user.role == UserRole.warehouse_manager:
            return user.assigned_hub_id == shipment_hub_id
        
        # Driver/Handler can scan packages at their hub
        if user.role in [UserRole.driver, UserRole.handler]:
            return user.assigned_hub_id == shipment_hub_id
        
        return False
    
    @staticmethod
    def restrict_to_own_shipments(user: User, shipment_owner_id: int) -> None:
        """
        Enforce that user cannot view/modify other users' shipments
        (Unless they have admin privileges)
        
        Args:
            user: User object
            shipment_owner_id: Owner (customer) of the shipment
        
        Raises:
            HTTPException with 403 Forbidden
        """
        if user.role == UserRole.system_admin or user.role == UserRole.admin:
            return  # Admins can access all
        
        if user.role == UserRole.customer:
            # Customer can only access their own shipments
            # Note: You'll need to map user_id to customer_id in practice
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access other customer's shipments"
            )
    
    @staticmethod
    def get_dashboard_view(user: User) -> str:
        """
        Determine which dashboard view a user should see
        
        Args:
            user: User object
        
        Returns:
            Dashboard type (admin, warehouse_manager, driver, customer, etc.)
        """
        dashboard_map = {
            UserRole.system_admin: "system_admin",
            UserRole.warehouse_manager: "warehouse_manager",
            UserRole.driver: "driver",
            UserRole.handler: "handler",
            UserRole.customer: "customer",
            UserRole.admin: "admin",
            UserRole.partner: "driver",  # Partners see driver dashboard
            UserRole.support: "customer",  # Support staff see customer dashboard
        }
        return dashboard_map.get(user.role, "customer")
    
    @staticmethod
    def get_user_scopes(user: User) -> dict:
        """
        Get scope restrictions for a user based on their role
        
        Args:
            user: User object
        
        Returns:
            Dictionary with scope information
        """
        return {
            "role": user.role.value,
            "assigned_hub_id": user.assigned_hub_id,
            "is_system_admin": user.role == UserRole.system_admin,
            "is_warehouse_manager": user.role == UserRole.warehouse_manager,
            "is_driver": user.role == UserRole.driver,
            "is_handler": user.role == UserRole.handler,
            "is_customer": user.role == UserRole.customer,
            "dashboard_type": RBACService.get_dashboard_view(user),
        }
