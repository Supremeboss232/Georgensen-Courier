# Quick Start Guide - Observability & Background Jobs

## 🚀 Getting Started (5 minutes)

### 1. Configure Environment
```bash
# Copy configuration from example
cp .env.observability.example .env

# Review and adjust if needed
nano .env

# Key variables to check:
# - CELERY_BROKER_URL (should be: redis://redis:6379/0)
# - DATABASE_URL
# - LOG_LEVEL (default: INFO)
```

### 2. Start All Services
```bash
# Start Docker containers
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# Container           Status
# postgres           Up (healthy)
# redis              Up (healthy)
# backend            Up
# celery_worker      Up
# celery_beat        Up
# flower             Up
# prometheus         Up
# grafana            Up
```

### 3. Verify Installation
```bash
# Check API is running
curl http://localhost:8000/health

# Check metrics endpoint
curl http://localhost:8000/metrics

# Check task queue
docker-compose logs celery_worker | head -20
```

---

## 📊 Access Monitoring UIs

### Flower (Task Monitoring)
```
URL: http://localhost:5555
Shows:
  - Active tasks
  - Completed tasks
  - Failed tasks
  - Worker status
  - Task execution history
```

### Prometheus (Metrics)
```
URL: http://localhost:9090
Usage:
  1. Click "Graph" tab
  2. Enter metric name, e.g., "http_requests_total"
  3. Metrics available:
     - http_requests_total
     - http_request_duration_seconds
     - celery_tasks_total
     - celery_task_duration_seconds
```

### Grafana (Dashboards)
```
URL: http://localhost:3000
Login: admin / admin

Setup:
  1. Go to Configuration → Data Sources
  2. Add "Prometheus" data source
  3. URL: http://prometheus:9090
  4. Save & test
  5. Create dashboards or import pre-built ones
```

---

## 🔧 Testing Background Jobs

### Submit Test Task
```bash
# Method 1: Via Python shell
docker-compose exec backend python

>>> from app.tasks.email import send_email_task
>>> task = send_email_task.delay(
...     to_email="test@example.com",
...     subject="Test Email",
...     body="This is a test email"
... )
>>> print(task.id)  # Task ID
>>> print(task.status)  # Check status
>>> print(task.result)  # Get result

# Method 2: Via Celery command
docker-compose exec celery_worker celery -A app.celery_app inspect active

# Method 3: View in Flower
# Go to http://localhost:5555/tasks
```

### Monitor Task Execution
```bash
# Real-time logs
docker-compose logs -f celery_worker

# Task metrics in Prometheus
curl http://localhost:8000/metrics | grep celery_

# Task details in Flower
http://localhost:5555/tasks
```

---

## 📝 View Structured Logs

### JSON Logs in Docker
```bash
# All logs from all services
docker-compose logs

# Formatted as JSON
docker-compose logs backend | jq .

# Filter by level
docker-compose logs backend | jq 'select(.level == "ERROR")'

# Filter by message
docker-compose logs backend | jq 'select(.message | contains("task"))'

# Specific field
docker-compose logs backend | jq '.message, .duration_ms'
```

### Example Log Entry
```json
{
  "timestamp": "2024-01-15T10:30:45.123456+00:00",
  "level": "INFO",
  "message": "Email sent successfully",
  "logger": "tasks.email",
  "function": "send_email_task",
  "line": 52,
  "task_id": "abc123def456",
  "task_name": "send_email",
  "to": "user@example.com",
  "duration_ms": 1250
}
```

---

## 🐛 Troubleshooting

### Services Not Starting
```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verify Docker is running
docker ps
```

### Celery Tasks Not Processing
```bash
# Check worker is running
docker-compose ps celery_worker

# Worker logs
docker-compose logs celery_worker

# Restart worker
docker-compose restart celery_worker

# Check Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Can't Access Flower/Prometheus/Grafana
```bash
# Check ports are exposed
netstat -tuln | grep LISTEN | grep -E "5555|9090|3000|8000"

# Check containers are healthy
docker-compose ps

# Verify network
docker network ls
docker network inspect georgensen
```

### Metrics Not Appearing
```bash
# Check metrics endpoint returns data
curl http://localhost:8000/metrics

# Check Prometheus scrape config
# Edit: infra/prometheus.yml
# Make sure targets are correct:
# - backend should be: localhost:8000
# - Verify /metrics path exists

# Restart Prometheus
docker-compose restart prometheus

# Check Prometheus targets
http://localhost:9090/targets
```

---

## 📋 Common Tasks

### Schedule a New Task
```python
# In your API endpoint or service
from app.tasks.email import send_email_task

# Queue the task
task = send_email_task.delay(
    to_email="user@example.com",
    subject="Welcome",
    body="Welcome to Georgensen!"
)

# Return task ID to client
return {"task_id": task.id, "status": task.status}
```

### Monitor Task Progress
```python
from app.celery_app import celery_app

task_id = "abc123"
task = celery_app.AsyncResult(task_id)

print(f"Status: {task.status}")  # PENDING, STARTED, SUCCESS, FAILURE
print(f"Result: {task.result}")  # Task return value
print(f"Info: {task.info}")      # Progress info
```

### View Scheduled Tasks
```bash
# Active tasks
docker-compose exec celery_worker celery -A app.celery_app inspect active

# Scheduled tasks
docker-compose exec celery_worker celery -A app.celery_app inspect scheduled

# Reserved tasks
docker-compose exec celery_worker celery -A app.celery_app inspect reserved
```

---

## 📊 Creating a Grafana Dashboard

### Step 1: Add Prometheus Data Source
1. Go to http://localhost:3000
2. Login with admin/admin
3. Click "Configuration" → "Data Sources"
4. Click "Add data source"
5. Select "Prometheus"
6. URL: `http://prometheus:9090`
7. Click "Save & Test"

### Step 2: Create Dashboard
1. Click "Create" → "Dashboard"
2. Click "Add new panel"
3. Select "Prometheus" as data source
4. Enter query, e.g., `rate(http_requests_total[5m])`
5. Click "Run queries"
6. Customize visualization
7. Click "Save"

### Step 3: Sample Queries
```promql
# HTTP request rate per second
rate(http_requests_total[5m])

# Average request duration
histogram_quantile(0.95, http_request_duration_seconds)

# Active Celery tasks
celery_tasks_total{status="processing"}

# Task completion rate
rate(celery_tasks_total{status="success"}[5m])

# Task error rate
rate(celery_tasks_total{status="failure"}[5m])
```

---

## 🔒 Production Considerations

Before deploying to production:

### 1. Security
```bash
# Update in .env:
# - Change CELERY_BROKER_URL password
# - Set SENTRY_DSN for error tracking
# - Enable HTTPS in Grafana
# - Disable Flower public access (use authentication)
```

### 2. Performance
```bash
# Adjust in docker-compose.yml:
# - Celery worker concurrency (–concurrency=10)
# - Celery worker pool (–pool=prefork)
# - Prometheus retention period (15d default)
```

### 3. Backup & Recovery
```bash
# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# Backup Prometheus data
docker exec <prometheus-container> tar czf /backup/prometheus.tar.gz /prometheus

# Schedule regular backups
# Use task: backup_database (runs daily at 01:00 UTC)
```

### 4. Monitoring & Alerts
```bash
# Set up Prometheus alerts
# Edit: infra/prometheus.yml
# Add: alerting rules

# Configure alert receivers
# Edit Alertmanager config
# Integrate with PagerDuty, Slack, etc.
```

---

## 📚 Additional Resources

- **Celery Documentation**: https://docs.celeryproject.io/
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **Docker Compose Docs**: https://docs.docker.com/compose/
- **Redis Documentation**: https://redis.io/docs/

---

## 💬 Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Review configuration: `.env` and `docker-compose.yml`
3. Test connectivity: `docker-compose exec <service> <command>`
4. Check status: `docker-compose ps`
5. Restart services: `docker-compose restart`

---

**Ready to go! Start monitoring your application in minutes.** 🎉
