# DEPLOYMENT LAUNCH CHECKLIST
**Project:** Georgensen Courier API  
**Date:** ________________  
**Environment:** Production  
**Deployed By:** ________________  
**Reviewed By:** ________________  

---

## PRE-DEPLOYMENT (7 days before)

### Infrastructure & Hosting
- [ ] Domain registered and DNS configured
- [ ] Server provisioned (4GB+ RAM, 50GB+ disk, 100Mbps+ connection)
- [ ] SSH access verified and secured (key-based, no password)
- [ ] Firewall rules configured (80, 443 open; others restricted)
- [ ] PostgreSQL database created and configured
- [ ] Redis instance created and configured
- [ ] S3 bucket created for backups with encryption enabled
- [ ] CDN configured for static assets
- [ ] SSL certificate purchased or Let's Encrypt account ready

### Security & Secrets
- [ ] All environment variables documented and values obtained:
  - [ ] `SECRET_KEY` generated (32+ char, cryptographically secure)
  - [ ] `DB_PASSWORD` strong (16+ char, mixed case, numbers, symbols)
  - [ ] `REDIS_PASSWORD` strong (16+ char, mixed case, numbers, symbols)
  - [ ] `STRIPE_SECRET_KEY` from Stripe dashboard
  - [ ] `STRIPE_WEBHOOK_SECRET` from Stripe dashboard
  - [ ] Email provider API key (SendGrid/Mailgun/SES)
  - [ ] `SENTRY_DSN` from Sentry project
- [ ] All secrets stored securely (1Password, Vault, etc.)
- [ ] No secrets committed to version control
- [ ] `.env.production` file created with all values
- [ ] `.env.production` file has 600 permissions (readable only by owner)
- [ ] Team members who need access have secure credential sharing

### Monitoring & Alerting
- [ ] Sentry project created and DSN obtained
- [ ] Prometheus configuration reviewed
- [ ] Grafana admin password changed from default
- [ ] Alert rules created for critical metrics:
  - [ ] API error rate > 5%
  - [ ] Database CPU > 80%
  - [ ] Disk space < 10%
  - [ ] Response time > 5s
  - [ ] Background job queue > 1000 tasks
- [ ] Slack/PR/PagerDuty integrations configured
- [ ] On-call rotation established
- [ ] Incident response procedures documented

### Team Preparation
- [ ] Team trained on deployment process
- [ ] Team trained on monitoring dashboards
- [ ] Runbooks created for common issues
- [ ] Rollback procedures documented and tested
- [ ] Post-deployment validation checklist prepared

---

## 24 HOURS BEFORE DEPLOYMENT

### Final Infrastructure Check
- [ ] Database backups verified
- [ ] S3 access verified (upload/download test)
- [ ] SSL certificate ready (If Let's Encrypt, certbot installed)
- [ ] Nginx reverse proxy configuration reviewed
- [ ] Docker images built and tested locally
- [ ] docker-compose.prod.yml syntax validated

### Configuration & Code
- [ ] `.env.production` all values filled and verified
- [ ] No hardcoded secrets in code
- [ ] All environment variables in config.py are used
- [ ] Database migration scripts tested (if any)
- [ ] API documentation generated and accessible
- [ ] Git repository latest main branch pulled
- [ ] All unit tests passing locally

### Communication
- [ ] Deployment window scheduled in team calendar
- [ ] Client/stakeholders notified of deployment time
- [ ] On-call rotation confirmed for deployment window
- [ ] Slack #incidents channel ready
- [ ] Status page updated with maintenance window (if needed)

---

## DEPLOYMENT DAY - BEFORE START

### Final Verification (2 hours before)
- [ ] All team members present and ready
- [ ] Communication channels open (Slack, call bridge, etc.)
- [ ] Monitoring dashboards visible to all
- [ ] Rollback plan reviewed with team
- [ ] Pre-deployment baseline metrics captured:
  - [ ] API response time
  - [ ] Error rate
  - [ ] Database query count
  - [ ] Active connections
  - [ ] Background job queue size
- [ ] Database backup created
- [ ] Git commit tagged with version (v1.0.0-prod)

### Server Preparation (30 mins before)
- [ ] SSH into server and verify access
- [ ] Check disk space: `df -h`
- [ ] Verify Docker running: `docker ps`
- [ ] Current running containers noted/documented
- [ ] Environment file backed up: `cp .env.production .env.production.bak`

---

## DEPLOYMENT - EXECUTION

### Phase 1: Configuration & Secrets (0 min - 5 min)
- [ ] Copy .env.production to server
- [ ] Verify all values in .env.production
- [ ] Check no "CHANGE_ME" values remain
- [ ] Test database connection from server
- [ ] Test Redis connection from server

### Phase 2: Build (5 min - 15 min)
- [ ] Pull latest code: `git pull origin main`
- [ ] Build backend image: `docker-compose -f docker-compose.prod.yml build backend`
- [ ] Build completes with no errors
- [ ] Image size verified and reasonable
- [ ] Image layers reviewed (no temporary files left)

### Phase 3: Start Services (15 min - 25 min)
- [ ] Database service started and healthy: `docker-compose -f docker-compose.prod.yml up -d db`
- [ ] Wait 10s for database to be ready
- [ ] Database health check passes: `docker-compose ps db` shows "Up (healthy)"
- [ ] Redis service started and healthy: `docker-compose -f docker-compose.prod.yml up -d redis`
- [ ] Redis health check passes
- [ ] Remaining services started: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] All services started: `docker-compose ps` shows all "Up"
- [ ] No service is in "Restarting" state

### Phase 4: Database Initialization (25 min - 35 min)
- [ ] Database tables created (first deploy only): `docker-compose exec backend python -m app.db.init_db`
- [ ] No database errors in logs: `docker-compose logs db | grep ERROR`
- [ ] Admin user created (if first deploy)
- [ ] Database seed data loaded (if applicable)
- [ ] Database migration scripts run (if any)

### Phase 5: Validation - API (35 min - 45 min)
- [ ] Check backend logs for errors: `docker-compose logs backend --tail=50`
- [ ] API health check passes: `curl https://api.georgensen.com/health`
- [ ] API docs accessible: `curl https://api.georgensen.com/api/docs`
- [ ] Metrics endpoint working: `curl https://api.georgensen.com/metrics`
- [ ] Test login: `curl -X POST https://api.georgensen.com/api/v1/auth/login`
- [ ] Create test order (if applicable)
- [ ] Retrieve test order (if applicable)
- [ ] Test webhook endpoint (if applicable)

### Phase 6: Validation - Background Jobs (45 min - 55 min)
- [ ] Celery worker logs show tasks ready: `docker-compose logs celery_worker --tail=20 | grep ready`
- [ ] Task submitted and execute: `docker-compose exec backend celery -A app.celery_app call send_email -a args --arg=test@example.com`
- [ ] Flower UI accessible: `curl https://flower.georgensen.com` (with auth)
- [ ] Celery Beat scheduler running: `docker-compose logs celery_beat --tail=10 | grep "Scheduler tick"`
- [ ] Scheduled tasks appear in Flower

### Phase 7: Validation - Monitoring (55 min - 65 min)
- [ ] Prometheus scrape targets healthy: `curl https://monitoring.georgensen.com/api/v1/targets`
- [ ] Prometheus collecting metrics: `curl https://monitoring.georgensen.com/api/v1/query?query=up`
- [ ] Grafana dashboard loaded: `curl https://monitoring.georgensen.com/health`
- [ ] Grafana connected to Prometheus as data source
- [ ] Custom dashboards visible and updating
- [ ] Alert rules loaded: `curl https://monitoring.georgensen.com/api/v1/rules`

### Phase 8: Validation - SSL/TLS (65 min - 70 min)
- [ ] HTTPS working: `curl -I https://api.georgensen.com` returns 200
- [ ] SSL certificate valid: `openssl s_client -connect api.georgensen.com:443 | grep "Issuer"`
- [ ] Certificate not expiring soon: `echo | openssl s_client -servername api.georgensen.com -connect api.georgensen.com:443 2>/dev/null | openssl x509 -noout -dates`
- [ ] HSTS header present: `curl -I https://api.georgensen.com | grep Strict-Transport`
- [ ] Mixed content warnings (check browser console on monitoring sites)

### Phase 9: Performance Baseline (70 min - 75 min)
- [ ] Response time acceptable: < 500ms for normal requests
- [ ] API latency: `curl -w 'Total: %{time_total}s\n' https://api.georgensen.com/api/docs`
- [ ] Database query performance: `docker-compose exec db psql -U georgensen -d georgensen_prod -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"`
- [ ] Error rate at baseline: `curl https://api.georgensen.com/metrics | grep http_requests_total`
- [ ] Celery task execution time acceptable: Check Flower

### Phase 10: Security Check (75 min - 80 min)
- [ ] No sensitive data in logs: `docker-compose logs | grep -i password || echo "OK"`
- [ ] No debug mode enabled: `curl -s https://api.georgensen.com/api/docs | grep -i debug || echo "OK"`
- [ ] SQL injection test fails (returns 400): `curl "https://api.georgensen.com/api/v1/orders?id=1';DROP TABLE orders;--"`
- [ ] CORS properly configured: Test cross-origin requests
- [ ] Authentication required for protected endpoints
- [ ] Rate limiting working: Make 200 requests in 10s, expect 429 errors

---

## POST-DEPLOYMENT (Immediately after)

### System Verification (80 min - 90 min)
- [ ] All containers running: `docker ps` shows all services "Up"
- [ ] Disk space reasonable: `du -sh *` shows no unexpected growth
- [ ] Memory usage acceptable: `docker stats` shows reasonable values
- [ ] Network connectivity fine: `docker-compose exec backend curl https://api.external-service.com`
- [ ] Services restarting properly: `docker-compose restart && docker ps`

### Monitoring & Alerts (90 min - 100 min)
- [ ] Logs being collected: `docker-compose logs backend | tail -20 | jq .`
- [ ] Metrics flowing into Prometheus: Check Prometheus targets
- [ ] Grafana dashboards updating: Check dashboard timestamps
- [ ] Sentry receiving events: Make request that generates error
- [ ] Alert notification sent: Check Slack/PagerDuty
- [ ] No critical alerts firing (only baseline alerts)

### Stakeholder Communication (100 min - 105 min)
- [ ] Notify client/stakeholders: "Deployment successful"
- [ ] Share monitoring dashboard links
- [ ] Post in #incidents: "Deployment complete, monitoring normal"
- [ ] Update status page (if was in maintenance mode)
- [ ] Document deployment details in wiki/confluence

### Developers Test via UI (Last step)
- [ ] Login to customer portal: Works without issues
- [ ] Create an order: Completes successfully
- [ ] Track order: Shows live tracking updates
- [ ] View admin dashboard: Shows live metrics
- [ ] Receive email notifications: Arrives within 5 minutes
- [ ] Payment processing (if enabled): Test transaction

---

## 24 HOURS AFTER DEPLOYMENT

### System Health
- [ ] No error spikes in logs
- [ ] API response time stable
- [ ] Database performance stable
- [ ] Background job queue normal
- [ ] No stuck tasks in Celery
- [ ] Memory usage stable (no leaks)
- [ ] CPU usage normal
- [ ] Disk usage not growing unexpectedly

### Business Functions
- [ ] Orders processed normally
- [ ] Emails delivered on time
- [ ] Payments processed correctly
- [ ] Partner dashboard updated
- [ ] Customer tracking working
- [ ] Admin reports generated correctly

### Security & Compliance
- [ ] No unauthorized access attempts (check logs)
- [ ] SSL certificate still valid
- [ ] No data breaches reported
- [ ] Backup completed successfully
- [ ] Log retention policy enforced

### Team Debrief
- [ ] Post-deployment meeting conducted
- [ ] Any issues documented
- [ ] Follow-up tasks assigned
- [ ] Deployment notes added to wiki
- [ ] Runbooks updated if needed
- [ ] Team feedback collected

---

## ROLLBACK PROCEDURE (If needed)

**Only if critical issues occur that can't be fixed within 30 minutes:**

- [ ] Declare incident in #incidents Slack channel
- [ ] Stop receiving new traffic (or route to old version)
- [ ] Document what's broken
- [ ] Execute rollback:
  ```bash
  docker-compose -f docker-compose.prod.yml down
  git revert <deployment-commit>
  docker-compose -f docker-compose.prod.yml build backend
  docker-compose -f docker-compose.prod.yml up -d
  ```
- [ ] Verify old version works
- [ ] Notify stakeholders: "Rolled back to previous version"
- [ ] Schedule post-mortem within 24 hours
- [ ] Root cause analysis completed
- [ ] Fix deployed after verification

---

## SIGN-OFF

| Role | Name | Signature | Date | Time |
|------|------|-----------|------|------|
| Deployment Lead | ____________ | ____________ | ________ | ________ |
| Tech Lead | ____________ | ____________ | ________ | ________ |
| DevOps Engineer | ____________ | ____________ | ________ | ________ |
| QA Lead | ____________ | ____________ | ________ | ________ |

---

## NOTES & ISSUES DURING DEPLOYMENT

```
[Use this space to document any issues or deviations]



```

---

**CRITICAL CONTACTS**

- **On-Call:** [on-call@georgensen.com](mailto:on-call@georgensen.com)
- **Infrastructure Lead:** [infra-lead@georgensen.com](mailto:infra-lead@georgensen.com)
- **Database Admin:** [db-admin@georgensen.com](mailto:db-admin@georgensen.com)
- **Security Team:** [security@georgensen.com](mailto:security@georgensen.com)

**Post-deployment monitoring:** Watch dashboards at https://monitoring.georgensen.com for 48 hours

---

*Keep this checklist up-to-date. Review and update after each deployment.*
