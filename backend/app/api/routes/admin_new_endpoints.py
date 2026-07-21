# New endpoints for admin users management
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.models import User, Shipment
from app.api.deps import get_current_admin

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"]
)

@router.get("/users/{user_id}/logistics-history")
async def get_user_logistics_history(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get user's regional logistics history"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get logistics history by region (mock for now)
    regions = ['north_america', 'europe', 'asia_pacific', 'middle_east', 'latin_america']
    history = []
    
    for region in regions:
        # Count shipments in region
        shipment_count = db.query(Shipment).filter(
            Shipment.assigned_handler_id == user_id if user.role == "partner" else Shipment.customer_id == user_id
        ).count()
        
        if shipment_count > 0:
            history.append({
                "region": region,
                "shipment_count": shipment_count,
                "rating": getattr(user, 'rating', 4.5),
                "last_active": getattr(user, 'updated_at', None)
            })
    
    return history


@router.post("/users/bulk-action")
async def bulk_user_action(
    action_data: dict,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Perform bulk actions on multiple users"""
    
    user_ids = action_data.get("user_ids", [])
    action = action_data.get("action")
    
    if not user_ids or not action:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing user_ids or action"
        )
    
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    
    if action == "send_regional_update":
        message = action_data.get("message", "")
        # Send email/notification logic here
        return {
            "message": f"Regional update sent to {len(users)} users",
            "action": action,
            "user_count": len(users)
        }
    
    elif action == "suspend_regional_access":
        for user in users:
            user.is_active = False
        db.commit()
        return {
            "message": f"Suspended access for {len(users)} users",
            "action": action,
            "user_count": len(users)
        }
    
    elif action == "send_compliance_reminder":
        # Send compliance reminder emails
        return {
            "message": f"Compliance reminders sent to {len(users)} users",
            "action": action,
            "user_count": len(users)
        }
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {action}"
        )
