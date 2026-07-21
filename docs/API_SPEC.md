# API Specification - Georgensen Courier

**Version**: 1.0.0  
**Base URL**: `http://localhost:8000/api/v1` (development)  
**Auth**: JWT Bearer Token in Authorization header

---

## Authentication Endpoints

### Register User
Create a new user account (customer, partner, or admin).

**Endpoint**: `POST /auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "phone": "+234800000000",
  "role": "customer"  // or "partner", "admin"
}
```

**Response (201 Created)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+234800000000",
  "role": "customer",
  "status": "active",
  "created_at": "2026-02-04T10:00:00Z"
}
```

**Errors**:
- `400 Bad Request`: Email already registered
- `422 Unprocessable Entity`: Invalid input data

---

### Login
Authenticate and receive JWT tokens.

**Endpoint**: `POST /auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors**:
- `401 Unauthorized`: Invalid email or password
- `403 Forbidden`: User account is disabled

---

### Refresh Token
Get a new access token using refresh token.

**Endpoint**: `POST /auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### Get Current User
Retrieve authenticated user profile.

**Endpoint**: `GET /auth/me`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response (200 OK)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+234800000000",
  "role": "customer",
  "status": "active"
}
```

---

## Orders Endpoints

### Get Shipping Quote
Calculate shipping cost before creating order.

**Endpoint**: `POST /orders/quote`

**Request Body**:
```json
{
  "service_type": "local",  // "local", "intercity", "international"
  "distance": 15.5,
  "weight": 2.5,
  "speed": "standard",  // "economy", "standard", "express"
  "package_value": 50000
}
```

**Response (200 OK)**:
```json
{
  "base_fare": 5.0,
  "distance_charge": 7.75,
  "weight_charge": 5.0,
  "speed_multiplier": 1.0,
  "insurance_charge": 2500.0,
  "subtotal": 17.75,
  "total_price": 2517.75,
  "breakdown": {
    "base": 5.0,
    "distance": 7.75,
    "weight": 5.0,
    "speed": "standard x 1.0",
    "insurance": 2500.0
  }
}
```

---

### Create Order
Submit new delivery order.

**Endpoint**: `POST /orders/`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "service_type": "local",
  "speed": "standard",
  "pickup_address": "123 Main St, Lagos",
  "delivery_address": "456 King St, Abuja",
  "pickup_contact": "+234801234567",
  "delivery_contact": "+234807654321",
  "delivery_email": "recipient@example.com",
  "package_weight": 2.5,
  "package_value": 50000
}
```

**Response (201 Created)**:
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "tracking_number": "GEO-26-AB12CD",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "service_type": "local",
  "speed": "standard",
  "status": "pending",
  "total_price": 2517.75,
  "created_at": "2026-02-04T10:30:00Z",
  "payment_status": "pending"
}
```

---

### List Orders
Get user's orders (filtered by role).

**Endpoint**: `GET /orders/?skip=0&limit=10&status=pending`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Query Parameters**:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Number of records to return (default: 10)
- `status` (string, optional): Filter by status (pending, confirmed, delivered, etc.)

**Response (200 OK)**:
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "tracking_number": "GEO-26-AB12CD",
    "status": "pending",
    "total_price": 2517.75,
    "created_at": "2026-02-04T10:30:00Z"
  }
]
```

---

### Get Order Details
Retrieve complete order information.

**Endpoint**: `GET /orders/{order_id}`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response (200 OK)**:
```json
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "tracking_number": "GEO-26-AB12CD",
  "customer_id": "550e8400-e29b-41d4-a716-446655440000",
  "assigned_partner_id": "660e8400-e29b-41d4-a716-446655440001",
  "service_type": "local",
  "speed": "standard",
  "status": "in_transit",
  "payment_status": "completed",
  "base_fare": 5.0,
  "distance_charge": 7.75,
  "weight_charge": 5.0,
  "insurance_charge": 2500.0,
  "total_price": 2517.75,
  "pickup_address": "123 Main St, Lagos",
  "delivery_address": "456 King St, Abuja",
  "package_weight": 2.5,
  "package_value": 50000,
  "created_at": "2026-02-04T10:30:00Z",
  "updated_at": "2026-02-04T11:00:00Z"
}
```

---

### Update Order Status
Update delivery status (partner/admin only).

**Endpoint**: `PATCH /orders/{order_id}/status`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "status": "in_transit"
}
```

**Valid Statuses**:
- `pending` - Awaiting partner assignment
- `confirmed` - Partner assigned
- `picked_up` - Item collected
- `in_transit` - On delivery route
- `delivered` - Successfully delivered
- `cancelled` - Order cancelled

---

### Track Order by Number
Public tracking endpoint (no authentication).

**Endpoint**: `GET /orders/{tracking_number}/track`

**Response (200 OK)**:
```json
{
  "tracking_number": "GEO-26-AB12CD",
  "status": "in_transit",
  "pickup_address": "123 Main St, Lagos",
  "delivery_address": "456 King St, Abuja",
  "current_location": "Ikeja, Lagos",
  "created_at": "2026-02-04T10:30:00Z",
  "updated_at": "2026-02-04T11:45:00Z"
}
```

---

## Partners Endpoints

### Register as Partner
Create delivery partner account.

**Endpoint**: `POST /partners/register`

**Request Body**:
```json
{
  "email": "driver@example.com",
  "password": "SecurePass123!",
  "full_name": "Ahmed Rider",
  "phone": "+234809876543",
  "profile": {
    "vehicle_type": "motorbike",
    "services": ["local", "intercity"],
    "plate_number": "LGS-123ABC"
  }
}
```

---

### Get Partner Profile
Retrieve authenticated partner's profile.

**Endpoint**: `GET /partners/me`

**Headers**:
```
Authorization: Bearer {partner_token}
```

---

### Get Assigned Orders
Retrieve orders assigned to partner.

**Endpoint**: `GET /partners/assigned-orders?status=in_transit&skip=0&limit=10`

**Response (200 OK)**:
```json
[
  {
    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "tracking_number": "GEO-26-AB12CD",
    "customer_name": "John Doe",
    "status": "in_transit",
    "pickup_address": "123 Main St, Lagos",
    "delivery_address": "456 King St, Abuja",
    "total_price": 2517.75,
    "assigned_at": "2026-02-04T10:45:00Z"
  }
]
```

---

### Accept Order
Partner accepts job assignment.

**Endpoint**: `POST /partners/accept-order/{order_id}`

**Headers**:
```
Authorization: Bearer {partner_token}
```

**Response (200 OK)**:
```json
{
  "message": "Order accepted",
  "order_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "tracking_number": "GEO-26-AB12CD"
}
```

---

### Get Earnings Summary
Retrieve partner earnings and statistics.

**Endpoint**: `GET /partners/earnings?period=monthly`

**Response (200 OK)**:
```json
{
  "partner_id": "660e8400-e29b-41d4-a716-446655440001",
  "total_earnings": 125000.50,
  "pending_earnings": 25000.00,
  "completed_orders": 47,
  "average_per_order": 2659.59,
  "period": "monthly",
  "earnings_list": [
    {
      "order_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "delivery_fee": 2517.75,
      "commission_amount": 377.66,
      "net_earnings": 2140.09,
      "status": "completed",
      "created_at": "2026-02-04T15:00:00Z"
    }
  ]
}
```

---

## Tracking Endpoints

### Public Tracking
Get real-time tracking information (no auth required).

**Endpoint**: `GET /tracking/{tracking_number}`

**Response (200 OK)**:
```json
{
  "tracking_number": "GEO-26-AB12CD",
  "status": "in_transit",
  "current_location": "Ikeja, Lagos",
  "estimated_delivery": "2026-02-04T14:00:00Z",
  "history": [
    {
      "status": "picked_up",
      "location": "Main Warehouse",
      "timestamp": "2026-02-04T10:45:00Z",
      "notes": "Package collected from sender"
    },
    {
      "status": "in_transit",
      "location": "Ikeja, Lagos",
      "timestamp": "2026-02-04T11:30:00Z",
      "notes": "On delivery route"
    }
  ]
}
```

---

### Update Delivery Location
Partner updates current location.

**Endpoint**: `POST /tracking/update-location`

**Headers**:
```
Authorization: Bearer {partner_token}
```

**Request Body**:
```json
{
  "shipment_id": "550e8400-e29b-41d4-a716-446655440000",
  "latitude": 6.5244,
  "longitude": 3.3792,
  "location": "Ikeja, Lagos",
  "notes": "At delivery point, calling customer"
}
```

---

### Submit Proof of Delivery
Partner uploads delivery evidence.

**Endpoint**: `POST /tracking/submit-proof-of-delivery`

**Headers**:
```
Authorization: Bearer {partner_token}
```

**Request Body**:
```json
{
  "shipment_id": "550e8400-e29b-41d4-a716-446655440000",
  "recipient_name": "Jane Doe",
  "delivery_notes": "Delivered to office receptionist",
  "signature_path": "/uploads/signatures/sig-001.png",
  "photo_path": "/uploads/photos/photo-001.jpg"
}
```

**Response (200 OK)**:
```json
{
  "message": "Proof of delivery submitted",
  "shipment_id": "550e8400-e29b-41d4-a716-446655440000",
  "recipient_name": "Jane Doe",
  "delivery_time": "2026-02-04T12:30:00Z"
}
```

---

## Admin Endpoints

### Admin Dashboard
Get system KPIs and statistics.

**Endpoint**: `GET /admin/dashboard`

**Headers**:
```
Authorization: Bearer {admin_token}
```

**Response (200 OK)**:
```json
{
  "users": {
    "total": 1250,
    "customers": 1000,
    "partners": 200,
    "admins": 50
  },
  "orders": {
    "total": 8500,
    "delivered": 7950,
    "delivery_rate": 93.5
  },
  "revenue": {
    "total": 2125000.50,
    "average_order": 250.00
  }
}
```

---

### List All Users
Get all system users with filters.

**Endpoint**: `GET /admin/users?role=partner&status=active&skip=0&limit=50`

**Headers**:
```
Authorization: Bearer {admin_token}
```

**Response (200 OK)**:
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "email": "driver@example.com",
    "full_name": "Ahmed Rider",
    "role": "partner",
    "status": "active",
    "phone": "+234809876543",
    "created_at": "2026-01-15T10:00:00Z"
  }
]
```

---

### Update User Status
Enable or disable user account.

**Endpoint**: `PATCH /admin/users/{user_id}/status`

**Headers**:
```
Authorization: Bearer {admin_token}
```

**Request Body**:
```json
{
  "status": "disabled"  // or "active", "suspended"
}
```

---

### List Disputes
Get all customer disputes.

**Endpoint**: `GET /admin/disputes?status=pending&skip=0&limit=50`

**Response (200 OK)**:
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "tracking_number": "GEO-26-AB12CD",
    "dispute_type": "delayed",
    "status": "pending",
    "filed_by": "John Doe",
    "created_at": "2026-02-04T13:00:00Z"
  }
]
```

---

### Resolve Dispute
Update dispute resolution.

**Endpoint**: `PATCH /admin/disputes/{dispute_id}/resolve`

**Headers**:
```
Authorization: Bearer {admin_token}
```

**Request Body**:
```json
{
  "resolution": "Full refund issued",
  "refund_amount": 2517.75
}
```

---

## Error Responses

All endpoints may return these error codes:

### 400 Bad Request
```json
{
  "detail": "Invalid input data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to perform this action"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **General endpoints**: 10 requests/second
- **API endpoints**: 100 requests/second
- **Authentication**: 5 requests/minute per IP

Rate limit info returned in response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1675341600
```

---

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `skip` (int): Number of items to skip (default: 0)
- `limit` (int): Number of items per page (default: 10, max: 100)

**Response Metadata**:
```json
{
  "items": [...],
  "total": 250,
  "skip": 0,
  "limit": 10,
  "pages": 25
}
```

---

## Data Types & Formats

### Timestamps
All timestamps are in ISO 8601 format (UTC):
```
2026-02-04T10:30:00Z
```

### UUIDs
All IDs are UUID v4 format:
```
550e8400-e29b-41d4-a716-446655440000
```

### Phone Numbers
International format with country code:
```
+234800000000
+1-555-123-4567
```

### Currency
All amounts in Nigerian Naira (₦), returned as float:
```
2517.75  // ₦2,517.75
```

---

**Last Updated**: February 4, 2026  
**Documentation Version**: 1.0.0
