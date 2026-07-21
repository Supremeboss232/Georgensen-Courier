# PRODUCTION DEPLOYMENT GUIDE
# Georgensen Courier API - Complete Deployment Instructions

## 📋 Pre-Deployment Checklist

### Infrastructure
- [ ] Domain name(s) registered and DNS configured
- [ ] SSL/TLS certificates obtained (Let's Encrypt or commercial)
- [ ] Server(s) provisioned with sufficient resources (4GB+ RAM, 50GB+ disk)
- [ ] Database server configured (managed service or self-hosted)
- [ ] Redis server configured (managed service or self-hosted)
- [ ] Backup storage configured (S3, Google Cloud Storage, etc.)
- [ ] CDN configured for static assets

### Secrets & Security
- [ ] All `.env.production` values filled in and secured
- [ ] `SECRET_KEY` generated and set
- [ ] `STRIPE_SECRET_KEY` and webhook secret obtained
- [ ] Email provider API keys configured (SendGrid/Mailgun/SES)
- [ ] Sentry DSN obtained
- [ ] Database password strong and secure
- [ ] Redis password strong and secure
- [ ] SSL certificates installed on server

### Monitoring & Alerting
- [ ] Sentry project created and DSN obtained
- [ ] Grafana admin password changed
- [ ] Prometheus scrape targets configured
- [ ] Alert rules defined
- [ ] PagerDuty/Slack integrations configured
- [ ] Log aggregation service configured (optional)

### Team & Documentation
- [ ] Runbooks created for common issues
- [ ] On-call rotation established
- [ ] Incident response procedures documented
- [ ] Access control and permissions set up
- [ ] Team trained on deployment process

---

## 🚀 Step-by-Step Deployment

### Phase 1: Prepare the Server

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose git

# 3. Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# 4. Create application directory
mkdir -p /opt/georgensen/{data,logs,certs}
cd /opt/georgensen

# 5. Clone repository
git clone https://github.com/georgensen/platform.git .

# 6. Set up SSL certificates directory
mkdir -p certs
# Copy your SSL certificates here:
# - fullchain.pem (certificate chain)
# - privkey.pem (private key)
```

### Phase 2: Configure Environment

```bash
# 1. Copy production environment template
cp .env.production.example .env.production

# 2. Edit environment variables with your values
nano .env.production
# Update:
# - DB_PASSWORD (strong, unique)
# - REDIS_PASSWORD (strong, unique)
# - SECRET_KEY (run: python -c "from secrets import token_urlsafe; print(token_urlsafe(32))")
# - STRIPE_SECRET_KEY
# - SENTRY_DSN
# - MAIL provider credentials
# - Domain names
# - All other required fields

# 3. Verify all required variables are set
grep "CHANGE_ME\|error\|:?" .env.production || echo "✓ All values configured"

# 4. Secure the file
chmod 600 .env.production
```

### Phase 3: Database Setup

```bash
# 1. Start database service only
docker-compose -f docker-compose.prod.yml up -d db redis

# 2. Wait for database to be healthy
docker-compose -f docker-compose.prod.yml ps db
# Status should be "Up (healthy)"

# 3. Create initial tables
docker-compose -f docker-compose.prod.yml exec db psql -U georgensen -d georgensen_prod -c "CREATE SCHEMA IF NOT EXISTS public;"

# 4. Initialize seed data (if applicable)
docker-compose -f docker-compose.prod.yml exec backend python -m app.db.init_db

# 5. Verify database connectivity
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.db.base import engine; engine.connect()"
```

### Phase 4: Configure SSL/TLS with Let's Encrypt

```bash
# 1. Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# 2. Generate certificates (replace with your domain)
sudo certbot certonly --standalone \
  -d api.georgensen.com \
  -d monitoring.georgensen.com \
  -d flower.georgensen.com \
  -d prometheus.georgensen.com

# 3. Copy certificates to application directory
sudo cp /etc/letsencrypt/live/api.georgensen.com/fullchain.pem /opt/georgensen/infra/nginx/ssl/
sudo cp /etc/letsencrypt/live/api.georgensen.com/privkey.pem /opt/georgensen/infra/nginx/ssl/
sudo chown 1000:1000 /opt/georgensen/infra/nginx/ssl/*

# 4. Set up auto-renewal
sudo certbot renew --dry-run  # Test renewal
sudo systemctl enable certbot.timer
```

### Phase 5: Create Nginx Authentication

```bash
# Create .htpasswd file for monitoring endpoints
docker run --rm -v /opt/georgensen/infra/nginx:/tmp ubuntu:latest \
  bash -c "apt-get update && apt-get install -y apache2-utils && \
  htpasswd -bc /tmp/.htpasswd admin YOUR_SECURE_PASSWORD"

chmod 600 /opt/georgensen/infra/nginx/.htpasswd
```

### Phase 6: Deploy Application

```bash
# 1. Update docker-compose with environment
export $(cat .env.production | grep -v '^#' | xargs)

# 2. Pull latest images
docker-compose -f docker-compose.prod.yml pull

# 3. Build backend image
docker-compose -f docker-compose.prod.yml build backend

# 4. Start all services
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify all services are running
docker-compose -f docker-compose.prod.yml ps
# All should show "Up" status

# 6. Check logs for errors
docker-compose -f docker-compose.prod.yml logs -f backend --tail=50

# 7. Health check
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.georgensen.com/health
```

### Phase 7: Verify Deployment

```bash
# 1. Test API endpoints
curl https://api.georgensen.com/api/docs

# 2. Check Prometheus is scraping
curl -u admin:PASSWORD https://monitoring.georgensen.com/api/v1/targets

# 3. Check background jobs
curl -u admin:PASSWORD https://flower.georgensen.com

# 4. Verify Grafana
curl https://monitoring.georgensen.com
# Login: admin / (your Grafana password)

# 5. Check SSL certificate
curl -vI https://api.georgensen.com 2>&1 | grep "subject="

# 6. Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 📊 Post-Deployment Verification

### Application Health

```bash
# Check API availability
watch curl -s https://api.georgensen.com/health | jq .

# Monitor background job queue
curl -u admin:PASSWORD https://flower.georgensen.com/api/workers

# Check database connections
docker-compose -f docker-compose.prod.yml exec db psql -U georgensen -d georgensen_prod -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis memory usage
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO memory
```

### Metrics & Monitoring

```bash
# Verify Prometheus is collecting metrics
curl https://monitoring.georgensen.com/api/v1/query?query=up

# Check Grafana dashboards
# Access: https://monitoring.georgensen.com
# - API Performance Dashboard
# - Business Metrics Dashboard
# - Infrastructure Dashboard

# Verify log aggregation
# Check centralized logs for errors
```

### Backup & Recovery

```bash
# 1. Test database backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U georgensen georgensen_prod > /tmp/backup.sql

# 2. Upload to S3
aws s3 cp /tmp/backup.sql s3://georgensen-backups-prod/

# 3. Test restore procedure
# Don't do this in production, but document the process

# 4. Verify automated backups are running
docker-compose -f docker-compose.prod.yml logs celery_beat | grep backup
```

---

## 🔒 Security Hardening Post-Deployment

### Access Control

```bash
# 1. Disable root login
sudo sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# 2. Set up SSH key authentication only
sudo sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config

# 3. Restart SSH
sudo systemctl restart sshd

# 4. Set up firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (for Let's Encrypt renewal)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Container Security

```bash
# 1. Set resource limits in docker-compose.prod.yml
# Already configured with `deploy.resources`

# 2. Use read-only filesystems where possible
# Add to services: `read_only: true`

# 3. Run containers as non-root
# Already configured: `user:` directives

# 4. Scan images for vulnerabilities
docker pull ubuntu:latest
trivy image georgensen/backend:latest
```

### Data Security

```bash
# 1. Encrypt database backups
gpg --symmetric /tmp/backup.sql

# 2. Set up S3 bucket encryption
aws s3api put-bucket-encryption \
  --bucket georgensen-backups-prod \
  --server-side-encryption-configuration '{...}'

# 3. Restrict S3 access
aws s3api put-bucket-versioning \
  --bucket georgensen-backups-prod \
  --versioning-configuration Status=Enabled
```

---

## 🚨 Monitoring & Alerting Setup

### Configure Sentry for Error Tracking

```bash
# 1. Create Sentry project at https://sentry.io

# 2. Set SENTRY_DSN in .env.production
SENTRY_DSN=https://key@sentry.io/project_id

# 3. Test Sentry integration
docker-compose -f docker-compose.prod.yml exec backend python -c \
  "import sentry_sdk; sentry_sdk.capture_message('Test')"

# 4. Verify in Sentry dashboard
```

### Configure Alerts

```bash
# 1. On Slack
SLACK_WEBHOOK_ERRORS=https://hooks.slack.com/services/...
SLACK_WEBHOOK_ALERTS=https://hooks.slack.com/services/...

# 2. On PagerDuty
PAGERDUTY_INTEGRATION_KEY=...

# 3. Create alert rules in Prometheus
# Edit: infra/prometheus/alert_rules.yml
```

### Log Aggregation (Optional)

```bash
# Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)
# Option 2: Datadog
# Option 3: New Relic
# Option 4: CloudWatch (if using AWS)

# All services output JSON logs to:
# - /var/log/container.log
# Forward these to your log aggregation service
```

---

## 📈 Scaling & Performance Optimization

### Horizontal Scaling

```bash
# Increase replicas in docker-compose.prod.yml
services:
  backend:
    deploy:
      replicas: 3  # Scale from 1 to 3
  celery_worker:
    deploy:
      replicas: 4  # Increase workers
  nginx:
    deploy:
      replicas: 2  # Load balance

# Redeploy
docker-compose -f docker-compose.prod.yml up -d
```

### Database Optimization

```bash
# 1. Configure connection pooling
# Already set: DATABASE_POOL_SIZE=20

# 2. Add read replicas for read-heavy workloads
# Edit: DATABASE_URL for read operations

# 3. Monitor slow queries
docker-compose -f docker-compose.prod.yml exec db psql -U georgensen -d georgensen_prod \
  -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

### Redis Optimization

```bash
# Monitor memory usage
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO memory

# Set up persistence
# Already configured: appendonly yes

# Monitor hit rate
docker-compose -f docker-compose.prod.yml exec redis redis-cli INFO stats
```

---

## 🔄 Continuous Deployment

### GitHub Actions Workflow

```yaml
name: Deploy Production
on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to production
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
        run: |
          mkdir -p ~/.ssh
          echo "$DEPLOY_KEY" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa \
            root@$DEPLOY_HOST \
            "cd /opt/georgensen && git pull && \
            docker-compose -f docker-compose.prod.yml down && \
            docker-compose -f docker-compose.prod.yml up -d"
```

---

## 🐛 Troubleshooting & Recovery

### Common Issues

**Services not starting:**
```bash
docker-compose -f docker-compose.prod.yml logs
docker-compose -f docker-compose.prod.yml restart
```

**Database connection errors:**
```bash
docker-compose -f docker-compose.prod.yml exec db psql -U georgensen -d georgensen_prod -c "SELECT 1;"
```

**Out of disk space:**
```bash
docker system prune -a
docker volume prune
```

**High memory usage:**
```bash
docker stats
# Adjust resource limits in docker-compose.prod.yml
```

### Rollback Procedure

```bash
# 1. Tag current image
docker tag georgensen/backend:latest georgensen/backend:v1.0.0-stable

# 2. In case of issues, revert
docker-compose -f docker-compose.prod.yml down
git revert <commit-hash>
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📚 Maintenance Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| SSL certificate renewal | 30 days before expiry | Automated |
| Database backups | Daily | Automated |
| Log rotation | Daily | Automated |
| Dependency updates | Weekly | DevOps |
| Security patches | As available | Security team |
| Performance review | Monthly | DevOps |
| Disaster recovery drill | Quarterly | DevOps |
| Major version upgrades | Bi-annually | DevOps + team |

---

## 📞 Support & Escalation

```
Level 1: Check logs → Fix common issues
Level 2: Contact DevOps team → Investigate infrastructure
Level 3: Page on-call → Critical production issue
Level 4: Post-incident review → Root cause analysis
```

**On-call contact:** [oncall@georgensen.com](mailto:oncall@georgensen.com)
**Incident channel:** #incidents on Slack
**Status page:** https://status.georgensen.com

---

## ✅ Deployment Checklist Summary

- [ ] Server prepared and secured
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] SSL certificates installed
- [ ] Nginx configured with SSL
- [ ] All services started and healthy
- [ ] API endpoints tested
- [ ] Monitoring dashboards verified
- [ ] Backup system tested
- [ ] Security hardening completed
- [ ] Team trained on procedures
- [ ] Incident response procedures documented
- [ ] Post-deployment verification passed

**Deployment Date:** ____________
**Deployed By:** ____________
**Reviewed By:** ____________

---

**Review this guide and update as needed. Keep it up-to-date with your infrastructure changes.**
