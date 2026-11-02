# 🚚 Georgensen Courier Platform

Enterprise-grade, full-stack global logistics and courier platform built with **FastAPI**, **SQLAlchemy**, **Payrail Payment Rails**, **WebSockets**, and a multi-portal responsive **HTML5/JS** frontend.

---

## 🏗️ System Architecture & Portals

The platform unifies four operational portals and a 14-router REST + WebSocket API under a single deployment:

1. **Public Portal (`/`, `/services`, `/pricing`, `/tracking`, `/customs`, `/locations`, `/careers`, `/contact`)**
   - Instant multi-region quote calculation across **5 global regions** and **46 countries** (`North America`, `Europe`, `Asia-Pacific`, `Middle East & Africa`, `Latin America`).
   - Live public shipment tracking with WebSocket GPS updates and bilingual (`EN`/`FR`) status localization.
   - Full regulatory & legal compliance suite (`/privacy`, `/terms`, `/security`, `/accessibility`, `/ccpa`, `/data-deletion`, `/cookies`, `/dpa`).

2. **Customer Portal (`/customer/dashboard`, `/customer/new-order`, `/customer/orders`, `/customer/tracking`, `/customer/invoices`, `/customer/support`, `/customer/profile`)**
   - Shipment booking with automatic invoice creation and partner auto-assignment.
   - Saved address book management, real-time shipment tracking, invoice payment via **Payrail**, and customer support ticketing.

3. **Partner / Driver Portal (`/partner/partner-dashboard`, `/partner/available-jobs`, `/partner/active-deliveries`, `/partner/earnings`, `/partner/partner-settings`)**
   - Regional job board, one-click job acceptance, active delivery status & GPS updates, Proof of Delivery (POD) signature/photo upload, and multi-currency earnings & payout requests.

4. **Admin & Logistics Operations Portal (`/admin/dashboard`, `/admin/orders`, `/admin/partners`, `/admin/disputes`, `/admin/reports`, `/admin/settings`, `/admin/logs`, `/admin/profile`)**
   - Global KPI dashboard, manual & automated partner assignment, partner KYC/approval workflows, dispute resolution, regional revenue analytics, system configuration, and immutable **Chain-of-Custody** (`ShipmentLog` & `AuthAuditLog`) inspection.

---

## 🔒 Security Architecture

- **Strict Role-Based Access Control (RBAC)**: Self-registration (`POST /api/v1/auth/register`) is strictly restricted to `customer` and `partner` roles, preventing privilege escalation.
- **Object-Level Ownership (IDOR Protection)**: Orders, invoices, payments, support tickets, and disputes verify resource ownership against the authenticated user/customer/partner profile.
- **Brute-Force Rate Limiting & Audit Logging**: Login attempts are tracked in `LoginAttempt` with automatic lockout after 5 failed attempts in 15 minutes; all auth events are recorded in `AuthAuditLog`.
- **HTTP Security Headers**: Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, and `Strict-Transport-Security`.
- **Path Traversal Protection**: Static and HTML file serving validates `.resolve().is_relative_to(frontend_path.resolve())`.

---

## 🚀 Quick Start

### 1. Local Development
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start the server (PYTHONPATH=backend)
npm start
# Or directly with uvicorn:
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Render Cloud Deployment
Configured out-of-the-box via [`render.yaml`](render.yaml) with Python `3.11.8`, `PYTHONPATH=backend`, Payrail payment integration (`PAYRAIL_SECRET_KEY`), and Redis Cloud task queues.
