"""
Structured logging configuration with JSON format
Enables log aggregation and centralized monitoring

Usage:
    import logging
    logger = logging.getLogger(__name__)
    logger.info("User logged in", extra={"user_id": 123, "duration_ms": 45})
"""

import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from functools import wraps

# ============================================================================
# JSON LOG FORMATTER
# ============================================================================

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing by log aggregation services"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Convert log record to JSON"""
        
        # Build log object
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields (passed via extra={...})
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        if hasattr(record, "ip_address"):
            log_obj["ip_address"] = record.ip_address
        if hasattr(record, "endpoint"):
            log_obj["endpoint"] = record.endpoint
        if hasattr(record, "error_code"):
            log_obj["error_code"] = record.error_code
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)


# ============================================================================
# LOGGER SETUP
# ============================================================================

def setup_json_logging(app_name: str = "georgensen-courier", level: str = "INFO"):
    """
    Configure JSON logging for the application.
    
    Args:
        app_name: Application name to include in logs
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Root logger
    root_logger = logging.getLogger()
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # JSON formatter
    json_formatter = JsonFormatter()
    
    # Console handler (stream to stdout for Docker/K8s)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(json_formatter)
    
    # Remove default handlers
    root_logger.handlers = []
    
    # Add JSON handler
    root_logger.addHandler(console_handler)
    
    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return root_logger



# ============================================================================
# REQUEST LOGGING MIDDLEWARE
# ============================================================================

def add_request_context(func):
    """Decorator to add request context (user_id, request_id, duration)"""
    
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        import uuid
        
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        
        # Start timer
        start_time = time.time()
        
        # Extract user_id if authenticated
        user_id = None
        if hasattr(request, "user"):
            user_id = getattr(request.user, "id", None)
        
        # Extract client IP
        ip_address = request.client.host if request.client else "unknown"
        
        # Execute function
        try:
            response = await func(request, *args, **kwargs)
        except Exception as e:
            # Log error with context
            duration_ms = (time.time() - start_time) * 1000
            logger = logging.getLogger(__name__)
            logger.error(
                f"Request failed: {func.__name__}",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "ip_address": ip_address,
                }
            )
            raise
        
        # Log success
        duration_ms = (time.time() - start_time) * 1000
        logger = logging.getLogger(__name__)
        logger.info(
            f"Request completed: {func.__name__}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": getattr(response, "status_code", 200),
                "duration_ms": round(duration_ms, 2),
                "ip_address": ip_address,
            }
        )
        
        return response
    
    return wrapper


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Initialize logging
    logger = setup_json_logging()
    
    # Example 1: Basic log
    logger.info("Application started")
    
    # Example 2: Log with context
    logger.info(
        "User logged in successfully",
        extra={
            "user_id": 123,
            "ip_address": "192.168.1.1",
            "duration_ms": 45.2,
        }
    )
    
    # Example 3: Log warning
    logger.warning(
        "High memory usage detected",
        extra={
            "memory_percent": 85.5,
            "threshold": 80,
        }
    )
    
    # Example 4: Log error
    try:
        raise ValueError("Invalid shipment data")
    except ValueError as e:
        logger.error(
            "Failed to create shipment",
            extra={
                "user_id": 456,
                "error_code": "INVALID_DATA",
            },
            exc_info=True
        )

# ============================================================================
# CELERY TASK LOGGER
# ============================================================================

def create_task_logger(task_name: str, task_id: str) -> logging.Logger:
    """
    Create a logger for Celery tasks with task context.
    
    Args:
        task_name: Name of the Celery task
        task_id: Unique task ID from Celery
        
    Returns:
        logging.Logger: Configured logger with task context
        
    Usage:
        logger = create_task_logger("send_email", self.request.id)
        logger.info("Task started", extra={"recipient": "user@example.com"})
    """
    logger = logging.getLogger(f"celery.{task_name}")
    
    # Monkey-patch the logger to add task_id and task_name to all logs
    original_makeRecord = logger.makeRecord
    
    def makeRecord_with_context(*args, **kwargs):
        """Add task context to all log records"""
        record = original_makeRecord(*args, **kwargs)
        record.task_id = task_id
        record.task_name = task_name
        return record
    
    logger.makeRecord = makeRecord_with_context
    
    return logger