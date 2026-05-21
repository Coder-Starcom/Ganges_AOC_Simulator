import os
import math
import random
import psycopg2
import psycopg2.extras
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURATION AND CLOUD URI PARSING ---
# Strict Production Boundary: Pull target cloud environment string dynamically.
# Hardcoded fallbacks stripped to prevent credential leaks on public VCS commits.
NEON_DB_URI = os.getenv("DATABASE_URL")

if not NEON_DB_URI:
    raise EnvironmentError(
        "❌ CRITICAL CONFIGURATION FAULT: The 'DATABASE_URL' environment variable is unassigned. "
        "Data pipeline pipeline initialization aborted to safeguard credentials."
    )


# --- 2. ADVANCED GEODETIC GEOMETRY CALCULATION ---
def calculate_haversine(lat1, lon1, lat2, lon2):
    """
    Computes the geodetic great-circle distance between two coordinate pairs
    on the surface of a sphere via the Haversine formula.
    """
    R = 6371.0  # Earth's mean radius in kilometers
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * (2 * math.asin(math.sqrt(a)))


# --- 3. EXECUTION PIPELINE CONTROLLER ---
def run_pipeline():
    print("🛫 Initializing Re-Engineered Quantitative Simulator Data Pipeline...")
    
    # Standardizing paths assuming execution from inside a scripts/ directory
    source_nodes_path = "../data/global_graph_nodes_clean.csv"
    staged_airports_path = "../data/staged_airports.csv"
    staged_routes_path = "../data/staged_routes.csv"

    try:
        df_nodes = pd.read_csv(source_nodes_path)
    except FileNotFoundError:
        print(f"❌ CRITICAL ERROR: Source topology node mapping file missing at '{source_nodes_path}'.")
        return

    # Add default operational constants to dataframe if not predefined
    defaults = {
        'landing_fee_inr': 45000.00,
        'turnaround_fee_inr': 65000.00,
        'base_ground_turnaround_minutes': 45,
        'is_operational': True
    }
    for column, value in defaults.items():
        if column not in df_nodes.columns:
            df_nodes[column] = value

    valid_airport_cols = [
        'airport_code', 'name', 'city', 'country', 'latitude', 'longitude', 
        'landing_fee_inr', 'turnaround_fee_inr', 'base_ground_turnaround_minutes', 'is_operational'
    ]
    
    df_nodes = df_nodes[valid_airport_cols].copy()
    airports_list = df_nodes.to_dict(orient='records')
    print(f"📌 Parsed {len(airports_list)} structural airport nodes from disk.")

    # Generate Directed Edges via Geodetic Combinations
    print("🧠 Extracting geodetic topology lines...")
    routes_rows = []
    np.random.seed(42)
    drop_rate = 0.85
    
    for i in range(len(airports_list)):
        ap1 = airports_list[i]
        for j in range(i + 1, len(airports_list)):
            ap2 = airports_list[j]
            
            if np.random.rand() > drop_rate:
                dist = calculate_haversine(ap1['latitude'], ap1['longitude'], ap2['latitude'], ap2['longitude'])
                if dist < 50.0:
                    continue
                # Add bi-directional spatial edges to represent complete market corridors
                routes_rows.append([ap1['airport_code'], ap2['airport_code'], round(dist, 2)])
                routes_rows.append([ap2['airport_code'], ap1['airport_code'], round(dist, 2)])

    df_routes = pd.DataFrame(routes_rows, columns=['source_airport', 'target_airport', 'distance_km'])
    print(f"📊 Synthesized {len(df_routes):,} unique geodetic spatial routes.")

    # Stage raw static files out for low-overhead streaming ingestion via PostgreSQL COPY
    df_nodes.to_csv(staged_airports_path, index=False, header=False)
    df_routes.to_csv(staged_routes_path, index=False, header=False)

    print("\n🔌 Establishing connection pooling matrix directly to NeonDB cluster...")
    try:
        connection = psycopg2.connect(NEON_DB_URI)
        cursor = connection.cursor()
        
        print("🧹 Executing atomic network purging via TRUNCATE CASCADE...")
        cursor.execute("TRUNCATE TABLE flight_instances, tickets, bookings, users, routes, aircraft_fleet, airports CASCADE;")
        
        # --- STREAM STEP 1: AIRPORTS ---
        print("📥 Streaming 'airports' structural nodes to NeonDB via COPY protocol...")
        with open(staged_airports_path, "r", encoding="utf-8") as f:
            sql = f"COPY airports ({','.join(valid_airport_cols)}) FROM STDIN WITH CSV DELIMITER ','"
            cursor.copy_expert(sql, f)
            
        # --- STREAM STEP 2: FLEET SEEDING ---
        print("✈️ Seeding Heterogeneous Corporate Aircraft Asset Inventory Layer...")
        fleet_profiles = [
            ('VT-GIA', 'Airbus A320neo', 180, 2.80, 18000.00, 22000.00),
            ('VT-GIB', 'Airbus A350-900', 320, 5.40, 45000.00, 55000.00),
            ('VT-GIC', 'Boeing 787-9 Dreamliner', 290, 4.90, 41000.00, 48000.00),
            ('VT-GID', 'Boeing 747-400 Legacy', 410, 11.20, 65000.00, 95000.00)
        ]
        for f_prof in fleet_profiles:
            cursor.execute("""
                INSERT INTO aircraft_fleet (registration_no, model_name, total_seat_capacity, fuel_burn_liters_per_km, hourly_crew_cost_inr, hourly_maint_cost_inr)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, f_prof)
            
        # --- STREAM STEP 3: ROUTES ---
        print("🛰️ Streaming 'routes' edge coordinates to NeonDB via COPY protocol...")
        with open(staged_routes_path, "r", encoding="utf-8") as f:
            sql = "COPY routes (source_airport, target_airport, distance_km) FROM STDIN WITH CSV DELIMITER ','"
            cursor.copy_expert(sql, f)

        # --- STREAM STEP 4: GENERATING LIVE TIME-DEPENDENT SCHEDULING MATRIX ---
        print("⏳ Constructing Stochastic Temporal Scheduling Matrix instances (7-Day Horizon)...")
        cursor.execute("SELECT route_id, distance_km FROM routes;")
        database_routes = cursor.fetchall()
        
        cursor.execute("SELECT aircraft_id, total_seat_capacity FROM aircraft_fleet;")
        database_fleet = cursor.fetchall()

        # Operational calendar setup
        base_time = datetime.now(timezone.utc) + timedelta(days=1)
        flight_instances_records = []
        
        # Deconstruct and categorize fleet assets by capacity bands
        wide_bodies = [f for f in database_fleet if f[1] >= 290]
        narrow_bodies = [f for f in database_fleet if f[1] < 290]
        
        # Defensive Fallbacks: If database fleet queries ever return empty, use general fleet array
        if not wide_bodies: wide_bodies = database_fleet
        if not narrow_bodies: narrow_bodies = database_fleet

        # Build systematic flight schedules across mapped routes
        for r_id, dist_km in database_routes:
            dist_float = float(dist_km)
            
            # Select appropriate equipment based on geodetic distance threshold
            if dist_float > 4500.0:
                assigned_plane = random.choice(wide_bodies)
            else:
                assigned_plane = random.choice(narrow_bodies)

            # Calculate expected block time duration (assumes ~800 km/h baseline network cruise velocity)
            calculated_duration_hours = dist_float / 800.0
            calculated_duration_minutes = max(int(calculated_duration_hours * 60), 45)

            # Generate rolling temporal occurrences across a multi-day timeline horizon
            for sequence in range(3):
                departure = base_time + timedelta(days=sequence, hours=random.randint(0, 20))
                arrival = departure + timedelta(minutes=calculated_duration_minutes)
                
                flight_instances_records.append((
                    r_id,
                    assigned_plane[0],  # aircraft_id
                    departure,
                    arrival,
                    assigned_plane[1]   # Initial seat liquidity sets to airframe capacity ceiling
                ))

        print(f"📥 Batch inserting {len(flight_instances_records):,} live temporal schedule paths to database tables...")
        psycopg2.extras.execute_values(
            cursor,
            "INSERT INTO flight_instances (route_id, aircraft_id, departure_timestamp, arrival_timestamp, current_seat_liquidity) VALUES %s",
            flight_instances_records
        )

        connection.commit()
        print(f"\n✅ RECONCILIATION SUCCESSFUL: Network core infrastructure populated safely.")
        
    except Exception as error:
        print(f"❌ MATRIX PIPELINE FAULTED: Operation rolled back. Details:\n{error}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
        print("Pool connection safely released.")


if __name__ == "__main__":
    run_pipeline()