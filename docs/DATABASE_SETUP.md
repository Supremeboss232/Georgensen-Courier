# GeorgJensen Production Database Setup

## AWS RDS PostgreSQL Configuration

**Instance:** georgjensen  
**Engine:** PostgreSQL 17.6  
**Endpoint:** `georgjensen.cf2w2gwcmvc8.eu-north-1.rds.amazonaws.com:5432`  
**Region:** eu-north-1 (Stockholm)  
**Instance Class:** db.t4g.micro (2 vCPU, 1 GB RAM)  
**Storage:** 20 GiB (gp2, autoscaling to 1000 GiB max)  

**Master Credentials:**
- Username: `georgjensen`
- Password: `Supposedbe5`
- Database: `georgjensen`

**Networking:**
- VPC: vpc-0ba833df2e84992db
- Security Group: default (sg-07a0b2e18bc453ee5)
- Publicly accessible: No
- Multi-AZ: No

---

## Backend Configuration

### 1. Update Environment Variables

Create a `.env` file in `backend/` directory:

```bash
# Database (Production RDS)
DATABASE_URL=postgresql://georgjensen:Supposedbe5@georgjensen.cf2w2gwcmvc8.eu-north-1.rds.amazonaws.com:5432/georgjensen

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-secure-random-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=["http://localhost:8000", "http://localhost:3000"]

# Email Configuration
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# Redis (for Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run Database Migrations

```bash
# Option A: Use the initialization script (recommended)
python scripts/init_db.py

# Option B: Manual migration steps
# Step 1: Run Alembic migrations
alembic upgrade head

# Step 2: Seed initial data
python scripts/seed_logistics.py
```

---

## Verification Checklist

After initialization, verify the setup:

### 1. Check Database Connection

```python
python -c "
from app.core.config import settings
from app.db.base import engine
from sqlalchemy import inspect

# Test connection
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'Connected! Found {len(tables)} tables:')
for table in tables:
    print(f'  - {table}')
"
```

### 2. Verify Tables Created

Expected tables:
- ✓ users
- ✓ customers
- ✓ partners
- ✓ shipments
- ✓ tracking
- ✓ tracking_history
- ✓ proof_of_delivery
- ✓ **hubs** (NEW)
- ✓ **fleet_vehicles** (NEW)
- ✓ **handlers** (NEW)
- ✓ **shipment_logs** (NEW - Audit Trail)

### 3. Test API Connection

```bash
# Start the server
python -m uvicorn app.main:app --reload

# In another terminal, test endpoints
curl -X GET http://localhost:8000/api/docs

# Test logistics endpoint
curl -X GET http://localhost:8000/api/v1/logistics/hub/1/activity \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Create Test Shipment

Run the seed script which creates test users with credentials:

**System Admin:**
```
Email: admin@georjensen.local
Password: Admin@GeorgJensen123
Role: system_admin
```

**Warehouse Manager (Nairobi):**
```
Email: manager.nrb@georjensen.local
Password: Manager@123
Role: warehouse_manager
Hub: HUB-NRB (Nairobi Central)
```

**Driver (Nairobi):**
```
Email: driver.nrb.1@georjensen.local
Password: Driver@123
Role: driver
Hub: HUB-NRB
```

**Handler/Warehouse Staff:**
```
Email: handler.nrb.1@georjensen.local
Password: Handler@123
Role: handler
Hub: HUB-NRB
```

---

## Database Schema Overview

### Core Tables

#### `hubs` - Warehouse/Distribution Centers
- Stores location, capacity, operating hours
- Indexes on: code, name, city, created_at
- Related to: fleet_vehicles, handlers, shipments

#### `fleet_vehicles` - Trucks, Vans, Motorcycles
- Tracks vehicle capacity, location, status, maintenance
- Indexes on: plate_number (unique), hub_id, created_at
- Linked to hubs and handlers

#### `handlers` - Drivers & Warehouse Staff
- Employee information, performance metrics
- Types: warehouse_staff, driver
- Linked to users and hubs

#### `shipment_logs` - Complete Audit Trail (Chain of Custody)
- IMMUTABLE record of every shipment action
- Actions: scanned, dispatched, delivered, etc.
- Indexes on: shipment_id, tracking_number, action, timestamp
- Critical for logistics compliance

### Updated Tables

#### `shipments` - Enhanced with Logistics Fields
**New columns:**
- `origin_hub_id` - Where package originates
- `destination_hub_id` - Where package goes
- `current_hub_id` - Where package is now
- `assigned_handler_id` - Current responsible handler
- `assigned_vehicle_id` - Current vehicle assignment
- `is_locked` - Read-only flag once delivered
- `delivery_proof_signature` - Base64 signature
- `delivery_proof_photo` - Proof of delivery photo
- `signature_required` - POD requirement flag
- `last_location_update` - Last GPS update timestamp

#### `users` - Enhanced with Hub Assignment
**New column:**
- `assigned_hub_id` - Which hub this user manages/works at

---

## Seeded Data

The `seed_logistics.py` script creates:

### Hubs
1. **HUB-NRB** - Nairobi Central Hub (Regional)
   - Coordinates: -1.2872, 36.8172
   - Capacity: 5000 packages
   - Manager: Jane Kimani

2. **HUB-MBA** - Mombasa Port Hub (Regional)
   - Coordinates: -4.0435, 39.6682
   - Capacity: 4000 packages
   - Manager: Ahmed Hassan

3. **HUB-KSME** - Kisumu East Hub
   - Coordinates: -0.1022, 34.7617
   - Capacity: 2000 packages
   - Manager: Peter Omondi

4. **HUB-NKR** - Nakuru Distribution Center
   - Coordinates: -0.3031, 36.0800
   - Capacity: 3000 packages
   - Manager: Faith Kipchoge

### Fleet
- 5 vehicles total
- Mix of vans, trucks, and cars
- Distributed across hubs

### Staff
- 1 System Admin
- 1 Warehouse Manager (Nairobi)
- 3 Drivers
- 2 Warehouse Handlers

---

## Troubleshooting

### Connection Errors

**Error:** `FATAL: no password supplied`
```bash
# Solution: Check DATABASE_URL in config.py
# Format: postgresql://user:password@host:port/dbname
# Ensure special characters in password are URL-encoded
```

**Error:** `ERROR Could not connect to RDS endpoint`
```bash
# Solution: Check security group rules
# Ensure your machine's IP is allowed in RDS security group
# AWS Console → RDS → Security Groups → Inbound Rules
```

### Migration Errors

**Error:** `Alembic couldn't find migration script`
```bash
# Solution: Ensure alembic/versions/001_add_logistics_models.py exists
# Run: ls alembic/versions/
```

**Error:** `Column 'xxx' already exists`
```bash
# Solution: Migration script may have partially run
# Check current migration: alembic current
# Downgrade if needed: alembic downgrade -1
```

### Seed Script Errors

**Error:** `ModuleNotFoundError: No module named 'app'`
```bash
# Solution: Run from backend directory
cd backend
python scripts/seed_logistics.py
```

**Error:** `ForeignKeyError: Could not create foreign key`
```bash
# Solution: Ensure migrations ran first
# Run: alembic upgrade head
```

---

## Production Checklist

- [ ] RDS endpoint configured in settings
- [ ] psycopg2 installed (PostgreSQL driver)
- [ ] Alembic migrations applied
- [ ] Seed data created
- [ ] Test users created and verified
- [ ] API endpoints responding
- [ ] Security group allows application IP
- [ ] Database backups configured
- [ ] Monitoring/alerting set up
- [ ] Read replicas configured (if heavy traffic)
- [ ] Multi-AZ failover enabled (optional)

---

## Backup & Recovery

### Manual Backup

```bash
# Using pg_dump (PostgreSQL CLI tool)
pg_dump -h georgjensen.cf2w2gwcmvc8.eu-north-1.rds.amazonaws.com \
        -U georgjensen \
        -d georgjensen \
        -f database_backup_$(date +%Y%m%d).sql
```

### Automated Backups

AWS RDS automatically maintains backups with:
- **Retention Period:** 7 days (configurable)
- **Backup Window:** Daily during maintenance window
- **Point-in-time Recovery:** Available for 7 days

### Restore from Backup

Via AWS Console:
1. RDS Dashboard → Databases → georgjensen
2. Actions → Restore to Point in Time
3. Select restore point and create new instance
4. Update application connection string

---

## Next Steps

1. **Frontend Development**
   - System Admin Dashboard (analytics, user management)
   - Warehouse Manager Dashboard (hub operations)
   - Driver Dashboard (route maps, deliveries, POD)
   - Handler Dashboard (barcode scanning, sorting)
   - Customer Dashboard (live tracking, POD view)

2. **Integration**
   - Third-party carrier APIs (FedEx, UPS)
   - Google Maps for ETA/routing
   - SMS notifications for customers
   - Payment system for driver payouts

3. **Barcode & Mobile**
   - Barcode scanner device integration
   - GPS tracking for vehicles
   - Mobile apps for drivers/handlers
   - Signature capture at delivery

4. **Monitoring & Observability**
   - Prometheus metrics for logistics operations
   - Alerts for failed deliveries
   - Performance tracking by handler/vehicle
   - Real-time hub capacity monitoring

---

## Support

For issues or questions about the database setup, review:
- PostgreSQL documentation: https://www.postgresql.org/docs/17/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Alembic docs: https://alembic.sqlalchemy.org/
- AWS RDS docs: https://docs.aws.amazon.com/rds/
