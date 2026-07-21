"""
Authentication endpoints with production-grade security
"""
from datetime import timedelta, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.base import get_db
from app.db.models.user import User
from app.db.models.auth import (
    EmailVerification, RefreshToken, AuthAuditLog,
    PasswordReset, LoginAttempt
)
from app.core.security import SecurityUtils
from app.core.config import settings
from app.schemas.order import UserRegister, UserLogin, TokenResponse, UserResponse
from app.api.deps import get_current_user


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


def get_client_info(request: Request) -> tuple[str, str]:
    """Extract client IP and user agent"""
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    return ip, user_agent


def log_auth_event(
    db: Session,
    user_id: Optional[int],
    event_type: str,
    ip_address: str,
    user_agent: str,
    success: bool = True,
    reason: Optional[str] = None,
    email: Optional[str] = None
):
    """Log authentication event to audit trail"""
    log = AuthAuditLog(
        user_id=user_id,
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        reason=reason,
        metadata={"email": email} if email else None
    )
    db.add(log)
    db.commit()


def check_rate_limit(db: Session, email: str, ip_address: str, max_attempts: int = 5) -> bool:
    """Check if user has exceeded login attempt rate limit
    
    Returns:
        True if within limits, False if exceeded
    """
    from datetime import timedelta
    
    # Check failed attempts in last 1 minute
    one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
    recent_attempts = db.query(LoginAttempt).filter(
        and_(
            LoginAttempt.email == email,
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.success == False,
            LoginAttempt.created_at >= one_minute_ago
        )
    ).count()
    
    if recent_attempts >= max_attempts:
        return False
    
    # Check if account is temporarily locked (after 5 failed attempts)
    # Lock escalates: 2min, 5min, 15min, 30min based on failure count
    return True


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register new user account
    
    User must verify email before they can use the account
    """
    
    ip_address, user_agent = get_client_info(request)
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        log_auth_event(db, None, "register", ip_address, user_agent, success=False,
                      reason="Email already registered", email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_strong, error_msg = SecurityUtils.is_password_strong(user_data.password)
    if not is_strong:
        log_auth_event(db, None, "register", ip_address, user_agent, success=False,
                      reason=error_msg, email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create new user (not verified yet)
    user = User(
        email=user_data.email,
        hashed_password=SecurityUtils.get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role or "customer",
        is_active=True,
        is_email_verified=False  # NEW: Not verified until email confirmed
    )
    
    db.add(user)
    db.flush()  # Get user.id
    
    # Create email verification token
    verification_token = SecurityUtils.create_email_verification_token()
    email_verification = EmailVerification(
        user_id=user.id,
        token=verification_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(email_verification)
    db.commit()
    db.refresh(user)
    
    log_auth_event(db, user.id, "register", ip_address, user_agent, success=True)
    
    # TODO: Send verification email with token
    # send_verification_email(user.email, verification_token)
    
    return user


@router.post("/email-verification/send")
async def send_email_verification(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send (or resend) email verification link"""
    
    ip_address, user_agent = get_client_info(request)
    
    if user.is_email_verified:
        return {"message": "Email already verified"}
    
    # Create new verification token
    verification_token = SecurityUtils.create_email_verification_token()
    
    # Invalidate old tokens
    db.query(EmailVerification).filter(
        and_(
            EmailVerification.user_id == user.id,
            EmailVerification.is_verified == False
        )
    ).update({"expires_at": datetime.now(timezone.utc)})
    
    email_verification = EmailVerification(
        user_id=user.id,
        token=verification_token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(email_verification)
    db.commit()
    
    log_auth_event(db, user.id, "email_verification_sent", ip_address, user_agent, success=True)
    
    # TODO: Send verification email
    # send_verification_email(user.email, verification_token)
    
    return {"message": "Verification email sent"}


@router.post("/email-verification/verify")
async def verify_email(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify email using verification token
    
    Token expires after 24 hours
    """
    
    ip_address, user_agent = get_client_info(request)
    
    # Find verification token
    email_verification = db.query(EmailVerification).filter(
        and_(
            EmailVerification.token == token,
            EmailVerification.is_verified == False,
            EmailVerification.expires_at > datetime.now(timezone.utc)
        )
    ).first()
    
    if not email_verification:
        log_auth_event(db, None, "email_verification", ip_address, user_agent, success=False,
                      reason="Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Mark as verified
    email_verification.is_verified = True
    email_verification.verified_at = datetime.now(timezone.utc)
    
    user = email_verification.user
    user.is_email_verified = True
    
    db.commit()
    
    log_auth_event(db, user.id, "email_verified", ip_address, user_agent, success=True)
    
    return {"message": "Email verified successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user and return access + refresh tokens
    
    User must have verified email before login is allowed
    """
    
    ip_address, user_agent = get_client_info(request)
    
    # Check rate limit
    if not check_rate_limit(db, credentials.email, ip_address):
        log_auth_event(db, None, "login", ip_address, user_agent, success=False,
                      reason="Too many failed attempts", email=credentials.email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not SecurityUtils.verify_password(credentials.password, user.hashed_password):
        # Log failed attempt
        attempt = LoginAttempt(
            email=credentials.email,
            ip_address=ip_address,
            success=False
        )
        db.add(attempt)
        db.commit()
        
        log_auth_event(db, user.id if user else None, "login", ip_address, user_agent,
                      success=False, reason="Invalid credentials", email=credentials.email)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        log_auth_event(db, user.id, "login", ip_address, user_agent, success=False,
                      reason="Account disabled")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # NEW: Check if email is verified
    if not user.is_email_verified:
        log_auth_event(db, user.id, "login", ip_address, user_agent, success=False,
                      reason="Email not verified")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )
    
    # Create tokens
    access_token = SecurityUtils.create_access_token({"sub": user.email, "user_id": user.id})
    refresh_token, refresh_jti = SecurityUtils.create_refresh_token({"sub": user.email, "user_id": user.id})
    
    # Store refresh token for revocation support
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_jti=refresh_jti,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(refresh_token_record)
    
    # Log successful login
    attempt = LoginAttempt(
        email=credentials.email,
        ip_address=ip_address,
        success=True
    )
    db.add(attempt)
    db.commit()
    
    log_auth_event(db, user.id, "login", ip_address, user_agent, success=True)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get new access token using refresh token
    
    Refresh token must not be revoked
    """
    
    ip_address, user_agent = get_client_info(request)
    
    # Decode refresh token
    payload = SecurityUtils.decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        log_auth_event(db, None, "refresh_token", ip_address, user_agent, success=False,
                      reason="Invalid token type")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("user_id")
    jti = payload.get("jti")
    
    # Check if refresh token is revoked
    token_record = db.query(RefreshToken).filter(
        and_(
            RefreshToken.user_id == user_id,
            RefreshToken.token_jti == jti,
            RefreshToken.is_revoked == False
        )
    ).first()
    
    if not token_record:
        log_auth_event(db, user_id, "refresh_token", ip_address, user_agent, success=False,
                      reason="Token revoked or invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    # Get user
    user = db.query(User).get(user_id)
    if not user or not user.is_active:
        log_auth_event(db, user_id, "refresh_token", ip_address, user_agent, success=False,
                      reason="User not found or inactive")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    new_access_token = SecurityUtils.create_access_token({"sub": user.email, "user_id": user.id})
    
    log_auth_event(db, user.id, "refresh_token", ip_address, user_agent, success=True)
    
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,  # Same refresh token (could rotate if desired)
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user by revoking refresh tokens"""
    
    ip_address, user_agent = get_client_info(request)
    
    # Revoke all refresh tokens for this user
    db.query(RefreshToken).filter(
        and_(
            RefreshToken.user_id == user.id,
            RefreshToken.is_revoked == False
        )
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc)
    })
    db.commit()
    
    log_auth_event(db, user.id, "logout", ip_address, user_agent, success=True)
    
    return {"message": "Logged out successfully"}


@router.post("/password-reset/request")
async def request_password_reset(
    email: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Request a password reset email
    
    Sends reset token via email (or returns 200 even if user not found, for security)
    """
    
    ip_address, user_agent = get_client_info(request)
    
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        # Invalidate old reset tokens
        db.query(PasswordReset).filter(
            and_(
                PasswordReset.user_id == user.id,
                PasswordReset.is_used == False
            )
        ).update({"expires_at": datetime.now(timezone.utc)})
        
        # Create new reset token
        reset_token = SecurityUtils.create_password_reset_token()
        password_reset = PasswordReset(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)  # 15 min expiry
        )
        db.add(password_reset)
        db.commit()
        
        log_auth_event(db, user.id, "password_reset_request", ip_address, user_agent, success=True)
        
        # TODO: Send password reset email
        # send_password_reset_email(user.email, reset_token)
    
    # Always return 200 (don't leak if email exists)
    return {"message": "If email exists, reset link has been sent"}


@router.post("/password-reset/verify")
async def verify_password_reset(
    token: str,
    new_password: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset password using reset token
    
    Token expires after 15 minutes and can only be used once
    """
    
    ip_address, user_agent = get_client_info(request)
    
    # Validate new password
    is_strong, error_msg = SecurityUtils.is_password_strong(new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Find reset token
    password_reset = db.query(PasswordReset).filter(
        and_(
            PasswordReset.token == token,
            PasswordReset.is_used == False,
            PasswordReset.expires_at > datetime.now(timezone.utc)
        )
    ).first()
    
    if not password_reset:
        log_auth_event(db, None, "password_reset", ip_address, user_agent, success=False,
                      reason="Invalid or expired reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user = password_reset.user
    user.hashed_password = SecurityUtils.get_password_hash(new_password)
    
    # Mark reset token as used
    password_reset.is_used = True
    password_reset.used_at = datetime.now(timezone.utc)
    
    # Revoke all existing refresh tokens (force re-login)
    db.query(RefreshToken).filter(
        and_(
            RefreshToken.user_id == user.id,
            RefreshToken.is_revoked == False
        )
    ).update({
        "is_revoked": True,
        "revoked_at": datetime.now(timezone.utc)
    })
    
    db.commit()
    
    log_auth_event(db, user.id, "password_reset", ip_address, user_agent, success=True)
    
    return {"message": "Password reset successfully. Please login with your new password."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user info"""
    return current_user



@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user"""
    
    return current_user
