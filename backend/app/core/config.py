from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Georjensen API"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database
    # Supabase PostgreSQL
    # Format: postgresql://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql://postgres.vzklbpudzszvzqdltmnv:QBln5wFtsxTqD6o6@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    
    # Supabase Configuration
    SUPABASE_URL: str = "https://vzklbpudzszvzqdltmnv.supabase.co"
    SUPABASE_ANON_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6a2xicHVkenN6dnpxZGx0bW52Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY1MTk2NDYsImV4cCI6MjA5MjA5NTY0Nn0.hq5zick18MWYX1wZbzATeLUzmKhQbQG_RDT4xUppoA0"
    SUPABASE_SERVICE_ROLE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ6a2xicHVkenN6dnpxZGx0bW52Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjUxOTY0NiwiZXhwIjoyMDkyMDk1NjQ2fQ.dcBm81J8xPqZj4hYz_rha3KygRl_iSm5MOoZmPXZZR4"
    SUPABASE_JWT_SECRET: str = "Vb2A+uCsTKiriRl0F9vQXLwVrbH9tpwuJRdQ2ipBS4tzI979XNBQKBr9wItZoXt3bmFCLzxyHSRgXttPms5H7A=="
    
    # Security
    SECRET_KEY: str = "georjensen-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 24 * 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:4000", "http://localhost:3000", "http://127.0.0.1:4000"]
    BACKEND_CORS_ORIGINS: list = ["http://localhost:4000"]
    
    # Features
    ENABLE_NOTIFICATIONS: bool = True
    ENABLE_PAYMENTS: bool = False
    
    # Email Configuration
    MAIL_FROM: str = "noreply@georjensen.app"
    MAIL_FROM_NAME: str = "Georgensen Courier"
    SMTP_HOST: str = "smtp.gmail.com"  # Change to SendGrid, Mailgun, or your SMTP provider
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"  # Set via environment variable
    SMTP_PASSWORD: str = "your-app-password"  # Set via environment variable (use app-specific password for Gmail)
    
    # Webhook Secrets (for signature verification)
    # Payment webhooks
    STRIPE_WEBHOOK_SECRET: Optional[str] = None  # Set via environment variable
    
    # Stripe Keys
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    
    # Carrier webhooks (FedEx, UPS)
    FEDEX_WEBHOOK_SECRET: Optional[str] = None  # Set via environment variable - SharedSecret from FedEx Developer Portal
    UPS_WEBHOOK_SECRET: Optional[str] = None  # Set via environment variable - OAuth ClientSecret from UPS Developer Portal
    
    # Communication platform webhooks
    SENDGRID_WEBHOOK_KEY: Optional[str] = None  # Set via environment variable
    TWILIO_WEBHOOK_TOKEN: Optional[str] = None  # Set via environment variable
    
    # Admin
    FIRST_SUPERUSER: str = "admin@example.com"
    FIRST_SUPERUSER_EMAIL: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "Admin123!"
    
    # ==================== BACKGROUND JOBS & OBSERVABILITY ====================
    
    # Celery Configuration (Task Queue)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    
    # Redis Configuration (Cache & Message Broker)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 2
    REDIS_PASSWORD: Optional[str] = None
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "json"  # json or standard
    
    # Sentry Configuration (Error Tracking)
    SENTRY_DSN: Optional[str] = None  # Set to enable error tracking
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of requests
    
    # Prometheus Configuration (Metrics)
    PROMETHEUS_PORT: int = 8000
    PROMETHEUS_METRICS_PATH: str = "/metrics"
    
    # OpenTelemetry Configuration (Distributed Tracing)
    OTEL_ENABLED: bool = False
    OTEL_JAEGER_AGENT_HOST: str = "localhost"
    OTEL_JAEGER_AGENT_PORT: int = 6831
    
    # Flower Configuration (Celery Monitoring)
    FLOWER_PORT: int = 5555
    FLOWER_PERSISTENT: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env file

settings = Settings()

