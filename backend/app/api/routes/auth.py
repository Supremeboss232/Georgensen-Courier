from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.db.models import User, Handler, HandlerType, HandlerStatus
from app.core.security import SecurityUtils
from app.schemas.order import UserRegister, UserLogin, TokenResponse, UserResponse
from app.api.deps import get_current_user


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register new user account - supports both customers and delivery partners"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=SecurityUtils.get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role or "customer",
        is_active=True
    )
    
    db.add(user)
    db.flush()  # Flush to get user.id without committing
    
    # If partner role, create handler record for logistics tracking
    if user_data.role == "partner" and user_data.profile:
        profile = user_data.profile
        try:
            handler = Handler(
                user_id=user.id,
                full_name=user_data.full_name,
                email=user_data.email,
                phone=user_data.phone or "",
                handler_type=HandlerType.driver,
                hub_id=1,  # Default to hub 1 until assigned
                status=HandlerStatus.active,
                license_number=profile.get("license_number"),
                license_category=profile.get("license_category"),
                notes=f"Registered as delivery partner with vehicle: {profile.get('vehicle_type')}"
            )
            db.add(handler)
        except Exception as e:
            # If handler creation fails, continue with user creation
            print(f"Warning: Could not create handler record: {str(e)}")
    
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return tokens"""
    
    print(f"🔐 LOGIN ATTEMPT: email={credentials.email}")
    
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        print(f"❌ User not found: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not SecurityUtils.verify_password(credentials.password, user.hashed_password):
        print(f"❌ Password verification failed for: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create tokens
    access_token = SecurityUtils.create_access_token({"sub": user.email})
    refresh_token, _ = SecurityUtils.create_refresh_token({"sub": user.email})
    
    print(f"✅ Login successful: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "is_active": user.is_active,
            "created_at": user.created_at
        }
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    token_data: dict,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required"
        )
    
    payload = SecurityUtils.decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user"
        )
    
    # Create new access token
    new_access_token = SecurityUtils.create_access_token({"sub": email})
    
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user"""
    
    return current_user


@router.post("/forgot-password")
async def forgot_password(
    data: dict,
    db: Session = Depends(get_db)
):
    """
    Request password reset link
    Triggers async Celery task to send email without blocking response
    """
    import uuid
    from datetime import datetime, timedelta
    from app.db.models import PasswordReset
    from app.services.email_service import send_password_reset_email
    
    email = data.get("email", "").strip()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    
    # For security: don't reveal if email exists or not
    # Send success response either way to prevent email enumeration attacks
    if user:
        try:
            # Generate secure reset token
            reset_token = str(uuid.uuid4())
            
            # Create password reset record
            reset_record = PasswordReset(
                user_id=user.id,
                token=reset_token,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(reset_record)
            db.commit()
            
            # Trigger async Celery task to send email
            # This returns immediately without waiting for email delivery
            try:
                send_password_reset_email.delay(
                    user.email,
                    user.full_name,
                    reset_token
                )
            except Exception as e:
                print(f"Warning: Could not queue email task: {str(e)}")
                # Continue anyway - user can still reset if task fails
        except Exception as e:
            print(f"Error creating password reset record: {str(e)}")
    
    # Always return success to prevent email enumeration attacks
    return {
        "message": "If an account exists with this email, you will receive a password reset link. Check your email and click the link within 24 hours.",
        "status": "success"
    }


@router.post("/reset-password")
async def reset_password(
    data: dict,
    db: Session = Depends(get_db)
):
    """
    Reset password using token from reset link
    """
    from app.db.models import PasswordReset
    from datetime import datetime
    
    token = data.get("token", "").strip()
    new_password = data.get("password", "").strip()
    
    if not token or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token and password are required"
        )
    
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Find valid reset token
    reset_record = db.query(PasswordReset).filter(
        PasswordReset.token == token,
        PasswordReset.expires_at > datetime.utcnow(),
        PasswordReset.is_used == False
    ).first()
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token"
        )
    
    # Update user password
    user = reset_record.user
    user.hashed_password = SecurityUtils.get_password_hash(new_password)
    
    # Mark reset token as used
    reset_record.is_used = True
    reset_record.used_at = datetime.utcnow()
    
    db.add(user)
    db.add(reset_record)
    db.commit()
    
    return {
        "message": "Password reset successfully. You can now login with your new password.",
        "status": "success"
    }


@router.post("/verify-email")
async def verify_email(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify email using 6-digit code or token
    User must be authenticated (received code via email after registration)
    """
    from app.db.models import EmailVerification
    from datetime import datetime
    
    code = data.get("code", "").strip()
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code is required"
        )
    
    # The code should be a token (we treat the first 6 chars as the code)
    # In a real world scenario, you might generate a 6-digit OTP
    # For now, we'll search for a verification token that matches or starts with the code
    
    verification = db.query(EmailVerification).filter(
        EmailVerification.user_id == current_user.id,
        EmailVerification.is_verified == False,
        EmailVerification.expires_at > datetime.utcnow()
    ).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No pending verification found or token expired"
        )
    
    # Check if code matches the token (in this case, we accept the full token)
    # In production, you'd generate/validate a 6-digit OTP separately
    if code.lower() != verification.token.lower()[:6]:
        # Try exact match as fallback
        if code != verification.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
    
    # Mark verification as complete
    verification.is_verified = True
    verification.verified_at = datetime.utcnow()
    
    # Update user status
    current_user.is_email_verified = True
    
    db.add(verification)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    # Create new tokens for the verified user
    access_token = SecurityUtils.create_access_token({"sub": current_user.email})
    refresh_token, _ = SecurityUtils.create_refresh_token({"sub": current_user.email})
    
    return {
        "status": "success",
        "message": "Email verified successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role
        }
    }


@router.post("/resend-verification")
async def resend_verification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resend verification email to current user
    User must be authenticated
    """
    from app.db.models import EmailVerification
    from app.services.email_service import send_verification_email
    import uuid
    from datetime import datetime, timedelta
    
    # Check if user already verified
    if current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Check if there's an existing unverified verification record
    existing = db.query(EmailVerification).filter(
        EmailVerification.user_id == current_user.id,
        EmailVerification.is_verified == False
    ).first()
    
    # Delete old verification if exists
    if existing:
        db.delete(existing)
        db.commit()
    
    try:
        # Generate new verification token
        verification_token = str(uuid.uuid4())
        
        # Create new verification record
        verification = EmailVerification(
            user_id=current_user.id,
            token=verification_token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(verification)
        db.commit()
        
        # Send verification email via async task
        try:
            send_verification_email.delay(
                current_user.email,
                current_user.full_name,
                verification_token
            )
        except Exception as e:
            print(f"Warning: Could not queue verification email task: {str(e)}")
            # Continue anyway - user can still verify if task fails
        
        return {
            "status": "success",
            "message": "Verification code sent to your email. Please check your inbox."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create verification record"
        )
