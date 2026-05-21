-- =============================================================================
-- ✈️ GANGES INTERNATIONAL AIRLINES | CORE NETWORK OPERATIONAL LEDGER
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 0. CLEAN TEARDOWN MATRIX
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS flight_instances CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS aircraft_fleet CASCADE;
DROP TABLE IF EXISTS airports CASCADE;

-- -----------------------------------------------------------------------------
-- 1. SPATIAL TOPOLOGY LAYER
-- -----------------------------------------------------------------------------
CREATE TABLE airports (
    airport_code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(150) NOT NULL,
    country VARCHAR(100) NOT NULL,
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(10, 6) NOT NULL,
    landing_fee_inr NUMERIC(12, 2) NOT NULL DEFAULT 45000.00,
    turnaround_fee_inr NUMERIC(12, 2) NOT NULL DEFAULT 65000.00,
    base_ground_turnaround_minutes INT DEFAULT 45,
    is_operational BOOLEAN DEFAULT TRUE,
    CONSTRAINT chk_geodetic_lat CHECK (latitude BETWEEN -90.0 AND 90.0),
    CONSTRAINT chk_geodetic_lon CHECK (longitude BETWEEN -180.0 AND 180.0)
);

-- -----------------------------------------------------------------------------
-- 2. HETEROGENEOUS ASSET INVENTORY
-- -----------------------------------------------------------------------------
CREATE TABLE aircraft_fleet (
    aircraft_id SERIAL PRIMARY KEY,
    registration_no VARCHAR(15) UNIQUE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    total_seat_capacity INT NOT NULL CHECK (total_seat_capacity > 0),
    fuel_burn_liters_per_km NUMERIC(6, 2) NOT NULL,
    hourly_crew_cost_inr NUMERIC(12, 2) NOT NULL,
    hourly_maint_cost_inr NUMERIC(12, 2) NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. GEODETIC VECTOR EDGES
-- -----------------------------------------------------------------------------
CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    source_airport VARCHAR(10) REFERENCES airports(airport_code) ON DELETE RESTRICT,
    target_airport VARCHAR(10) REFERENCES airports(airport_code) ON DELETE RESTRICT,
    distance_km NUMERIC(10, 2) NOT NULL,
    CONSTRAINT unique_spatial_vector UNIQUE(source_airport, target_airport)
);

-- -----------------------------------------------------------------------------
-- 4. TEMPORAL SCHEDULING MATRIX
-- -----------------------------------------------------------------------------
CREATE TABLE flight_instances (
    flight_id SERIAL PRIMARY KEY,
    route_id INT REFERENCES routes(route_id) ON DELETE RESTRICT,
    aircraft_id INT REFERENCES aircraft_fleet(aircraft_id) ON DELETE RESTRICT,
    departure_timestamp TIMESTAMPTZ NOT NULL,
    arrival_timestamp TIMESTAMPTZ NOT NULL,
    current_seat_liquidity INT NOT NULL,
    CONSTRAINT check_timeline CHECK (arrival_timestamp > departure_timestamp),
    CONSTRAINT check_seat_leakage CHECK (current_seat_liquidity >= 0)
);

-- -----------------------------------------------------------------------------
-- 5. SYNTHETIC PASSENGER METRICS
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    profile_tier VARCHAR(50) DEFAULT 'STANDARD' CHECK (profile_tier IN ('STANDARD', 'INSTITUTIONAL_WHOLESALE', 'QUANT_STRESS_BOT')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 6. THE REALIZED-REVENUE MASTER LEDGER
-- -----------------------------------------------------------------------------
CREATE TABLE bookings (
    booking_id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
    booking_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    simulated_fuel_price_multiplier NUMERIC(4,2) DEFAULT 1.00
);

-- -----------------------------------------------------------------------------
-- 7. ASSET YIELD TRANSACTION LEDGER
-- -----------------------------------------------------------------------------
CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    booking_id INT REFERENCES bookings(booking_id) ON DELETE CASCADE,
    flight_id INT REFERENCES flight_instances(flight_id) ON DELETE RESTRICT, 
    seat_number VARCHAR(10) NOT NULL,
    fare_paid_inr NUMERIC(12, 2) NOT NULL,
    class_tier VARCHAR(20) DEFAULT 'Economy' CHECK (class_tier IN ('Economy', 'Premium Economy', 'Business', 'First Class')),
    CONSTRAINT unique_flight_seat UNIQUE (flight_id, seat_number)
);

-- -----------------------------------------------------------------------------
-- 8. PERFORMANCE TUNING INDEXES
-- -----------------------------------------------------------------------------
CREATE INDEX idx_graph_departure ON flight_instances(departure_timestamp ASC);
CREATE INDEX idx_flight_route_search ON flight_instances(route_id, current_seat_liquidity);
CREATE INDEX idx_ticket_pricing_aggregation ON tickets(flight_id, fare_paid_inr);