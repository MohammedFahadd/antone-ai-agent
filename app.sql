-- Track physical facility configurations
CREATE TABLE facilities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    operating_hours VARCHAR(100),
    gate_policy TEXT
);

-- Unit inventory tracking status and tiered pricing
CREATE TABLE units (
    id SERIAL PRIMARY KEY,
    facility_id INT REFERENCES facilities(id),
    size VARCHAR(20) NOT NULL,          -- e.g., '5x10', '10x20'
    price_monthly DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'Available' -- 'Available', 'Rented', 'Maintenance'
);

-- Tenant records for self-service lookups
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    current_gate_code VARCHAR(20),
    balance_due DECIMAL(10, 2) DEFAULT 0.00
);

-- Handle live booking intent
CREATE TABLE reservations (
    id SERIAL PRIMARY KEY,
    tenant_id INT REFERENCES tenants(id),
    unit_id INT REFERENCES units(id),
    reservation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);