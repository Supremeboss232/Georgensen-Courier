# Deployment Guide

## Overview

This document outlines the deployment process for the Georgensen Courier platform across development, staging, and production environments.

## Prerequisites

- Docker and Docker Compose installed
- AWS account (for production)
- GitHub repository access
- SSL certificates (production only)
- Database backups configured

## Environment Setup

### Development Environment

```bash
# Clone repository
git clone https://github.com/georgensen/courier.git
cd courier

# Build development containers
docker-compose -f docker-compose.yml build

# Start services
docker-compose up -d

# Initialize database
docker-compose exec backend python -m alembic upgrade head

# Run tests
docker-compose exec backend pytest
```

### Staging Environment

Staging should mirror production as closely as possible.

```bash
# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Run smoke tests
docker-compose exec backend pytest tests/smoke/

# Performance testing
docker-compose exec backend locust -f tests/performance/locustfile.py
```

### Production Environment

#### AWS ECS Deployment

```bash
# Push images to ECR
aws ecr get-login-password --region au-southeast-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.au-southeast-2.amazonaws.com

docker tag georgensen/frontend:latest <account-id>.dkr.ecr.au-southeast-2.amazonaws.com/georgensen-frontend:latest
docker push <account-id>.dkr.ecr.au-southeast-2.amazonaws.com/georgensen-frontend:latest

# Update ECS service
aws ecs update-service \
  --cluster georgensen-prod \
  --service frontend \
  --force-new-deployment \
  --region au-southeast-2
```

#### RDS Database Setup

```bash
# Create database instance
aws rds create-db-instance \
  --db-instance-identifier georgensen-prod-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --allocated-storage 100 \
  --region au-southeast-2

# Create read replica for failover
aws rds create-db-instance-read-replica \
  --db-instance-identifier georgensen-prod-db-replica \
  --source-db-instance-identifier georgensen-prod-db \
  --region au-southeast-2
```

## Service Deployment

### Backend Service

```dockerfile
# Dockerfile.backend
FROM python:3.12-slim

WORKDIR /app

COPY backend-python/requirements.txt .
RUN pip install -r requirements.txt

COPY backend-python/ .

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Service

```dockerfile
# Dockerfile.frontend
FROM node:18-alpine

WORKDIR /app

COPY frontend/package.json .
RUN npm install

COPY frontend/ .

RUN npm run build

CMD ["npm", "start"]
```

### Nginx Configuration

```nginx
# nginx.conf
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name georgensen.com.au;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name georgensen.com.au;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri /index.html;
    }
}
```

## Database Migration

```bash
# Backup production database
pg_dump -h prod-db.rds.amazonaws.com -U admin -d georgensen > backup.sql

# Run migrations
docker-compose exec backend alembic upgrade head

# Verify migration
docker-compose exec backend alembic current
```

## Monitoring and Logging

### CloudWatch Logs

```bash
# View backend logs
aws logs tail /ecs/georgensen-backend --follow

# Set up alarms
aws cloudwatch put-metric-alarm \
  --alarm-name georgensen-backend-cpu \
  --alarm-description "Alert on high CPU usage" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold
```

### Application Monitoring

- **APM Tool:** New Relic
- **Log Aggregation:** CloudWatch Logs
- **Metrics:** Prometheus + Grafana
- **Uptime Monitoring:** UptimeRobot

## Rollback Procedure

```bash
# Rollback to previous version
aws ecs update-service \
  --cluster georgensen-prod \
  --service backend \
  --task-definition georgensen-backend:50 \
  --force-new-deployment

# Verify rollback
aws ecs describe-services \
  --cluster georgensen-prod \
  --services backend
```

## Health Checks

```python
# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow()
    }
```

## Disaster Recovery

- **RTO:** 1 hour
- **RPO:** 15 minutes
- **Backup frequency:** Every 6 hours
- **Backup retention:** 30 days
- **Disaster recovery drill:** Monthly

## Security

- SSL/TLS encryption on all connections
- VPC with restricted security groups
- Secrets managed by AWS Secrets Manager
- DDoS protection via CloudFront
- WAF rules configured

## Scaling

### Auto-scaling Configuration

```yaml
TargetTrackingScalingPolicy:
  TargetValue: 70
  PredefinedMetricSpecification:
    PredefinedMetricType: ECSServiceAverageCPUUtilization
  ScaleOutCooldown: 60
  ScaleInCooldown: 300
```

## Maintenance Windows

- **Scheduled maintenance:** Sundays 02:00-04:00 AEDT
- **Planned downtime:** 4 hours maximum
- **Maintenance notifications:** 48 hours advance notice
- **Emergency patches:** Deployed immediately with user notification

## Deployment Checklist

- [ ] Code reviewed and merged to main branch
- [ ] All tests passing (unit, integration, e2e)
- [ ] Database migrations tested
- [ ] Performance benchmarks verified
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Stakeholders notified
- [ ] Rollback plan confirmed
- [ ] Health checks passing
- [ ] Monitoring alerts active

## Support Contacts

- **DevOps Team:** devops@georgensen.com.au
- **On-call:** Check PagerDuty schedule
- **Emergency:** +61 2 XXXX XXXX
