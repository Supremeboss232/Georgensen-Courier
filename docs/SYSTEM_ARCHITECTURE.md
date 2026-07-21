# GeorgJensen System Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER PORTAL                               │
│     (Live Tracking, POD View, Shipment Creation)                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Frontend   │
                    │  (React)    │
                    └──────┬──────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────────────┐
│                      FastAPI Backend                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    API Routes                               │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │ • /api/v1/auth/*              (Authentication)             │   │
│  │ • /api/v1/orders/*            (Order Management)           │   │
│  │ • /api/v1/shipments/*         (Shipment Tracking)          │   │
│  │ • /api/v1/logistics/*         (Chain of Custody)  ◄──NEW   │   │
│  │ • /api/v1/logistics/scan      (Barcode Scanning)  ◄──NEW   │   │
│  │ • /api/v1/logistics/deliver   (POD Upload)        ◄──NEW   │   │
│  │ • /api/v1/logistics/webhook/* (Third-Party APIs)  ◄──NEW   │   │
│  │ • /api/v1/admin/*             (Management)                 │   │
│  │ • /api/v1/payments/*          (Payment Processing)         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                           ▲                                          │
│                           │                                          │
│  ┌─────────────────────────┴─────────────────────────────────────┐  │
│  │                   Services Layer                              │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ • auth.py              (JWT, Passwords)                      │  │
│  │ • logistics.py         (Chain of Custody)          ◄──NEW    │  │
│  │ • eta.py               (ETA Calculation)          ◄──NEW    │  │
│  │ • rbac.py              (Role-Based Access)        ◄──NEW    │  │
│  │ • tracking.py          (GPS, Real-time)                      │  │
│  │ • payments.py          (Payments)                            │  │
│  │ • notifications.py     (Email, SMS)                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           ▲                                        │
│                           │                                        │
│  ┌────────────────────────┴──────────────────────────────────┐   │
│  │              Database Models (SQLAlchemy)                 │   │
│  ├───────────────────────────────────────────────────────────┤   │
│  │ Existing Tables:                                          │   │
│  │  • users, customers, partners                             │   │
│  │  • shipments, tracking, orders                            │   │
│  │  • invoices, disputes, support_tickets                    │   │
│  │                                                           │   │
│  │ NEW Tables (Logistics):                                   │   │
│  │  ✓ hubs                 (Warehouses/Distribution)         │   │
│  │  ✓ fleet_vehicles       (Trucks, Vans)                    │   │
│  │  ✓ handlers             (Drivers, Staff)                  │   │
│  │  ✓ shipment_logs        (Audit Trail)          ◄──KEY     │   │
│  │                                                           │   │
│  │ Enhanced Tables:                                          │   │
│  │  • shipments            (+10 new columns)                 │   │
│  │  • users                (+assigned_hub_id)                │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                    │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
    ┌───▼────┐        ┌────▼────┐       ┌────▼────┐
    │  RDS   │        │  Redis  │       │ Celery  │
    │  Postgres       │ (Cache) │       │ (Queue) │
    │  17.6  │        │ Broker  │       │ Workers │
    └────────┘        └─────────┘       └─────────┘
```

---

## Data Flow: Shipment Lifecycle

```
SHIPMENT JOURNEY WITH AUDIT TRAIL

Customer Portal
     │
     │ 1. Create Order
     ▼
┌─────────────────┐
│ order_received  │  ← Log Entry 1: Order received in system
└────────┬────────┘
         │
         │ 2. Payment
         ▼
┌─────────────────┐
│ payment_confirmed
         │
         │ 3. Handler scans at Origin Hub
         ▼
    ┌─────────────────────────────────────────┐
    │ scanned                                  │  ← Log Entry 2
    │ Handler: Jane (NRB Hub)                  │     Handler: Jane
    │ Location: -1.2872, 36.8172              │     Hub: NRB
    │ Barcode: GJ-2026-001                    │     GPS: -1.2872, 36.8172
    └────────┬────────────────────────────────┘
             │
             │ 4. Sorted & Packed
             ▼
    ┌─────────────────────────────────────────┐
    │ sorted → packed                          │  ← Log Entry 3
    │ Vehicle: KCT-100A (Van)                  │     Vehicle: Nissan NV200
    │ Max Capacity: 50 packages                │     Capacity: 50
    └────────┬────────────────────────────────┘
             │
             │ 5. Dispatch from Hub
             ▼
    ┌─────────────────────────────────────────┐
    │ dispatched                               │  ← Log Entry 4
    │ Driver: Robert Mwangi                    │     Handler: Robert
    │ Vehicle: KCT-100A                        │     Vehicle: KCT-100A
    │ Route: NRB → Customer                    │     Route: Planned
    │ ETA: 2 hours                             │     ETA: Updated
    └────────┬────────────────────────────────┘
             │
             │ 6. In Transit (Real-time GPS)
             ▼
    ┌─────────────────────────────────────────┐
    │ in_transit                               │  ← Log Entry 5
    │ Location: Nairobi → CBD                  │     Location: Real-time
    │ GPS: -1.3031, 36.7589                   │     GPS: Current
    │ Next Checkpoint: 5 km                    │     Distance: 5km
    └────────┬────────────────────────────────┘
             │
             │ 7. Out for Final Delivery
             ▼
    ┌─────────────────────────────────────────┐
    │ out_for_delivery                         │  ← Log Entry 6
    │ Driver: Robert                           │     Handler: Robert
    │ Stop #: 3 of 8 today                    │     GPS: Final mile
    │ Address: Office Park, Ln 3               │     Recipient: Waiting
    └────────┬────────────────────────────────┘
             │
             │ 8. DELIVERY (Requires Signature/Photo)
             ▼
    ┌──────────────────────────────────────────────┐
    │ delivered ✓ [LOCKED]                         │  ← Log Entry 7
    │ Recipient: John Doe                          │     Signature: base64
    │ Signature: [Base64 Image]                    │     Photo: URL
    │ Time: 14:32 UTC                              │     Time: Locked
    │ STATUS: READ-ONLY FROM NOW ON                │     Status: Final
    └──────────────────────────────────────────────┘
         │
         │ Chain of Custody Complete
         │ 7 Log Entries Created
         │ Handler Accountability: ✓
         │ Audit Trail: ✓
         │
         ▼
    CUSTOMER CAN VIEW PROOF OF DELIVERY
    + Full Chain of Custody
    + All Handler Names & Timestamps
    + GPS Breadcrumb Trail
```

---

## Role-Based Access Control

```
                    Network Boundary
                    ┌──────────────┐
                    │   Internet   │
                    └──────┬───────┘
                           │ HTTPS
        ┌──────────────────▼──────────────────┐
        │     FastAPI Authentication          │
        │     (JWT Tokens, Password Hash)      │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │        RBAC Service checks          │
        │   has_permission() requires_role()  │
        └──────────┬───────────────────┬──────┘
                   │                   │
    ┌──────────────▼──┐    ┌─────────░────────────────┐
    │  System Admin   │    │  Hub-Scoped Users        │
    │  ✓ Global View  │    │                          │
    │  ✓ All Users    │    │  Warehouse Manager       │
    │  ✓ All Hubs     │    │  ├─ Sees only HUB-NRB   │
    │  ✓ All Metrics  │    │  │                       │
    │  ✓ Reports      │    │  Driver                  │
    └─────────────────┘    │  ├─ Sees only assigned   │
                           │  │   shipments at HUB     │
                           │  │                        │
                           │  Handler                │
                           │  ├─ Scans only at       │
                           │  │   assigned HUB        │
                           │  │                       │
                           │  Customer                │
                           │  └─ Tracks own          │
                           │      shipments only      │
                           └──────────────────────────┘
```

---

## Chain of Custody (Audit Trail)

```
IMMUTABLE SHIPMENT_LOGS TABLE

Shipment: GJ-2026-001

┌────┬─────────┬──────────┬──────────┬──────────────┬───────────┬────────────┐
│ id │ action  │ handler  │ hub      │ location     │ timestamp │ barcode    │
├────┼─────────┼──────────┼──────────┼──────────────┼───────────┼────────────┤
│ 1  │ scanned │ Jane     │ HUB-NRB  │ -1.2872, ... │ 14:00 UTC │ GJ-2026-001
├────┼─────────┼──────────┼──────────┼──────────────┼───────────┼────────────┤
│ 2  │ sorted  │ James    │ HUB-NRB  │ -1.2872, ... │ 14:15 UTC │ Vehicle ABC
├────┼─────────┼──────────┼──────────┼──────────────┼───────────┼────────────┤
│ 3  │ dispatch│ Robert   │ HUB-NRB  │ -1.2872, ... │ 14:30 UTC │ KCT-100A
├────┼─────────┼──────────┼──────────┼──────────────┼───────────┼────────────┤
│ 4  │ in_tran │ Robert   │ HUB-NRB  │ -1.3031, ... │ 14:45 UTC │ GPS signal
├────┼─────────┼──────────┼──────────┼──────────────┼───────────┼────────────┤
│ 5  │ out_for │ Robert   │ HUB-NRB  │ -1.2950, ... │ 15:10 UTC │ GPS signal
├────┼─────────┼──────────┼──────────┼──────────────┼───────────┼────────────┤
│ 6  │ deliver │ Robert   │ NaN      │ -1.2900, ... │ 15:32 UTC │ Signature
│    │         │          │          │              │           │ + Photo    │
└────┴─────────┴──────────┴──────────┴──────────────┴───────────┴────────────┘

PROPERTIES:
✓ Immutable - No DELETE or UPDATE after creation
✓ Indexed - Fast queries by shipment_id, tracking_number, timestamp
✓ Verified - Each log entry verified by handler/GPS/barcode
✓ Legal - Proof of delivery for compliance audits
✓ Accountable - Links handler name to every action
```

---

## ETA Calculation Service

```
┌─────────────────────────────────────────────────────────────────┐
│                    ETA CALCULATION ENGINE                        │
└──────────────────────────────────┬────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
            ┌───────▼────────┐         ┌─────────▼──────┐
            │ DISTANCE       │         │ SPEED MATRIX   │
            │ Calculation    │         │ (by service)   │
            │                │         │                │
            │ Haversine      │         │ Local: 30 km/h │
            │ Formula        │         │ Intercity: 80  │
            │                │         │ International:90
            │ Inputs:        │         │                │
            │ • Current GPS  │         │ Plus buffer:   │
            │ • Destination  │         │ • 30 min service
            │ • Real-time    │         │ • weather/traffic
            │   coordinates  │         │                │
            └────┬──────────┘         └────────┬───────┘
                 │                             │
                 └─────────────┬───────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  ETA = now() +      │
                    │  (dist/speed) +     │
                    │  buffer +           │
                    │  service_delay      │
                    └──────┬───────────────┘
                           │
                    ┌──────▼──────────┐
                    │ Update Shipment │
                    │ estimated_deliv │
                    │ in database      │
                    └─────────────────┘

EXAMPLE:
Current Location: -1.3031, 36.7589 (Nairobi CBD)
Destination: -1.2650, 36.7850 (Office Park, Ln 3)
Distance: ~5 km
Service: Standard Intercity
Speed: 80 km/h
Delays: 30 min
─────────────────────────────────────
Travel Time: 5 km / 80 km/h = 3.75 min
Plus Delays: 30 min
─────────────────────────────────────
ETA: Now + 34 min ≈ 15:59 UTC
```

---

## Database Relationships

```
USERS (Authentication)
  │
  ├─→ CUSTOMERS (Customer Profiles)
  │      └─→ SHIPMENTS (Orders)
  │             ├─→ TRACKING (Status)
  │             ├─→ SHIPMENT_LOGS (NEW) ◄─ AUDIT TRAIL
  │             │     └─→ HANDLERS (Staff)
  │             │          └─→ HUBS
  │             │
  │             ├─→ PROOF_OF_DELIVERY (Signatures)
  │             └─→ INVOICES (Billing)
  │
  ├─→ PARTNERS (Third-party carriers)
  │      └─→ TRACKING (Vehicle status)
  │
  ├─→ HANDLERS (NEW) - Drivers & Staff
  │      ├─→ HUBS (Assigned warehouse)
  │      └─→ SHIPMENT_LOGS (Actions)
  │
  └─→ [Other roles]


HUB (NEW)
  │
  ├─→ FLEET_VEHICLES (NEW)
  │      └─→ [GPS tracking]
  │
  ├─→ HANDLERS (NEW)
  │      └─→ SHIPMENT_LOGS (NEW)
  │
  └─→ SHIPMENTS (NEW columns)
         └─→ origin_hub_id
             destination_hub_id
             current_hub_id
             assigned_handler_id
             assigned_vehicle_id
```

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│              AWS CLOUD INFRASTRUCTURE                    │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │ VPC (vpc-0ba833df2e84992db)                        │ │
│  │ Region: eu-north-1 (Stockholm)                    │ │
│  │                                                    │ │
│  │  ┌─────────────────────────────────────────────┐ │ │
│  │  │     RDS PostgreSQL Instance                 │ │ │
│  │  │  ───────────────────────────────────────    │ │ │
│  │  │  • Instance: georgjensen                    │ │ │
│  │  │  • Engine: PostgreSQL 17.6                  │ │ │
│  │  │  • Class: db.t4g.micro (2vCPU, 1GB)        │ │ │
│  │  │  • Storage: 20 GB (gp2, auto-scale 1TB)    │ │ │
│  │  │  • Backup: Daily (7-day retention)         │ │ │
│  │  │  • Failover: Manual (no Multi-AZ)          │ │ │
│  │  │  • Endpoint: georgjensen....rds.amazonaws  │ │ │
│  │  │              .com:5432                      │ │ │
│  │  │  • Encryption: Enabled                      │ │ │
│  │  │  • Security Group: default (sg-...)        │ │ │
│  │  │                                             │ │ │
│  │  │  Tables Created:                            │ │ │
│  │  │  ├─ users, customers, partners              │ │ │
│  │  │  ├─ shipments ← ENHANCED                    │ │ │
│  │  │  ├─ **hubs** ← NEW                          │ │ │
│  │  │  ├─ **fleet_vehicles** ← NEW                │ │ │
│  │  │  ├─ **handlers** ← NEW                      │ │ │
│  │  │  ├─ **shipment_logs** ← NEW (Audit Trail)  │ │ │
│  │  │  └─ tracking, proof_of_delivery, ...        │ │ │
│  │  └─────────────────────────────────────────────┘ │ │
│  │                                                    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
└──────────────────────────────────────────────────────────┘
         ▲
         │ JDBC/SQLAlchemy
         │
┌────────┴──────────────────────────────────────────────────┐
│           LOCAL / CONTAINER DEPLOYMENT                   │
├─────────────────────────────────────────────────────────  ┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Docker Container (or Local Python)                │ │
│  │  ───────────────────────────────────────────────    │ │
│  │  • Base: Python 3.11+                             │ │
│  │  • Framework: FastAPI + Uvicorn                  │ │
│  │  • Port: 8000                                    │ │
│  │  • Modules:                                      │ │
│  │    - app/api/logistics.py (NEW)                 │ │
│  │    - app/services/logistics.py (NEW)            │ │
│  │    - app/services/eta.py (NEW)                  │ │
│  │    - app/core/rbac.py (NEW)                     │ │
│  │    - [All existing auth, orders, etc.]           │ │
│  │  • Background: Celery workers (Redis broker)     │ │
│  │  • Monitoring: Prometheus on /metrics            │ │
│  │                                                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  LocalRun Ports:                                   │ │
│  │  • API: http://localhost:8000                      │ │
│  │  • Docs: http://localhost:8000/api/docs           │ │
│  │  • Redis: localhost:6379 (Celery broker)          │ │
│  │  • PostgreSQL: localhost:5432 (or RDS endpoint)   │ │
│  │                                                  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## Request Flow: Shipment Scanning

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. DRIVER SCANS PACKAGE AT CHECKPOINT                               │
└─────────────────────────────────────────┬───────────────────────────┘
                                          │
                ┌─────────────────────────▼────────────────────────┐
                │ POST /api/v1/logistics/scan                      │
                │ {                                                │
                │   "tracking_number": "GJ-2026-001"              │
                │   "latitude": -1.2872,                           │
                │   "longitude": 36.8172,                          │
                │   "barcode_scanned": "GJ-2026-001"              │
                │ }                                                │
                └────────────────────┬─────────────────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │ GET CURRENT USER                │
                    │ (From JWT token in header)      │
                    └────────────────┬────────────────┘
                                     │
    ┌────────────────────────────────▼──────────────────────────┐
    │ RBAC CHECK                                                │
    │ • User role = driver ✓                                   │
    │ • Permission: SCAN_PACKAGES ✓                            │
    │ • Hub assignment = HUB-NRB ✓                             │
    └────────────────────────────────┬──────────────────────────┘
                                     │
    ┌────────────────────────────────▼──────────────────────────┐
    │ FIND SHIPMENT                                             │
    │ SELECT * FROM shipments                                  │
    │ WHERE tracking_number = 'GJ-2026-001'                   │
    │ ✓ Found (ID=12345)                                       │
    └────────────────────────────────┬──────────────────────────┘
                                     │
    ┌────────────────────────────────▼──────────────────────────┐
    │ VALIDATE STATE                                            │
    │ if shipment.is_locked: ✗ Raise Error                    │
    │ else: ✓ Continue                                          │
    └────────────────────────────────┬──────────────────────────┘
                                     │
    ┌────────────────────────────────▼──────────────────────────┐
    │ CREATE AUDIT LOG ENTRY (ShipmentLog)                      │
    │ ┌──────────────────────────────────────────────────────┐ │
    │ │ INSERT INTO shipment_logs (                         │ │
    │ │   shipment_id=12345,                               │ │
    │ │   tracking_number='GJ-2026-001',                   │ │
    │ │   action='scanned',                                │ │
    │ │   previous_status='processing',                    │ │
    │ │   new_status='processing',                         │ │
    │ │   handler_id=456,                                 │ │
    │ │   handler_name='Robert Mwangi',                   │ │
    │ │   hub_id=1,                                       │ │
    │ │   hub_name='Nairobi Central Hub',                 │ │
    │ │   latitude=-1.2872,                               │ │
    │ │   longitude=36.8172,                              │ │
    │ │   barcode_scanned='GJ-2026-001',                 │ │
    │ │   is_verified=true,                               │ │
    │ │   verification_method='barcode_scan',             │ │
    │ │   timestamp=now()                                 │ │
    │ │ )                                                 │ │
    │ └──────────────────────────────────────────────────────┘ │
    └────────────────────────────────┬──────────────────────────┘
                                     │
    ┌────────────────────────────────▼──────────────────────────┐
    │ UPDATE SHIPMENT RECORD                                    │
    │ UPDATE shipments SET                                      │
    │   current_hub_id = 1,                                    │
    │   latitude = -1.2872,                                    │
    │   longitude = 36.8172,                                   │
    │   last_location_update = now(),                          │
    │   assigned_handler_id = 456,                             │
    │   updated_at = now()                                     │
    │ WHERE id = 12345                                         │
    └────────────────────────────────┬──────────────────────────┘
                                     │
    ┌────────────────────────────────▼──────────────────────────┐
    │ CALCULATE NEW ETA                                         │
    │ • Current location: -1.2872, 36.8172 (NRB Hub)           │
    │ • Destination: From delivery_address                     │
    │ • Distance: Haversine formula → 5 km                     │
    │ • Speed: Service=Standard, so 40 km/h (local)            │
    │ • ETA = now() + (5/40) + 0.5h = now() + 1.125h          │
    └────────────────────────────────┬──────────────────────────┘
                                     │
    ┌────────────────────────────────▼──────────────────────────┐
    │ RETURN SUCCESS RESPONSE                                   │
    │ {                                                         │
    │   "success": true,                                       │
    │   "message": "Scanned successfully",                    │
    │   "tracking_number": "GJ-2026-001",                     │
    │   "status": "processing",                               │
    │   "log_id": 78901,                                      │
    │   "timestamp": "2026-04-16T15:30:00Z",                 │
    │   "location": "Nairobi Central Hub"                     │
    │ }                                                        │
    └──────────────────────────────────────────────────────────┘
```

---

## Mobile App Integration (Future)

```
┌──────────────────────────────────────────────────────────┐
│          DRIVER MOBILE APP (iOS/Android)                 │
└────────────────┬─────────────────────────────────────────┘
                 │
      ┌──────────▼──────────┐
      │ Features:           │
      │ • GPS Tracking      │
      │ • Route Maps        │
      │ • Barcode Scanner   │
      │   (Camera)          │
      │ • Signature Capture │
      │ • Offline Mode      │
      │ • Push Notify       │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────────────┐
      │ API Endpoints Used:         │
      │                             │
      │ GET /auth/login             │
      │ POST /logistics/scan         │
      │ POST /logistics/deliver     │
      │ PUT /shipments/{id}/location│
      │ GET /shipments/{id}/eta    │
      │ WS /ws/tracking/{track_id} │
      │    (Real-time updates)      │
      └─────────────────────────────┘
```

---

**This architecture ensures production-grade logistics operations with complete accountability and compliance.**

