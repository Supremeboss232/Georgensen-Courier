"""
Metrics tracking utilities for Prometheus integration.

Provides decorators and middleware for tracking HTTP request metrics,
task execution times, and other performance indicators.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any
from prometheus_client import Counter, Histogram, Gauge
from datetime import datetime

logger = logging.getLogger("metrics")

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Task Metrics
celery_task_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
)

# Database Metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Application Metrics
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

background_jobs_queued = Gauge(
    'background_jobs_queued',
    'Number of queued background jobs'
)

background_jobs_processing = Gauge(
    'background_jobs_processing',
    'Number of background jobs currently processing'
)


# ============================================================================
# TRACKING FUNCTIONS
# ============================================================================

def track_metrics():
    """
    Initialize and return metrics tracking context.
    
    Returns:
        dict: Metrics context with tracking functions
    """
    return {
        "http_requests_total": http_requests_total,
        "http_request_duration_seconds": http_request_duration_seconds,
        "celery_task_total": celery_task_total,
        "celery_task_duration_seconds": celery_task_duration_seconds,
    }


def track_request(method: str, endpoint: str, status: int, duration_ms: float):
    """
    Track HTTP request metrics.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        status: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration_ms / 1000)


def track_task(task_name: str, status: str, duration_seconds: float):
    """
    Track Celery task metrics.
    
    Args:
        task_name: Name of the Celery task
        status: Task status (success, failure, retry)
        duration_seconds: Task execution time in seconds
    """
    celery_task_total.labels(task_name=task_name, status=status).inc()
    if status == "success":
        celery_task_duration_seconds.labels(task_name=task_name).observe(duration_seconds)


def track_query(query_type: str, duration_seconds: float):
    """
    Track database query metrics.
    
    Args:
        query_type: Type of query (select, insert, update, delete)
        duration_seconds: Query execution time in seconds
    """
    db_query_duration_seconds.labels(query_type=query_type).observe(duration_seconds)


# ============================================================================
# DECORATORS
# ============================================================================

def measure_execution_time(operation_name: str) -> Callable:
    """
    Decorator to measure and log execution time of functions.
    
    Args:
        operation_name: Name of the operation for logging
        
    Returns:
        Callable: Decorator function
        
    Usage:
        @measure_execution_time("send_email")
        def send_email(recipient):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{operation_name} completed", extra={
                    "operation": operation_name,
                    "duration_ms": duration * 1000,
                    "status": "success"
                })
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation_name} failed", extra={
                    "operation": operation_name,
                    "duration_ms": duration * 1000,
                    "status": "error",
                    "error": str(e)
                })
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{operation_name} completed", extra={
                    "operation": operation_name,
                    "duration_ms": duration * 1000,
                    "status": "success"
                })
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation_name} failed", extra={
                    "operation": operation_name,
                    "duration_ms": duration * 1000,
                    "status": "error",
                    "error": str(e)
                })
                raise
        
        # Return async or sync wrapper depending on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
