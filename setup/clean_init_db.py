import os
import sqlalchemy
from sqlalchemy import text

# Pull target cloud environment string directly from system environment variables
NEON_DB_URI = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:admin123@ep-ganges-aviation-pool.east-us-2.aws.neon.tech/gi_aviation_db?sslmode=require"
)
engine = sqlalchemy.create_engine(NEON_DB_URI)

def build_relational_schema():
    print("🚀 Initializing Ganges International Quant Operational Network Database Rebuild...")
    
    schema_queries = [
        # Clean teardown with cascading to prevent foreign key deadlocks during rebuild
        "DROP TABLE IF EXISTS tickets CASCADE;",
        "DROP TABLE IF EXISTS bookings CASCADE;",
        "DROP TABLE IF EXISTS users CASCADE;",
        "DROP TABLE IF EXISTS flight_instances CASCADE;",
        "DROP TABLE IF EXISTS routes CASCADE;",
        "DROP TABLE IF EXISTS aircraft_fleet CASCADE;",
        "DROP TABLE IF EXISTS airports CASCADE;",
        
        # 1. SPATIAL TOPOLOGY LAYER (Network Nodes with Fee Matrices)
        """
        CREATE TABLE airports (
            airport_code VARCHAR(10) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            city VARCHAR(150) NOT NULL,
            country VARCHAR(10) NOT NULL,
            latitude NUMERIC(10, 6) NOT NULL,
            longitude NUMERIC(10, 6) NOT NULL,
            landing_fee_inr NUMERIC(12, 2) NOT NULL DEFAULT 45000.00,    -- L_origin
            turnaround_fee_inr NUMERIC(12, 2) NOT NULL DEFAULT 65000.00, -- T_dest
            base_ground_turnaround_minutes INT DEFAULT 45,
            is_operational BOOLEAN DEFAULT TRUE
        );
        """,
        
        # 2. HETEROGENEOUS ASSET INVENTORY (Fleet Profiles for Variable Cost Calculations)
        """
        CREATE TABLE aircraft_fleet (
            aircraft_id SERIAL PRIMARY KEY,
            registration_no VARCHAR(15) UNIQUE NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            total_seat_capacity INT NOT NULL CHECK (total_seat_capacity > 0),
            fuel_burn_liters_per_km NUMERIC(6, 2) NOT NULL, -- The κ_a asset coefficient
            hourly_crew_cost_inr NUMERIC(12, 2) NOT NULL,   -- The C_crew baseline
            hourly_maint_cost_inr NUMERIC(12, 2) NOT NULL   -- The M_maint baseline
        );
        """,
        
        # 3. GEODETIC VECTOR EDGES (Pure Spatial Distance Layouts)
        """
        CREATE TABLE routes (
            route_id SERIAL PRIMARY KEY,
            source_airport VARCHAR(10) REFERENCES airports(airport_code) ON DELETE RESTRICT,
            target_airport VARCHAR(10) REFERENCES airports(airport_code) ON DELETE RESTRICT,
            distance_km NUMERIC(10, 2) NOT NULL,
            CONSTRAINT unique_spatial_vector UNIQUE(source_airport, target_airport)
        );
        """,
        
        # 4. TEMPORAL SCHEDULING MATRIX (The Live Operational Nexus)
        """
        CREATE TABLE flight_instances (
            flight_id SERIAL PRIMARY KEY,
            route_id INT REFERENCES routes(route_id) ON DELETE RESTRICT,
            aircraft_id INT REFERENCES aircraft_fleet(aircraft_id) ON DELETE RESTRICT,
            departure_timestamp TIMESTAMPTZ NOT NULL,
            arrival_timestamp TIMESTAMPTZ NOT NULL,
            current_seat_liquidity INT NOT NULL,
            CONSTRAINT check_timeline CHECK (arrival_timestamp > departure_timestamp)
        );
        """,
        
        # 5. SYNTHETIC PASSENGER METRICS
        """
        CREATE TABLE users (
            user_id VARCHAR(255) PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            profile_tier VARCHAR(50) DEFAULT 'STANDARD' CHECK (profile_tier IN ('STANDARD', 'INSTITUTIONAL_WHOSALE', 'QUANT_STRESS_BOT')),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # 6. THE REALIZED-REVENUE MASTER LEDGER
        """
        CREATE TABLE bookings (
            booking_id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE CASCADE,
            booking_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            simulated_fuel_price_multiplier NUMERIC(4,2) DEFAULT 1.00
        );
        """,
        
        # 7. ASSET YIELD TRANSACTION LEDGER
        """
        CREATE TABLE tickets (
            ticket_id SERIAL PRIMARY KEY,
            booking_id INT REFERENCES bookings(booking_id) ON DELETE CASCADE,
            flight_id INT REFERENCES flight_instances(flight_id) ON DELETE CASCADE,
            seat_number VARCHAR(10) NOT NULL,
            fare_paid_inr NUMERIC(12, 2) NOT NULL,
            class_tier VARCHAR(20) DEFAULT 'Economy' CHECK (class_tier IN ('Economy', 'Premium Economy', 'Business', 'First Class')),
            CONSTRAINT unique_flight_seat UNIQUE (flight_id, seat_number)
        );
        """,
        
        # 8. PERFORMANCE TUNING INDEXES (Critical for Real-Time Pathfinders)
        "CREATE INDEX idx_graph_departure ON flight_instances(departure_timestamp ASC);",
        "CREATE INDEX idx_flight_route_search ON flight_instances(route_id, current_seat_liquidity);"
    ]
    
    try:
        with engine.begin() as transaction:
            for index, query in enumerate(schema_queries, start=1):
                transaction.execute(text(query))
                print(f"🔹 Deployed Core Relational Infrastructure Table Layer ({index}/16)")
                    
        print("\n✅ SYSTEM SUCCESS: Quant Operations Engine Schema safely compiled and running on Neon DB.")
    except Exception as e:
        print(f"\n❌ DEPLOYMENT CRASHED: Database transactions aborted and rolled back to preserve safety state. Error:\n{str(e)}")

if __name__ == "__main__":
    build_relational_schema()