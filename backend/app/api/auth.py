from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import logging

from app.db.base import get_db
from app.db.models import (
    User, UserRole, Customer, Partner,
    EmailVerification, RefreshToken, AuthAuditLog,
    PasswordReset, LoginAttempt
)
from app.schemas.order import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, verify_token, generate_verification_token,
    hash_token
)
from app.services.email import EmailService
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
ALLOWED_SELF_REGISTER_ROLES = {"customer", "partner"}


def _ensure_role_profile(db: Session, user: User, profile_data: Optional[dict] = None):
    """Ensure Customer or Partner profile record exists for the user."""
    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
    if role_val == "customer":
        existing = db.query(Customer).filter(Customer.user_id == user.id).first()
        if not existing:
            cust = Customer(
                user_id=user.id,
                company_name=user.full_name or "Individual",
                account_type="individual",
                phone=user.phone,
                email_verified=bool(user.is_email_verified),
            )
            db.add(cust)
            db.commit()
    elif role_val in ("partner", "driver"):
        existing = db.query(Partner).filter(Partner.user_id == user.id).first()
        if not existing:
            pdata = profile_data or user.profile_data or {}
            partner = Partner(
                user_id=user.id,
                business_name=pdata.get("business_name") or user.full_name or "Partner Courier",
                business_registration=pdata.get("business_registration") or f"REG-{user.id}-{int(datetime.utcnow().timestamp())}",
                contact_person=user.full_name or "Partner",
                contact_email=user.email,
                contact_phone=user.phone or pdata.get("phone") or "+1-800-555-0199",
                business_address=user.address or pdata.get("service_area") or "Toronto, ON",
                city=user.city or "Toronto",
                state=user.state or "ON",
                postal_code=user.postal_code or "M5V 2T6",
                vehicle_type=pdata.get("vehicle_type", "van"),
                status="approved",
                rating=4.8,
            )
            db.add(partner)
            db.commit()


def check_rate_limit(email: str, ip_address: str, db: Session) -> bool:
    cutoff_time = datetime.utcnow() - timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    failed_attempts = db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.success == False,
        LoginAttempt.created_at > cutoff_time
    ).count()
    return failed_attempts >= MAX_FAILED_ATTEMPTS


def record_login_attempt(email: str, ip_address: str, success: bool, db: Session):
    try:
        attempt = LoginAttempt(email=email, ip_address=ip_address, success=success)
        db.add(attempt)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to record login attempt: {e}")


def log_auth_action(
    user_id: Optional[int],
    action: str,
    ip_address: str,
    user_agent: str,
    status_str: str = "success",
    reason: Optional[str] = None,
    db: Session = None
):
    if not db:
        return
    try:
        audit_log = AuthAuditLog(
            user_id=user_id,
            event_type=action,
            ip_address=ip_address,
            user_agent=user_agent,
            success=(status_str == "success"),
            reason=reason
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Failed to log auth action: {e}")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register new user (restricted to customer or partner roles)"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    requested_role = (user_data.role or "customer").lower().strip()
    if requested_role not in ALLOWED_SELF_REGISTER_ROLES:
        log_auth_action(None, "register", ip_address, user_agent, "failed", f"Blocked role escalation: {requested_role}", db)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is restricted to customer and partner accounts"
        )

    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        log_auth_action(None, "register", ip_address, user_agent, "failed", "Email already registered", db)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    role_enum = UserRole.partner if requested_role == "partner" else UserRole.customer

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=role_enum,
        is_active=True,
        is_email_verified=False,
        profile_data=user_data.profile or {"status": "active", "primary_region": "NA"}
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Ensure role-specific Customer or Partner record is created
    _ensure_role_profile(db, new_user, user_data.profile)

    # Generate email verification token
    verification_token = generate_verification_token()
    email_verification = EmailVerification(
        user_id=new_user.id,
        token=hash_token(verification_token),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(email_verification)
    db.commit()

    try:
        EmailService.send_verification_email(
            email=new_user.email,
            user_name=new_user.full_name,
            verification_token=verification_token
        )
    except Exception as e:
        logger.warning(f"Failed to send verification email: {str(e)}")

    role_str = new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role)
    access_token = create_access_token({"sub": str(new_user.id), "role": role_str})
    refresh_token_str = create_refresh_token({"sub": str(new_user.id)})

    refresh_token_record = RefreshToken(
        user_id=new_user.id,
        token_jti=hash_token(refresh_token_str),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(refresh_token_record)
    db.commit()

    log_auth_action(new_user.id, "register", ip_address, user_agent, "success", None, db)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login with email and password"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    if check_rate_limit(credentials.email, ip_address, db):
        log_auth_action(None, "login", ip_address, user_agent, "failed", "Rate limit exceeded", db)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
        )

    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        record_login_attempt(credentials.email, ip_address, False, db)
        log_auth_action(user.id if user else None, "login", ip_address, user_agent, "failed", "Invalid credentials", db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        record_login_attempt(credentials.email, ip_address, False, db)
        log_auth_action(user.id, "login", ip_address, user_agent, "failed", "User inactive", db)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Ensure role profile exists for legacy users
    _ensure_role_profile(db, user)

    record_login_attempt(credentials.email, ip_address, True, db)

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token({"sub": str(user.id), "role": role_str})
    refresh_token_str = create_refresh_token({"sub": str(user.id)})

    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_jti=hash_token(refresh_token_str),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(refresh_token_record)
    db.commit()

    log_auth_action(user.id, "login", ip_address, user_agent, "success", None, db)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    request: Request,
    refresh_token: Optional[str] = None,
    body: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token (query param or JSON body)"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    token_str = refresh_token or (body.get("refresh_token") if isinstance(body, dict) else None)
    if not token_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh_token is required")

    payload = verify_token(token_str)
    if not payload or payload.get("type") != "refresh":
        log_auth_action(None, "token_refresh", ip_address, user_agent, "failed", "Invalid token", db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        log_auth_action(user_id, "token_refresh", ip_address, user_agent, "failed", "User not found or inactive", db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    new_access_token = create_access_token({"sub": str(user.id), "role": role_str})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    new_token_record = RefreshToken(
        user_id=user.id,
        token_jti=hash_token(new_refresh_token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(new_token_record)
    db.commit()

    log_auth_action(user_id, "token_refresh", ip_address, user_agent, "success", None, db)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_info(
    update_data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile information"""
    for field in ("full_name", "phone", "address", "city", "state", "postal_code"):
        if field in update_data and update_data[field] is not None:
            setattr(current_user, field, update_data[field])
    if "profile_data" in update_data and isinstance(update_data["profile_data"], dict):
        merged = dict(current_user.profile_data or {})
        merged.update(update_data["profile_data"])
        current_user.profile_data = merged
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(
    request: Request,
    refresh_token: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and revoke refresh tokens"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    if refresh_token:
        token_hash = hash_token(refresh_token)
        token_record = db.query(RefreshToken).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.token_jti == token_hash
        ).first()
        if token_record:
            token_record.is_revoked = True
            token_record.revoked_at = datetime.utcnow()
            db.commit()
    else:
        db.query(RefreshToken).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False
        ).update({
            RefreshToken.is_revoked: True,
            RefreshToken.revoked_at: datetime.utcnow()
        })
        db.commit()

    log_auth_action(current_user.id, "logout", ip_address, user_agent, "success", None, db)
    return {"message": "Logged out successfully"}


@router.post("/verify-email")
async def verify_email(
    request: Request,
    token: Optional[str] = None,
    body: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db)
):
    """Verify user email with verification token"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    raw_token = token or (body.get("token") if isinstance(body, dict) else None)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token required")

    token_hash = hash_token(raw_token)
    verification = db.query(EmailVerification).filter(
        EmailVerification.token == token_hash,
        EmailVerification.is_verified == False,
        EmailVerification.expires_at > datetime.utcnow()
    ).first()

    if not verification:
        log_auth_action(None, "email_verified", ip_address, user_agent, "failed", "Invalid or expired token", db)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    verification.is_verified = True
    verification.verified_at = datetime.utcnow()

    user = db.query(User).filter(User.id == verification.user_id).first()
    if user:
        user.is_email_verified = True

    db.commit()
    log_auth_action(verification.user_id, "email_verified", ip_address, user_agent, "success", None, db)
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification_email(
    request: Request,
    email: Optional[str] = None,
    body: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db)
):
    """Resend verification email"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    target_email = email or (body.get("email") if isinstance(body, dict) else None)
    if not target_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")

    user = db.query(User).filter(User.email == target_email).first()
    if not user:
        return {"message": "If email exists, verification link will be sent"}

    if user.is_email_verified:
        return {"message": "Email is already verified"}

    db.query(EmailVerification).filter(
        EmailVerification.user_id == user.id,
        EmailVerification.is_verified == False
    ).delete()

    verification_token = generate_verification_token()
    email_verification = EmailVerification(
        user_id=user.id,
        token=hash_token(verification_token),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(email_verification)
    db.commit()

    try:
        EmailService.send_verification_email(
            email=user.email,
            user_name=user.full_name,
            verification_token=verification_token
        )
    except Exception as e:
        logger.warning(f"Failed to send verification email: {str(e)}")

    log_auth_action(user.id, "resend_verification", ip_address, user_agent, "success", None, db)
    return {"message": "If email exists, verification link will be sent"}


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email: Optional[str] = None,
    body: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db)
):
    """Initiate password reset process"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    target_email = email or (body.get("email") if isinstance(body, dict) else None)
    if not target_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")

    user = db.query(User).filter(User.email == target_email).first()
    if not user:
        log_auth_action(None, "password_reset_request", ip_address, user_agent, "failed", "User not found", db)
        return {"message": "If email exists, password reset link will be sent"}

    db.query(PasswordReset).filter(
        PasswordReset.user_id == user.id,
        PasswordReset.is_used == False
    ).delete()

    reset_token = generate_verification_token()
    password_reset = PasswordReset(
        user_id=user.id,
        token=hash_token(reset_token),
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(password_reset)
    db.commit()

    try:
        EmailService.send_password_reset_email(
            email=user.email,
            user_name=user.full_name,
            reset_token=reset_token
        )
    except Exception as e:
        logger.warning(f"Failed to send password reset email: {str(e)}")

    log_auth_action(user.id, "password_reset_request", ip_address, user_agent, "success", None, db)
    return {"message": "If email exists, password reset link will be sent"}


@router.post("/reset-password")
async def reset_password(
    request: Request,
    token: Optional[str] = None,
    new_password: Optional[str] = None,
    body: Optional[dict] = Body(default=None),
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    raw_token = token or (body.get("token") if isinstance(body, dict) else None)
    raw_password = new_password or (body.get("new_password") if isinstance(body, dict) else None)

    if not raw_token or not raw_password or len(raw_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid token and password (at least 8 characters) are required"
        )

    token_hash = hash_token(raw_token)
    reset_record = db.query(PasswordReset).filter(
        PasswordReset.token == token_hash,
        PasswordReset.is_used == False,
        PasswordReset.expires_at > datetime.utcnow()
    ).first()

    if not reset_record:
        log_auth_action(None, "password_reset", ip_address, user_agent, "failed", "Invalid or expired token", db)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user = db.query(User).filter(User.id == reset_record.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = hash_password(raw_password)
    reset_record.is_used = True
    reset_record.used_at = datetime.utcnow()

    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.is_revoked == False
    ).update({
        RefreshToken.is_revoked: True,
        RefreshToken.revoked_at: datetime.utcnow()
    })
    db.commit()

    log_auth_action(user.id, "password_reset", ip_address, user_agent, "success", None, db)
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    request: Request,
    old_password: Optional[str] = None,
    new_password: Optional[str] = None,
    body: Optional[dict] = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    curr_pwd = old_password or (body.get("old_password") or body.get("current_password") if isinstance(body, dict) else None)
    next_pwd = new_password or (body.get("new_password") if isinstance(body, dict) else None)

    if not curr_pwd or not next_pwd:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both current and new passwords are required")

    if not verify_password(curr_pwd, current_user.hashed_password):
        log_auth_action(current_user.id, "password_change", ip_address, user_agent, "failed", "Invalid old password", db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid current password"
        )

    if len(next_pwd) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )

    current_user.hashed_password = hash_password(next_pwd)
    db.commit()

    log_auth_action(current_user.id, "password_change", ip_address, user_agent, "success", None, db)
    return {"message": "Password changed successfully"}
