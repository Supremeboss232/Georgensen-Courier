import os
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables (with safe local dev defaults)"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    # Project Info
    PROJECT_NAME: str = "Georgensen Courier Platform"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

    # Database: Defaults to local SQLite if DATABASE_URL is not configured in environment
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./georgensen_courier.db")
    DATABASE_ECHO: bool = False

    # Supabase Settings (loaded strictly from environment variables)
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_JWT_SECRET: Optional[str] = os.getenv("SUPABASE_JWT_SECRET")

    # Security / JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Payment Rails (Payrail & Stripe compatibility)
    PAYRAIL_SECRET_KEY: Optional[str] = os.getenv("PAYRAIL_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY")
    PAYRAIL_API_URL: str = os.getenv("PAYRAIL_API_URL", "https://api.payrail.co/v1")
    PAYRAIL_WEBHOOK_SECRET: Optional[str] = os.getenv("PAYRAIL_WEBHOOK_SECRET") or os.getenv("STRIPE_WEBHOOK_SECRET")
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")

    # Redis & Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

    # Support, Email & SMS
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@georgensencourier.com")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@georgensencourier.com")
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "https://georgensen-courier.onrender.com",
    ]

    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_DIR: str = "./uploads"


settings = Settings()
