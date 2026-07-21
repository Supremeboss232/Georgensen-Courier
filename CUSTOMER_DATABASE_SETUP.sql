"""
Customer Portal - Database Setup and Migration Guide
=====================================================

This script documents the SQL schema for the customer portal tables.
The actual table creation is handled by SQLAlchemy's Base.metadata.create_all()
in app/main.py startup event.

For production deployments, use these SQL statements directly or adapt for your
migration tool (Alembic, etc).
"""

# PostgreSQL Schema (Production)
# =================================

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    company_name VARCHAR(255),
    tax_id VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    
    billing_address VARCHAR(500),
    billing_city VARCHAR(100),
    billing_state VARCHAR(2),
    billing_zip VARCHAR(10),
    
    default_return_address VARCHAR(500),
    preferred_service_type VARCHAR(50) DEFAULT 'local',
    preferred_pickup_time VARCHAR(20),
    
    account_type VARCHAR(50) DEFAULT 'individual',
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP WITH TIME ZONE,
    
    total_shipments INTEGER DEFAULT 0,
    total_spent NUMERIC(12, 2) DEFAULT 0.0,
    account_balance NUMERIC(12, 2) DEFAULT 0.0,
    average_rating NUMERIC(3, 1) DEFAULT 0.0,
    
    email_notifications BOOLEAN DEFAULT TRUE,
    sms_notifications BOOLEAN DEFAULT FALSE,
    promotional_emails BOOLEAN DEFAULT TRUE,
    
    internal_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_shipment_date TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);


CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    
    street_address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    postal_code VARCHAR(10) NOT NULL,
    country VARCHAR(100) DEFAULT 'USA',
    
    address_type VARCHAR(50) NOT NULL,  -- residential, business, warehouse
    is_default BOOLEAN DEFAULT FALSE,
    delivery_instructions TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_customer_id (customer_id),
    INDEX idx_is_default (is_default)
);


CREATE TABLE shipments (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    tracking_number VARCHAR(50) NOT NULL UNIQUE,
    
    service_type VARCHAR(50) NOT NULL,  -- local, intercity, international
    speed VARCHAR(50) NOT NULL,  -- economy, standard, express
    status VARCHAR(50) DEFAULT 'order_received',
    
    pickup_contact_name VARCHAR(255) NOT NULL,
    pickup_phone VARCHAR(20) NOT NULL,
    pickup_address VARCHAR(500) NOT NULL,
    pickup_city VARCHAR(100) NOT NULL,
    pickup_state VARCHAR(2) NOT NULL,
    pickup_zip VARCHAR(10) NOT NULL,
    pickup_at TIMESTAMP WITH TIME ZONE,
    
    delivery_contact_name VARCHAR(255) NOT NULL,
    delivery_phone VARCHAR(20) NOT NULL,
    delivery_email VARCHAR(255),
    delivery_address VARCHAR(500) NOT NULL,
    delivery_city VARCHAR(100) NOT NULL,
    delivery_state VARCHAR(2) NOT NULL,
    delivery_zip VARCHAR(10) NOT NULL,
    estimated_delivery TIMESTAMP WITH TIME ZONE,
    actual_delivery TIMESTAMP WITH TIME ZONE,
    
    package_type VARCHAR(100) NOT NULL,
    package_weight NUMERIC(10, 2) NOT NULL,
    package_dimensions VARCHAR(50),
    package_value NUMERIC(12, 2),
    package_description TEXT,
    
    quoted_price NUMERIC(12, 2) NOT NULL,
    actual_cost NUMERIC(12, 2),
    insurance_amount NUMERIC(12, 2) DEFAULT 0.0,
    discount_amount NUMERIC(12, 2) DEFAULT 0.0,
    
    current_location VARCHAR(500),
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    
    special_instructions TEXT,
    delivery_instructions TEXT,
    internal_notes TEXT,
    
    assigned_partner_id INTEGER REFERENCES partners(id) ON DELETE SET NULL,
    assigned_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_customer_id (customer_id),
    INDEX idx_tracking_number (tracking_number),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);


CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    shipment_id INTEGER REFERENCES shipments(id) ON DELETE SET NULL,
    
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50),  -- billing, delivery, lost, damaged, dispute, account, other
    priority VARCHAR(50) DEFAULT 'normal',  -- low, normal, high, urgent
    status VARCHAR(50) DEFAULT 'open',  -- open, in_progress, waiting_customer, resolved, closed
    
    resolution_notes TEXT,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);


CREATE TABLE tracking_events (
    id SERIAL PRIMARY KEY,
    shipment_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    
    event_type VARCHAR(100) NOT NULL,  -- order_received, processing, picked_up, etc
    description TEXT,
    location VARCHAR(500),
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    
    recorded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_shipment_id (shipment_id),
    INDEX idx_created_at (created_at)
);


-- Indexes for performance
CREATE INDEX idx_customers_created_at ON customers(created_at);
CREATE INDEX idx_customers_account_type ON customers(account_type);
CREATE INDEX idx_addresses_customer_id ON addresses(customer_id);
CREATE INDEX idx_shipments_customer_id ON shipments(customer_id);
CREATE INDEX idx_shipments_status ON shipments(status);
CREATE INDEX idx_tracking_events_shipment_id ON tracking_events(shipment_id);
CREATE INDEX idx_support_tickets_customer_id ON support_tickets(customer_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);


-- SQLite Schema (Development)
-- ===========================

-- SQLite doesn't support SERIAL or TIMESTAMP WITH TIME ZONE
-- Adapt the above schema using:
-- - INTEGER PRIMARY KEY AUTOINCREMENT for auto-increment
-- - DATETIME for timestamps
-- - REAL for numeric values with decimals
-- - TEXT for VARCHAR/TEXT

-- Example for SQLite:

CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    
    company_name TEXT,
    tax_id TEXT UNIQUE,
    phone TEXT,
    
    -- ... other fields ...
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Then create indexes:
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_created_at ON customers(created_at);


-- Verification Queries
-- ======================

-- Count customer records
SELECT COUNT(*) FROM customers;

-- List customers with shipment counts
SELECT c.id, c.company_name, COUNT(s.id) as shipment_count
FROM customers c
LEFT JOIN shipments s ON c.id = s.customer_id
GROUP BY c.id, c.company_name
ORDER BY shipment_count DESC;

-- Check support ticket distribution
SELECT category, status, COUNT(*) 
FROM support_tickets
GROUP BY category, status;

-- Find customers with balance
SELECT id, company_name, account_balance, total_spent
FROM customers
WHERE account_balance > 0
ORDER BY account_balance DESC;

-- List pending shipments
SELECT tracking_number, customer_id, status, estimated_delivery
FROM shipments
WHERE status != 'delivered' AND status != 'cancelled'
ORDER BY estimated_delivery;
