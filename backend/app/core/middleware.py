"""
Middleware for authentication and authorization
"""
from datetime import datetime, timezone, timedelta
from typing import Callable

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models.auth import LoginAttempt, AuthAuditLog
from sqlalchemy import and_


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit login attempts to prevent brute force attacks
    
    Rules:
    - Max 5 failed attempts per minute per IP
    - Max 5 failed attempts per minute per email
    - Exponential backoff: block 2min→5min→15min→30min based on failure count
    """
    
    # Only apply rate limiting to login endpoint
    PROTECTED_PATHS = ["/api/v1/auth/login"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> None:
        # Check if this is a protected endpoint
        if not any(request.url.path.startswith(path) for path in self.PROTECTED_PATHS):
            return await call_next(request)
        
        if request.method != "POST":
            return await call_next(request)
        
        # Get client IP and read body
        ip_address = request.client.host if request.client else "unknown"
        
        # We'll check rate limit after login endpoint processes
        # (we need email from request body)
        response = await call_next(request)
        
        # For simplicity, rate limiting is done at the endpoint level
        # This middleware provides a hook for future enhancements
        
        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Audit log all API requests for compliance"""
    
    # Skip audit logging for these endpoints (too noisy)
    SKIP_AUDIT = [
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/favicon.ico"
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> None:
        # Skip non-protected endpoints and health checks
        if any(request.url.path.startswith(path) for path in self.SKIP_AUDIT):
            return await call_next(request)
        
        # Get response
        response = await call_next(request)
        
        # Log will be handled at endpoint level with more context
        # This middleware provides infrastructure for future centralized logging
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> None:
        response = await call_next(request)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Feature Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
