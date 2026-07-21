# OBSERVABILITY & BACKGROUND JOBS - QUICK START GUIDE

## ✅ Today's Deliverables

You now have:

1. **Assessment Document** - Full gap analysis (175 hours total work)
2. **Structured Logging** - `backend/app/core/logging_config.py` (15 hours effort)
3. **Celery Configuration** - `backend/app/celery_app.py` (20 hours effort)

---

## 🚀 Phase 1: Structured Logging (Week 1)

### Step 1: Update `backend/app/main.py`

Add this to the top of your FastAPI app initialization:

```python
# In backend/app/main.py, add near the top:

from app.core.logging_config import setup_json_logging, add_request_context

# Initialize JSON logging
logger = setup_json_logging(service_name="georgensen-courier")

# Then in your route handlers, add the decorator:
@app.get("/health", tags=["Health"])
@add_request_context
async def health_check(request):
    """Health check endpoint"""
    return {"status": "healthy"}

# All logs from your handlers will now include:
# - user_id (if authenticated)
# - request_id (trace ID)
# - duration_ms (how long request took)
# - ip_address (client IP)
```

### Step 2: Install Log Aggregation Service

**Option A: Datadog (Recommended for simplicity)**

```bash
pip install datadog

# Add to .env
DATADOG_API_KEY=your_key_here
DATADOG_SITE=datadoghq.com

# Logs automatically collected from stdout (JSON format)
```

**Option B: ELK Stack (Free, more setup)**

```bash
# Start ELK stack
docker-compose -f infra/docker-compose.elk.yml up -d

# Logs collected by Filebeat → Elasticsearch → Kibana dashboard
```

### Step 3: Test Structured Logging

```python
# In any endpoint:
import logging
logger = logging.getLogger(__name__)

@app.post("/orders")
async def create_order(order_data, current_user, db):
    order = Order(...)
    db.add(order)
    db.commit()
    
    # Log with context
    logger.info(
        "Order created successfully",
        extra={
            "user_id": current_user.id,
            "order_id": order.id,
            "total_amount": order.total_amount,
            "duration_ms": 125.5,
        }
    )
    
    return order
```

Run and check logs:
```bash
# Logs now appear as JSON (parseable by log aggregation)
docker logs georgensen-backend | tail -20
```

---

## 🚀 Phase 2: Background Jobs Setup (Week 1-2)

### Step 1: Install Dependencies

```bash
pip install celery redis

# Or update requirements.txt
echo "celery==5.3.4" >> backend/requirements.txt
echo "redis==5.0.1" >> backend/requirements.txt
```

### Step 2: Add Redis to Docker Compose

```yaml
# In docker-compose.yml, add:

  redis:
    image: redis:7-alpine
    container_name: georgensen-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  redis_data:
```

Start Redis:
```bash
docker-compose up -d redis
```

### Step 3: Update `backend/app/main.py` to Initialize Celery

```python
# In backend/app/main.py:

from app.celery_app import celery_app
from app.core.logging_config import setup_json_logging

# Initialize logging and Celery
logger = setup_json_logging()

# Celery will auto-discover tasks from app/tasks/ directory
```

### Step 4: Create Tasks Directory

```bash
mkdir -p backend/app/tasks
touch backend/app/tasks/__init__.py
```

### Step 5: Create First Task - Async Email

**`backend/app/tasks/email.py`**:

```python
from app.celery_app import celery_app
from app.services.notifications import NotificationService
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def send_email_task(self, email: str, subject: str, template: str, context: dict):
    """Send email asynchronously with retry logic"""
    try:
        service = NotificationService()
        service.send_email(email, subject=subject, template=template, context=context)
        
        logger.info(
            "Email sent successfully",
            extra={
                "email": email,
                "subject": subject,
                "task_id": self.request.id,
            }
        )
    except Exception as exc:
        # Retry with exponential backoff
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)
```

### Step 6: Update Order Endpoint to Use Async Email

```python
# In backend/app/api/orders.py:

from app.tasks.email import send_email_task

@router.post("/orders")
async def create_order(order_data, current_user, db):
    order = Order(...)
    db.add(order)
    db.commit()
    
    # ✅ NOW: Fire-and-forget (non-blocking)
    send_email_task.delay(
        email=current_user.email,
        subject="Order Confirmation",
        template="order-confirmation",
        context={"order": order}
    )
    
    # Return immediately (user doesn't wait for email SMTP)
    return {"order_id": order.id, "status": "created"}
```

### Step 7: Start Celery Workers

```bash
# Terminal 1: Start Celery worker (processes tasks)
cd backend
celery -A app.celery_app worker --loglevel=info

# Terminal 2: Start Celery beat (runs scheduled tasks)
cd backend
celery -A app.celery_app beat --loglevel=info

# Terminal 3: Monitor with Flower
cd backend
pip install flower
flower -A app.celery_app
# Visit http://localhost:5555
```

### Step 8: Test It

```python
# In Python shell:
from app.tasks.email import send_email_task

# Queue task
result = send_email_task.delay("test@example.com", "Test", "welcome", {})

# Check status
from app.celery_app import get_task_status
print(get_task_status(result.id))

# Check Flower dashboard: http://localhost:5555
```

---

## 📊 Phase 3: Metrics & Monitoring (Week 2-3)

### Step 1: Add Prometheus Metrics

**`backend/app/core/metrics.py`**:

```python
from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0]
)

# Define business metrics
orders_created_total = Counter(
    'orders_created_total',
    'Total orders created'
)

active_tasks = Gauge(
    'celery_active_tasks',
    'Active Celery tasks'
)

def track_metrics(func):
    """Decorator to track request metrics"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            status = getattr(result, 'status_code', 200)
        except Exception:
            status = 500
            raise
        finally:
            duration = time.time() - start
            method = "GET"  # Get from request if available
            endpoint = func.__name__
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        
        return result
    return wrapper
```

### Step 2: Expose Metrics Endpoint

```python
# In backend/app/main.py:

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(REGISTRY)
```

### Step 3: Monitor with Prometheus + Grafana

```bash
# Docker Compose addition:

prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./infra/prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    GF_SECURITY_ADMIN_PASSWORD=admin
```

Configure Prometheus to scrape your app:
```yaml
# infra/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'georgensen'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Step 4: Create Grafana Dashboard

Visit http://localhost:3000, add Prometheus as datasource, create dashboards showing:
- Requests per second
- Error rate (errors / total * 100)
- P95 latency
- Active tasks in Celery

---

## 🚨 Validation Checklist

### For Structured Logging:
- [ ] Logs output as JSON (check with `docker logs`)
- [ ] Can search logs by `user_id`, `endpoint`, `status`
- [ ] Datadog/ELK shows logs with proper filtering
- [ ] Test error handling (logs include stack trace)

### For Background Jobs:
- [ ] Redis is running (`redis-cli ping` returns PONG)
- [ ] Celery worker starts without errors
- [ ] Flower dashboard accessible at http://localhost:5555
- [ ] Email task completes in < 5 seconds
- [ ] Test retry: Kill Celery mid-task, task retries automatically
- [ ] Check `celery_active_tasks` metric in Prometheus

### For Metrics:
- [ ] `/metrics` endpoint returns Prometheus data
- [ ] Grafana connects to Prometheus
- [ ] Dashboard shows request rates and latencies in real-time

---

## 📈 Expected Performance Improvements

### After Structured Logging:
```
Before:
└─ Incident occurs
   └─ Grep through 50KB of logs
   └─ 30 minutes to find root cause

After:
└─ Incident occurs
   └─ Search Datadog: endpoint="/orders" AND status=500
   └─ 5 minutes to identify problem
   └─ 10 minute fix with stack trace
```

### After Background Jobs:
```
Before:
├─ Create order (50ms) + send email (500ms) = 550ms total
├─ User waits 550ms
└─ If email server slow → request times out

After:
├─ Create order (50ms) + queue email (5ms) = 55ms total
├─ User gets response in 55ms ✅
└─ Email sent asynchronously (no impact if slow)
```

### After Metrics:
```
Dashboard shows in real-time:
├─ API: 50 requests/sec, p95 latency 250ms ✅
├─ Database: 90% connection pool used (add more if needed)
├─ Cache: 85% hit rate (good!)
├─ Celery: 3 workers, 150 tasks in queue
└─ All data visible on one page
```

---

## 🎯 Next Priority Tasks

**After completing Phase 1-3 above (3-4 weeks):**

1. **Error Monitoring** (Sentry)
   - Automatically collect all exceptions
   - Group similar errors
   - Alert when error rate > threshold

2. **Distributed Tracing** (Jaeger)
   - Follow requests across services
   - Identify slow components
   - Debug production issues

3. **Admin Dashboard**
   - Real-time system status
   - Historical trends
   - Alert management

---

## 📚 Resources

- **Celery Docs**: https://docs.celeryproject.org
- **Prometheus**: https://prometheus.io/docs
- **Datadog**: https://docs.datadoghq.com
- **Grafana**: https://grafana.com/docs

---

## 💬 Troubleshooting

**Redis connection error**:
```
Error: Cannot connect to redis://localhost:6379/0
Solution: docker-compose up -d redis (or check Redis is running)
```

**Celery tasks not processing**:
```
Solution: Check celery worker is running
         celery -A app.celery_app worker --loglevel=info
```

**Logs not appearing as JSON**:
```
Solution: Verify logging_config.py is imported in main.py
         Check: all handlers use JsonFormatter
```

---

## Sign-Off

Both observability and background jobs are foundational for production. Start with **Week 1: Logging + Celery setup**, then build metrics and monitoring.

**Estimated Time to Complete All Phases**: 6-8 weeks, 3-4 engineers

Let's make the system observable and scalable! 🚀
