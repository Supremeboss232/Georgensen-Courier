# DEPLOYMENT QUICK START GUIDE

This guide helps you deploy Phase 1 critical fixes to production.

## Prerequisites

✅ Already have:
- FastAPI backend running
- PostgreSQL 15 database
- Stripe account (with webhook endpoint configured)
- Python 3.10+

## Step 1: Pull Latest Code Changes

Your local repository now has:
- 4 new Python files (auth models, middleware, webhooks, payout service)
- 3 enhanced existing files (auth endpoints, user model, invoice model)
- 2 enhanced utility/permission files (security.py, permissions.py)

Verify by checking:
```bash
ls -la backend/app/db/models/auth.py  # Should exist
ls -la backend/app/api/webhooks.py    # Should exist
ls -la backend/app/services/payout.py # Should exist
```

## Step 2: Run Database Migrations

### Create New Tables

```sql
-- Run in PostgreSQL as admin

-- 1. Email Verification Table
CREATE TABLE email_verifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_email_verification_user ON email_verifications(user_id);
CREATE INDEX idx_email_verification_token ON email_verifications(token);

-- 2. Refresh Token Table (for revocation support)
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45),
    user_agent VARCHAR(1000),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_refresh_token_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_token_jti ON refresh_tokens(token_jti);

-- 3. Auth Audit Log Table (IMMUTABLE - never update, only insert)
CREATE TABLE auth_audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(1000),
    success BOOLEAN NOT NULL,
    reason VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_auth_audit_event ON auth_audit_logs(event_type);
CREATE INDEX idx_auth_audit_user ON auth_audit_logs(user_id);
CREATE INDEX idx_auth_audit_success ON auth_audit_logs(success);
CREATE INDEX idx_auth_audit_created ON auth_audit_logs(created_at DESC);

-- 4. Password Reset Table
CREATE TABLE password_resets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_password_reset_user ON password_resets(user_id);
CREATE INDEX idx_password_reset_token ON password_resets(token);

-- 5. Login Attempt Table (for rate limiting)
CREATE TABLE login_attempts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    success BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_login_attempts_email_ip ON login_attempts(email, ip_address);
CREATE INDEX idx_login_attempts_created ON login_attempts(created_at DESC);
```

### Modify Existing Tables

```sql
-- 6. Add fields to users table
ALTER TABLE users 
    ADD COLUMN is_email_verified BOOLEAN DEFAULT FALSE,
    ADD COLUMN verified_at TIMESTAMP WITH TIME ZONE;
    
-- 7. Add fields to invoices table (Stripe integration)
ALTER TABLE invoices
    ADD COLUMN stripe_payment_intent_id VARCHAR(255) UNIQUE,
    ADD COLUMN stripe_charge_id VARCHAR(255) UNIQUE,
    ADD COLUMN refund_amount FLOAT DEFAULT 0.0,
    ADD COLUMN refunded_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN dispute_id VARCHAR(255),
    ADD COLUMN failure_reason TEXT;

-- Rename column for consistency
ALTER TABLE invoices 
    RENAME COLUMN paid_date TO paid_at;

-- Create indexes for webhook lookups
CREATE INDEX idx_invoice_stripe_intent ON invoices(stripe_payment_intent_id);
CREATE INDEX idx_invoice_stripe_charge ON invoices(stripe_charge_id);
CREATE INDEX idx_invoice_customer_status ON invoices(customer_id, status);
CREATE INDEX idx_invoice_created_status ON invoices(created_at DESC, status);
```

## Step 3: Update Environment Variables

Add these to your `.env` file:

```bash
# Stripe Webhook Secret (get from Stripe Dashboard → Webhooks)
STRIPE_WEBHOOK_SECRET=whsec_test_xxxxxxxxxxxxx

# Email Service Configuration (for verification/reset emails)
SMTP_HOST=smtp.gmail.com  # Or sendgrid, mailgun, etc.
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@georgensencourier.com

# JWT Configuration
JWT_SECRET_KEY=your-long-random-secret-at-least-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS=7

# App Configuration
APP_NAME=Georgensen Courier
APP_ENV=production
```

## Step 4: Update FastAPI App Initialization

In `backend/app/main.py`, add middleware initialization:

```python
from app.core.middleware import (
    RateLimitMiddleware,
    AuditLoggingMiddleware,
    SecurityHeadersMiddleware
)

# Add these after app initialization
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include webhook routes
from app.api import webhooks
app.include_router(webhooks.router)
```

## Step 5: Configure Stripe Webhook in Dashboard

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://your-api.com/api/v1/webhooks/stripe`
4. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
   - `charge.dispute.created`
5. Copy Webhook Signing Secret → Add to `.env` as `STRIPE_WEBHOOK_SECRET`

## Step 6: Test Locally

### Test Email Verification Flow

```bash
# 1. Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "phone": "+1234567890"
  }'

# Expected: User created but is_email_verified=false

# 2. Try to login (should fail - email not verified)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Expected: 403 "Please verify your email before logging in"

# 3. Get verification token from database
psql georgensen -c "SELECT token FROM email_verifications WHERE user_id = (SELECT id FROM users WHERE email = 'test@example.com') LIMIT 1;"

# 4. Verify email
curl -X POST http://localhost:8000/api/v1/auth/email-verification/verify \
  -H "Content-Type: application/json" \
  -d '{"token": "your-token-here"}'

# Expected: "Email verified successfully"

# 5. Now login should work
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Expected: access_token, refresh_token returned
```

### Test Stripe Webhook (Development)

Using Stripe CLI (installed locally):

```bash
# 1. Start listening to webhooks
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe

# 2. In another terminal, trigger a test event
stripe trigger payment_intent.succeeded

# Expected: Webhook received, processed, and logged
```

### Test Rate Limiting

```bash
# Should succeed (1st attempt)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "wrong"}'

# Should fail with 401 (invalid credentials)
# Repeat 5 times (might take 60 seconds)
# On 6th attempt within 60 seconds: Should get 429 "Too many attempts"
```

## Step 7: Deploy to Production

```bash
# 1. Run database migrations (use Alembic if available)
alembic upgrade head

# Or run SQL files manually via pgAdmin

# 2. Restart FastAPI server
systemctl restart georgensen-api

# Or with Docker:
docker-compose restart backend

# 3. Verify services are running
curl https://your-api.com/api/v1/health

# Expected: {"status": "ok"}

# 4. Test webhook endpoint is accessible
curl https://your-api.com/api/v1/webhooks/stripe

# Expected: 405 Method Not Allowed (POST only)
```

## Step 8: Monitor for Issues

### Check Logs

```bash
# View recent authentication events
psql georgensen -c "
  SELECT event_type, success, COUNT(*) as count
  FROM auth_audit_logs
  WHERE created_at > NOW() - INTERVAL '1 hour'
  GROUP BY event_type, success
  ORDER BY created_at DESC
  LIMIT 20;
"

# View failed login attempts
psql georgensen -c "
  SELECT email, ip_address, COUNT(*) as attempts
  FROM login_attempts
  WHERE success = false
    AND created_at > NOW() - INTERVAL '1 hour'
  GROUP BY email, ip_address
  ORDER BY attempts DESC;
"

# View webhook processing
psql georgensen -c "
  SELECT status, COUNT(*) 
  FROM invoices 
  WHERE updated_at > NOW() - INTERVAL '1 day'
  GROUP BY status;
"
```

### Common Issues & Fixes

**Issue: "is_email_verified column not found"**
- Solution: Run migration to add column to users table

**Issue: Auth endpoints return 404**
- Solution: Make sure `app.include_router(auth.router)` is in main.py

**Issue: Stripe webhooks not processing**
- Solution: Check STRIPE_WEBHOOK_SECRET is correct
- Solution: Verify webhook endpoint is publicly accessible (not localhost)

**Issue: Rate limiting too strict/loose**
- Solution: Adjust `max_attempts=5` parameter in `check_rate_limit()` function
- Location: `backend/app/api/auth.py` line ~72

## Step 9: Update Frontend (If Needed)

### New Endpoints Available

After Phase 1, frontend should use:

```javascript
// Registration with email verification
POST /api/v1/auth/register
// Response: User object (is_email_verified=false)
// Frontend shows: "Verify your email to continue"

// Email verification
POST /api/v1/auth/email-verification/verify
// Input: {token: "xxx"}
// Response: {message: "Email verified successfully"}

// Login (now requires email verified)
POST /api/v1/auth/login

// Logout (now revokes tokens)
POST /api/v1/auth/logout
// Requires: access token
// Effect: Refresh token is invalidated

// Password reset
POST /api/v1/auth/password-reset/request
// Input: {email: "user@example.com"}

POST /api/v1/auth/password-reset/verify
// Input: {token: "xxx", new_password: "NewPass123!"}
```

## Step 10: Update Documentation

- [ ] Update API documentation with new endpoints
- [ ] Add authentication flow diagram
- [ ] Document webhook events
- [ ] Create support article about email verification

## Validation Checklist

Before going live:

- [ ] All 5 new database tables created
- [ ] users table has is_email_verified column
- [ ] invoices table has Stripe fields
- [ ] Database indexes created successfully
- [ ] Environment variables configured
- [ ] Stripe webhook endpoint configured and tested
- [ ] Email service configured (test send an email)
- [ ] Auth endpoints accessible and working
- [ ] Rate limiting functional (test with 5 failed logins)
- [ ] Ownership checks working (can't access other user's data)
- [ ] Webhook signature verification working
- [ ] All tests passing (unit and integration)
- [ ] Monitoring and logging configured
- [ ] Backup and disaster recovery tested

## Support

If you encounter issues:

1. Check logs: `tail -f /var/log/georgensen-api.log`
2. Check database: `psql georgensen -c "SELECT * FROM auth_audit_logs ORDER BY created_at DESC LIMIT 5;"`
3. Test endpoints with curl/Postman
4. Refer to main deployment guide: `docs/DEPLOYMENT.md`

---

**Expected Deployment Time**: 1-2 hours for experienced DevOps engineer

This unlocks enterprise sales by providing:
✅ Secure authentication with email verification
✅ Token revocation and logout support  
✅ Rate limiting against brute force
✅ Authorization enforcement (no cross-customer data leaks)
✅ Payment reconciliation with Stripe
✅ Partner payout automation
