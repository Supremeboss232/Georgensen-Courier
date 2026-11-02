from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import hashlib
import secrets
import uuid

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class SecurityUtils:
    """Security utilities for JWT and password management"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "jti": str(uuid.uuid4()),
            "type": "access"
        })
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict) -> tuple[str, str]:
        """Create JWT refresh token and return (token, jti)"""
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
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_password_reset_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            return None

    @staticmethod
    def validate_token_type(token: str, expected_type: str) -> bool:
        payload = SecurityUtils.decode_token(token)
        if not payload:
            return False
        return payload.get("type") == expected_type

    @staticmethod
    def is_password_strong(password: str) -> tuple[bool, Optional[str]]:
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        return True, None


# Module-level functions used across auth.py, deps.py, and tests
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return SecurityUtils.verify_password(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return SecurityUtils.get_password_hash(password)


def get_password_hash(password: str) -> str:
    return SecurityUtils.get_password_hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return SecurityUtils.create_access_token(data, expires_delta)


def create_refresh_token(data: dict) -> str:
    token, _ = SecurityUtils.create_refresh_token(data)
    return token


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    return SecurityUtils.decode_token(token)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    return SecurityUtils.decode_token(token)


def generate_verification_token() -> str:
    return SecurityUtils.create_email_verification_token()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
