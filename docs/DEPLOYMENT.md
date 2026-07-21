# Deployment Guide - Georgensen Courier

**Version**: 1.0  
**Date**: February 4, 2026  
**Environment**: Production & Staging

---

## Prerequisites

### Local Development
```bash
# Python 3.9+
python --version

# PostgreSQL 13+
psql --version

# Docker & Docker Compose
docker --version
docker-compose --version
```

### Staging/Production Servers
- Ubuntu 20.04+ LTS
- 4GB+ RAM
- 50GB+ storage
- 100Mbps+ internet

---

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/georgensen/platform.git
cd georgensen
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies
```bash
cd backend-python
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cd backend-python
cp .env.example .env
# Edit .env with local PostgreSQL details
```

### 5. Initialize Database
```bash
# Create database
createdb -U postgres georgensen

# Run migrations (when available)
alembic upgrade head
```

### 6. Start Backend
```bash
cd backend-python
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start Frontend (new terminal)
```bash
cd frontend
python -m http.server 8080
```

**Access**:
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Frontend: http://localhost:8080

---

## Docker Deployment (Local)

### Build & Start Services
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Database Setup
```bash
# Connect to database container
docker exec -it georgensen-db psql -U georgensen

# Run migrations inside backend container
docker exec georgensen-backend alembic upgrade head
```

### Stop Services
```bash
docker-compose down
```

---

## Staging Deployment

### 1. Server Setup

**SSH into staging server**:
```bash
ssh ubuntu@staging.georgensen.com
```

**Install system dependencies**:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3-pip python3-venv
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nginx certbot python3-certbot-nginx
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
```

### 2. Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/georgensen/platform.git
cd platform
```

### 3. Configure Environment
```bash
cd backend-python
cp .env.example .env

# Edit with staging values
nano .env
```

**Staging .env values**:
```
DATABASE_URL=postgresql://user:password@localhost/georgensen_staging
JWT_SECRET=staging-secret-key-min-32-chars
DEBUG=False
CORS_ORIGINS=["https://staging.georgensen.com","https://admin-staging.georgensen.com"]
```

### 4. Build Docker Images
```bash
docker-compose -f docker-compose.yml build
```

### 5. Start Services
```bash
docker-compose -f docker-compose.yml up -d
```

### 6. Configure nginx
```bash
sudo nano /etc/nginx/sites-available/georgensen

# Add config (see nginx.conf section below)

# Enable site
sudo ln -s /etc/nginx/sites-available/georgensen /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL Certificate
```bash
# Using Let's Encrypt
sudo certbot certonly --nginx -d staging.georgensen.com -d admin-staging.georgensen.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Production Deployment

### 1. Server Requirements

**Recommended AWS Setup**:
- **Compute**: EC2 t3.large (2vCPU, 8GB RAM)
- **Database**: RDS PostgreSQL 13+, db.t3.small
- **Storage**: EBS 100GB gp3
- **CDN**: CloudFront
- **Email**: SES
- **DNS**: Route 53
- **Monitoring**: CloudWatch

**Architecture Diagram**:
```
                    ┌─────────────────┐
                    │   CloudFront    │
                    │   (CDN)         │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │   nginx ALB     │
                    └────────┬────────┘
                    ┌────────┴────────────────────┐
                    │                             │
        ┌───────────▼─────────┐     ┌────────────▼────────┐
        │  API Backend        │     │   Frontend/Admin    │
        │  (ECS, 3x tasks)    │     │   (ECS, 2x tasks)   │
        └───────────┬─────────┘     └────────────┬────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  RDS PostgreSQL            │
                    │  (Multi-AZ)                │
                    └────────────────────────────┘
```

### 2. Production Deployment Steps

**SSH to production server**:
```bash
ssh ubuntu@api.georgensen.com
```

**Clone and setup**:
```bash
cd /opt
sudo git clone https://github.com/georgensen/platform.git georgensen
cd georgensen
sudo chown -R ubuntu:ubuntu /opt/georgensen
```

**Configure production environment**:
```bash
cd backend-python
cp .env.example .env
nano .env
```

**Production .env**:
```
DATABASE_URL=postgresql://georgensen:STRONG_PASSWORD@prod-db.xyz.rds.amazonaws.com/georgensen
JWT_SECRET=GENERATE_STRONG_32_CHAR_SECRET
DEBUG=False
CORS_ORIGINS=["https://georgensen.com","https://admin.georgensen.com"]
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FIRST_SUPERUSER=admin@georgensen.com
FIRST_SUPERUSER_PASSWORD=STRONG_PASSWORD
```

**Build and start**:
```bash
docker-compose -f docker-compose.yml build --no-cache
docker-compose -f docker-compose.yml up -d
```

**Verify health**:
```bash
curl http://localhost:8000/health
curl http://localhost:8080/
```

### 3. nginx Configuration

**Create `/etc/nginx/sites-available/georgensen`**:

```nginx
# Upstream definitions
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:8080;
}

upstream admin {
    server admin:8081;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;

# Frontend server block
server {
    listen 80;
    listen [::]:80;
    server_name georgensen.com www.georgensen.com;
    
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name georgensen.com www.georgensen.com;
    
    ssl_certificate /etc/letsencrypt/live/georgensen.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/georgensen.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        limit_req zone=general burst=20 nodelay;
    }
}

# API server block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.georgensen.com;
    
    ssl_certificate /etc/letsencrypt/live/api.georgensen.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.georgensen.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        limit_req zone=api burst=100 nodelay;
    }
    
    location /health {
        proxy_pass http://backend/health;
        access_log off;
    }
}

# Admin server block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name admin.georgensen.com;
    
    ssl_certificate /etc/letsencrypt/live/admin.georgensen.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.georgensen.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location / {
        proxy_pass http://admin;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        limit_req zone=general burst=20 nodelay;
    }
}
```

### 4. Monitoring & Logging

**CloudWatch Logs**:
```bash
# View backend logs
docker-compose logs -f backend

# View access logs
tail -f /var/log/nginx/access.log | grep georgensen

# View error logs
tail -f /var/log/nginx/error.log
```

**Health Checks**:
```bash
# Backend health
curl https://api.georgensen.com/health

# Database connectivity
docker exec georgensen-db psql -U georgensen -d georgensen -c "SELECT 1"

# Uptime monitoring (setup with external service)
# https://uptimerobot.com/ - Add all 3 endpoints
```

---

## Database Backups

### Automated Backups
```bash
# Create backup directory
mkdir -p /backups/postgresql

# Add to crontab (daily at 2 AM)
0 2 * * * docker exec georgensen-db pg_dump -U georgensen georgensen > /backups/postgresql/backup-$(date +\%Y\%m\%d).sql
```

### Manual Backup
```bash
docker exec georgensen-db pg_dump -U georgensen georgensen > backup.sql
```

### Restore from Backup
```bash
docker exec -i georgensen-db psql -U georgensen < backup.sql
```

---

## Monitoring & Alerts

### Key Metrics to Monitor
- API Response Time (target: < 500ms)
- Error Rate (target: < 0.1%)
- Database Connections (target: < 80% max)
- Disk Usage (alert: > 80%)
- Memory Usage (alert: > 85%)
- CPU Usage (alert: > 75%)

### Alert Thresholds
```
API Down: Immediate alert
Error Rate > 1%: Alert
Response Time > 1s: Warning
Disk > 90%: Alert
Database Connections > 90%: Alert
```

---

## Scaling Considerations

### Horizontal Scaling
- Add more backend replicas (ECS task count)
- Add more frontend instances (behind ALB)
- Use RDS read replicas for reports

### Performance Tuning
- Enable connection pooling (PostgreSQL)
- Add Redis caching layer
- Optimize database indexes
- Implement CDN for static assets

---

## Rollback Procedures

### Quick Rollback
```bash
# Get previous image tag
docker ps --no-trunc | grep backend

# Stop current deployment
docker-compose down

# Deploy previous version
docker-compose -f docker-compose.old.yml up -d

# Verify
curl https://api.georgensen.com/health
```

### Database Rollback
```bash
# If migration failed, restore from backup
docker exec -i georgensen-db psql -U georgensen < /backups/postgresql/backup-YYYYMMDD.sql
```

---

## Troubleshooting

### API not responding
```bash
# Check if container is running
docker ps | grep backend

# Check logs
docker logs georgensen-backend

# Restart if needed
docker restart georgensen-backend
```

### Database connection issues
```bash
# Test connection
docker exec georgensen-backend psql -U georgensen -h db

# Check environment variables
docker exec georgensen-backend env | grep DATABASE
```

### High latency
```bash
# Check server resources
free -h  # Memory
df -h    # Disk
top      # CPU

# Check network
ping api.georgensen.com
curl -w "@curl-format.txt" https://api.georgensen.com
```

---

## Maintenance Windows

**Scheduled Maintenance**: Sundays, 2:00-4:00 AM UTC  
**Communication**: Notify users 48 hours before  
**Backup**: Always backup before maintenance

---

**Version**: 1.0  
**Last Updated**: February 4, 2026  
**Maintainer**: DevOps Team
