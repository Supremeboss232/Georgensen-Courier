from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.base import engine, SessionLocal, Base
from app.db.models import User
from app.db.models.user import UserRole
from app.core.security import SecurityUtils
from app.api.routes import auth, orders, tracking, admin, admin_new_endpoints
from app.api import ws_tracking, pod, payments, disputes, webhooks, logistics, support, customers, partners
import os
from pathlib import Path
import logging

# Observability & Background Jobs
from app.core.logging_config import setup_json_logging
from app.celery_app import celery_app
from app.core.metrics import track_metrics
import threading


# Initialize FastAPI app
app = FastAPI(
    title="Georgensen Courier API",
    description="Professional delivery management platform",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve static files from organized frontend structure
frontend_path = Path(__file__).parent.parent.parent / "frontend"

# Mount static file directories from organized structure
static_dirs = {
    "/css": ("css", "css"),
    "/js": ("js", "js"),
    "/assets": ("assets", "assets"),
    "/components": ("components", "components"),
    "/img": ("assets", "img"),  # Alias for backwards compatibility
    "/src/components": ("components", "src_components"),  # For legacy paths
}

for mount_path, (dir_name, mount_name) in static_dirs.items():
    dir_path = frontend_path / dir_name
    if dir_path.exists():
        app.mount(mount_path, StaticFiles(directory=str(dir_path)), name=mount_name)
        print(f"[OK] Mounted {mount_path} -> {dir_path}")
    else:
        print(f"[FAIL] Directory not found: {dir_path}")

print(f"[OK] Frontend path configured: {frontend_path}")


# Serve index.html for root path
@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serve frontend index page"""
    index_path = frontend_path / "pages" / "public" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Welcome to Georgensen Courier API", "version": "1.0.0", "docs": "/api/docs"}


# Catch-all to serve HTML files from pages directory (public pages)
@app.get("/{file_path:path}", tags=["Frontend"])
async def serve_html(file_path: str):
    """Serve HTML files from organized pages directories"""
    # Don't intercept API routes
    if file_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Map routing to pages directory
    # Examples: /customer/dashboard → pages/customer/dashboard.html
    #           /auth/login → pages/auth/login.html
    #           /about → pages/public/about.html
    
    parts = file_path.split("/")
    
    # Check if it's a known section (customer, admin, partner, auth)
    if parts[0] in ["customer", "admin", "partner", "auth"]:
        section = parts[0]
        page = "/".join(parts[1:]) if len(parts) > 1 else "index"
    else:
        # Default to public pages
        section = "public"
        page = file_path
    
    # Try to find the file in pages directory
    file_full_path = frontend_path / "pages" / section / page
    
    # Add .html extension if needed
    if not file_full_path.exists() and not page.endswith((".css", ".js", ".png", ".jpg", ".gif", ".svg", ".ico")):
        file_full_path = frontend_path / "pages" / section / f"{page}.html"
    
    if file_full_path.exists() and file_full_path.is_file():
        return FileResponse(file_full_path)
    
    raise HTTPException(status_code=404, detail="File not found")


# Include routers
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(partners.router)
app.include_router(tracking.router)
app.include_router(ws_tracking.router)  # Real-time tracking WebSocket
app.include_router(pod.router)  # Proof of delivery uploads
app.include_router(payments.router)  # Payment processing
app.include_router(disputes.router)  # Dispute management
app.include_router(admin.router)
app.include_router(admin_new_endpoints.router)  # Enhanced admin endpoints for regional oversight
app.include_router(customers.router)
app.include_router(logistics.router)  # Logistics & Chain of Custody operations

# Import quotes router for Canada-global pricing
from app.api import quotes
app.include_router(quotes.router)  # Quote calculation with regional pricing

# Include support router for contact forms and support tickets
app.include_router(support.router)  # Support & contact form submissions


@app.on_event("startup")
async def startup_event():
    """Initialize database, logging, and background jobs"""
    
    # Setup JSON logging for structured logs
    setup_json_logging(app_name="georgensen-api", level=settings.LOG_LEVEL)
    logger = logging.getLogger("startup")
    
    # Create tables (fast if they already exist)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready", extra={"component": "database"})
    
    # Initialize Celery (non-blocking)
    celery_app.conf.update(
        broker_url=settings.CELERY_BROKER_URL,
        result_backend=settings.CELERY_RESULT_BACKEND,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC'
    )
    logger.info("Celery configured", extra={
        "broker": settings.CELERY_BROKER_URL.split("://")[0]
    })
    
    # Create default admin user in background (non-blocking)
    def create_admin_user():
        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
            if not admin:
                admin_user = User(
                    email=settings.FIRST_SUPERUSER,
                    hashed_password=SecurityUtils.get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                    full_name="System Admin",
                    phone="+234000000000",
                    role=UserRole.admin,
                    is_active=True,
                    is_superuser=True,
                    is_email_verified=True
                )
                db.add(admin_user)
                db.commit()
                logger.info(f"Admin user created", extra={"email": settings.FIRST_SUPERUSER})
            else:
                logger.info(f"Admin user exists", extra={"email": settings.FIRST_SUPERUSER})
        except Exception as e:
            logger.error(f"Failed to create admin user: {str(e)}")
        finally:
            db.close()
    
    # Run admin creation in background thread
    admin_thread = threading.Thread(target=create_admin_user, daemon=True)
    admin_thread.start()
    
    logger.info("Application startup complete", extra={"status": "ready"})


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger = logging.getLogger("shutdown")
    logger.info("Application shutting down", extra={"status": "stopping"})
    
    # Graceful Celery shutdown
    celery_app.control.shutdown()
    logger.info("Celery task queue stopped", extra={"graceful": True})


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Georgensen Courier API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Georgensen Courier API",
        "version": "1.0.0"
    }


@app.get("/metrics", tags=["Observability"])
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, REGISTRY, CollectorRegistry
    metrics_output = generate_latest(REGISTRY)
    return PlainTextResponse(
        content=metrics_output.decode('utf-8'),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@app.get("/api/v1", tags=["API Info"])
async def api_info():
    """API information"""
    return {
        "name": "Georgensen Courier API",
        "version": "1.0.0",
        "base_url": "/api/v1",
        "endpoints": {
            "auth": "/auth",
            "orders": "/orders",
            "partners": "/partners",
            "tracking": "/tracking",
            "admin": "/admin"
        },
        "documentation": "/api/docs"
    }


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
