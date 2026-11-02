from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy import inspect, text
import time
import logging
import os

from app.core.config import settings
from app.db.base import Base, engine
from app.api import (
    auth, orders, tracking, partners, admin,
    payments, pod, disputes, customers, ws_tracking,
    support, quotes, logistics, webhooks
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _ensure_schema_columns():
    """Create tables and safely add any newly introduced columns on existing databases."""
    Base.metadata.create_all(bind=engine)
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        if "users" in table_names:
            user_cols = {c["name"] for c in inspector.get_columns("users")}
            with engine.begin() as conn:
                if "profile_data" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN profile_data JSON"))

        if "shipments" in table_names:
            ship_cols = {c["name"] for c in inspector.get_columns("shipments")}
            new_ship_cols = [
                ("base_fare", "FLOAT DEFAULT 0.0"),
                ("distance_charge", "FLOAT DEFAULT 0.0"),
                ("weight_charge", "FLOAT DEFAULT 0.0"),
                ("partner_payout", "FLOAT"),
                ("payment_status", "VARCHAR(50) DEFAULT 'pending'"),
                ("origin_country", "VARCHAR(10) DEFAULT 'CA'"),
                ("destination_country", "VARCHAR(10) DEFAULT 'CA'"),
                ("currency", "VARCHAR(10) DEFAULT 'CAD'"),
                ("estimated_distance_km", "FLOAT DEFAULT 10.0"),
                ("customs_status", "VARCHAR(50) DEFAULT 'cleared'"),
            ]
            with engine.begin() as conn:
                for col_name, col_type in new_ship_cols:
                    if col_name not in ship_cols:
                        conn.execute(text(f"ALTER TABLE shipments ADD COLUMN {col_name} {col_type}"))
    except Exception as e:
        logger.warning(f"Schema column check warning: {e}")


_ensure_schema_columns()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-grade full-stack courier & logistics platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers & Request Logging Middleware
@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(self), microphone=(), camera=(self)"
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {process_time:.3f}s"
    )
    return response


# Mount static files for frontend & uploads
frontend_path = Path(__file__).resolve().parent.parent.parent / "frontend"
uploads_path = Path(settings.UPLOAD_DIR).resolve()
os.makedirs(uploads_path / "pod", exist_ok=True)

if frontend_path.exists():
    if (frontend_path / "css").exists():
        app.mount("/css", StaticFiles(directory=str(frontend_path / "css")), name="css")
    if (frontend_path / "js").exists():
        app.mount("/js", StaticFiles(directory=str(frontend_path / "js")), name="js")
    if (frontend_path / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")

app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# ==================== API ROUTERS ====================
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(tracking.router)
app.include_router(ws_tracking.router)
app.include_router(partners.router)
app.include_router(admin.router)
app.include_router(customers.router)
app.include_router(payments.router)
app.include_router(pod.router)
app.include_router(disputes.router)
app.include_router(support.router)
app.include_router(quotes.router)
app.include_router(logistics.router)
app.include_router(webhooks.router)


# ==================== SYSTEM & HEALTH ENDPOINTS ====================
@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "timestamp": time.time()
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Basic metrics endpoint"""
    return {
        "service": settings.PROJECT_NAME,
        "uptime": "operational",
        "database": "connected"
    }


@app.get("/api/v1", tags=["API Info"])
async def api_info():
    """API version and available endpoints"""
    return {
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "orders": "/api/v1/orders",
            "tracking": "/api/v1/tracking",
            "tracking_ws": "ws://localhost:8000/api/v1/tracking/ws/{tracking_number}",
            "partners": "/api/v1/partners",
            "admin": "/api/v1/admin",
            "customers": "/api/v1/customers",
            "payments": "/api/v1/payments",
            "pod": "/api/v1/pod",
            "disputes": "/api/v1/disputes",
            "quotes": "/api/v1/quotes",
            "logistics": "/api/v1/logistics",
            "support": "/api/v1/support/tickets",
            "webhooks": "/api/v1/webhooks",
        },
        "docs": "/docs"
    }


# ==================== FRONTEND HTML SERVING ====================
@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve landing page"""
    index_path = frontend_path / "pages" / "public" / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


PORTAL_DEFAULTS = {
    "admin": "dashboard",
    "customer": "dashboard",
    "partner": "partner-dashboard",
    "auth": "login",
    "public": "index",
}

PAGE_ALIASES = {
    ("partner", "settings"): "partner-settings",
    ("partner", "dashboard"): "partner-dashboard",
    ("public", "pricing"): "quote",
    ("public", "track"): "tracking",
    ("customer", "shipments"): "orders",
}


@app.get("/{file_path:path}", include_in_schema=False)
async def serve_html(file_path: str):
    """Serve HTML pages from frontend/pages with path traversal protection"""
    clean_path = file_path.strip("/")

    if not clean_path:
        return await serve_index()

    # Never intercept API routes or static asset prefixes
    if clean_path.startswith(("api/", "css/", "js/", "assets/", "uploads/")):
        raise HTTPException(status_code=404, detail="Not found")

    parts = clean_path.split("/")
    section = parts[0]

    if section in ("customer", "admin", "partner", "auth", "public"):
        raw_page = parts[1] if len(parts) > 1 and parts[1] else PORTAL_DEFAULTS[section]
        page = raw_page[:-5] if raw_page.endswith(".html") else raw_page
        page = PAGE_ALIASES.get((section, page), page)
        html_path = frontend_path / "pages" / section / f"{page}.html"
    else:
        page = clean_path[:-5] if clean_path.endswith(".html") else clean_path
        page = PAGE_ALIASES.get(("public", page), page)
        html_path = frontend_path / "pages" / "public" / f"{page}.html"

    try:
        resolved = html_path.resolve()
        if not resolved.is_relative_to(frontend_path.resolve()):
            raise HTTPException(status_code=403, detail="Access denied")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Page not found")

    if resolved.exists() and resolved.is_file():
        return FileResponse(resolved, media_type="text/html")

    raise HTTPException(status_code=404, detail="Page not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
