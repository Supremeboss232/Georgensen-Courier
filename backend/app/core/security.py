from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import uuid

# Password hashing using argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class SecurityUtils:
    """Security utilities for JWT and password management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token (short-lived, typically 1 hour)"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Add unique ID for token revocation
        to_encode.update({
            "exp": expire,
            "jti": str(uuid.uuid4()),  # JWT ID - unique identifier
            "type": "access"
        })
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> tuple[str, str]:
        """Create JWT refresh token (long-lived, typically 7 days)
        
        Returns:
            Tuple of (token, jti) - token is the JWT, jti is the unique ID
        """
        jti = str(uuid.uuid4())
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({
            "exp": expire,
            "jti": jti,
            "type": "refresh"
        })
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt, jti
    
    @staticmethod
    def create_email_verification_token() -> str:
        """Generate a one-time email verification token"""
        return str(uuid.uuid4())
    
    @staticmethod
    def create_password_reset_token() -> str:
        """Generate a one-time password reset token"""
        return str(uuid.uuid4())
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def validate_token_type(token: str, expected_type: str) -> bool:
        """Validate that token is of expected type (access, refresh, etc)"""
        payload = SecurityUtils.decode_token(token)
        if not payload:
            return False
        return payload.get("type") == expected_type
    
    @staticmethod
    def is_password_strong(password: str) -> tuple[bool, Optional[str]]:
        """Validate password strength
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < 12:
            return False, "Password must be at least 12 characters"
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        return True, None
