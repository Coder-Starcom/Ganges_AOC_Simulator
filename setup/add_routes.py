import os
import math
import random
import psycopg2
import psycopg2.extras
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

# --- 1. CONFIGURATION AND CLOUD URI PARSING ---
NEON_DB_URI = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:admin123@ep-ganges-aviation-pool.east-us-2.aws.neon.tech/gi_aviation_db?sslmode=require"
)

# --- 2. ADVANCED GEODETIC GEOMETRY CALCULATION ---
def calculate_haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * (2 * math.asin(math.sqrt(a)))

# --- 3. EXECUTION PIPELINE CONTROLLER ---
def run_pipeline():
    print("🛫 Initializing Re-Engineered Quantitative Simulator Data Pipeline...")
    
    try:
        df_nodes = pd.read_csv("../data/global_graph_nodes_clean.csv")
    except FileNotFoundError:
        print("❌ CRITICAL ERROR: 'global_graph_nodes_clean.csv' missing on disk.")
        return

    # Add default institutional constraint fees and switches directly to dataframe
    if 'landing_fee_inr' not in df_nodes.columns:
        df_nodes['landing_fee_inr'] = 45000.00
    if 'turnaround_fee_inr' not in df_nodes.columns:
        df_nodes['turnaround_fee_inr'] = 65000.00
    if 'base_ground_turnaround_minutes' not in df_nodes.columns:
        df_nodes['base_ground_turnaround_minutes'] = 45
    if 'is_operational' not in df_nodes.columns:
        df_nodes['is_operational'] = True

    valid_airport_cols = [
        'airport_code', 'name', 'city', 'country', 'latitude', 'longitude', 
        'landing_fee_inr', 'turnaround_fee_inr', 'base_ground_turnaround_minutes', 'is_operational'
    ]
    
    df_nodes = df_nodes[valid_airport_cols].copy()
    airports_list = df_nodes.to_dict(orient='records')
    print(f"📌 Parsed {len(airports_list)} structural airport nodes from disk.")

    # Generate Edges via Geodetic Combinations
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
                # Add bi-directional spatial edges
                routes_rows.append([ap1['airport_code'], ap2['airport_code'], round(dist, 2)])
                routes_rows.append([ap2['airport_code'], ap1['airport_code'], round(dist, 2)])

    df_routes = pd.DataFrame(routes_rows, columns=['source_airport', 'target_airport', 'distance_km'])
    print(f"📊 Synthesized {len(df_routes):,} unique geodetic spatial routes.")

    # Stage raw static files out for low-overhead streaming ingestion
    df_nodes.to_csv("../data/staged_airports.csv", index=False, header=False)
    df_routes.to_csv("../data/staged_routes.csv", index=False, header=False)

    print("\n🔌 Establishing transaction pool connection mapping to NeonDB...")
    try:
        connection = psycopg2.connect(NEON_DB_URI)
        cursor = connection.cursor()
        
        print("🧹 Executing atomic network purge via TRUNCATE CASCADE...")
        cursor.execute("TRUNCATE TABLE flight_instances, tickets, bookings, users, routes, aircraft_fleet, airports CASCADE;")
        
        # --- STREAM STEP 1: AIRPORTS ---
        print("📥 Streaming 'airports' structural nodes to NeonDB via COPY protocol...")
        with open("../data/staged_airports.csv", "r", encoding="utf-8") as f:
            sql = f"COPY airports ({','.join(valid_airport_cols)}) FROM STDIN WITH CSV DELIMITER ','"
            cursor.copy_expert(sql, f)
            
        # --- STREAM STEP 2: FLEET SEEDING ---
        print("✈️ Seeding Heterogeneous Corporate Aircraft Asset Inventory Layer...")
        fleet_profiles = [
            ('VT-GIA', 'Airbus A320neo', 180, 2.80, 18000.00, 22000.00),
            ('VT-GIB', 'Airbus A350-900', 320, 5.40, 45000.00, 55000.00),
            ('VT-GIC', 'Boeing 787-9 Dreamliner', 290, 4.90, 41000.00, 48000.00),
            ('VT-GID', 'Boeing 747-400 Legacy', 410, 11.20, 65000.00, 95000.00) # Added fuel-guzzler for stress simulation testing
        ]
        for f_prof in fleet_profiles:
            cursor.execute("""
                INSERT INTO aircraft_fleet (registration_no, model_name, total_seat_capacity, fuel_burn_liters_per_km, hourly_crew_cost_inr, hourly_maint_cost_inr)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, f_prof)
            
        # --- STREAM STEP 3: ROUTES ---
        print("🛰️ Streaming 'routes' edge coordinates to NeonDB via COPY protocol...")
        with open("../data/staged_routes.csv", "r", encoding="utf-8") as f:
            sql = "COPY routes (source_airport, target_airport, distance_km) FROM STDIN WITH CSV DELIMITER ','"
            cursor.copy_expert(sql, f)

        # --- STREAM STEP 4: GENERATING live TIME-DEPENDENT SCHEDULING MATRIX ---
        print("⏳ Constructing Stochastic Temporal Scheduling Matrix instances (7-Day Horizon)...")
        cursor.execute("SELECT route_id, distance_km FROM routes;")
        database_routes = cursor.fetchall()
        
        cursor.execute("SELECT aircraft_id, total_seat_capacity FROM aircraft_fleet;")
        database_fleet = cursor.fetchall()

        base_time = datetime.now(timezone.utc) + timedelta(days=1)
        flight_instances_records = []
        
        # Build systematic flight schedules for our operational network paths
        for r_id, dist_km in database_routes:
            dist_float = float(dist_km)
            
            # Isolate wide-body assets vs narrow-body assets explicitly from database fields
            # database_fleet structure: (aircraft_id, total_seat_capacity)
            wide_bodies = [f for f in database_fleet if f[1] >= 290]  # A350, 787, 747
            narrow_bodies = [f for f in database_fleet if f[1] < 290] # A320neo
            
            if dist_float > 4500.0:
                # Route requires a long-haul asset. Randomly deploy an A350, 787, or legacy 747
                assigned_plane = random.choice(wide_bodies)
            else:
                # Short regional route gets the fuel-efficient regional narrow-body
                assigned_plane = random.choice(narrow_bodies)

            # Calculate cruise time duration (assume 800 km/h baseline cruise velocity)
            calculated_duration_hours = dist_float / 800.0
            calculated_duration_minutes = max(int(calculated_duration_hours * 60), 45)

            # Calculate cruise time duration (assume 800 km/h baseline cruise velocity)
            calculated_duration_hours = float(dist_km) / 800.0
            calculated_duration_minutes = max(int(calculated_duration_hours * 60), 45)

            # Generate 3 sequential flight occurrences across a rolling timeline horizon
            for sequence in range(3):
                departure = base_time + timedelta(days=sequence, hours=random.randint(0, 20))
                arrival = departure + timedelta(minutes=calculated_duration_minutes)
                
                flight_instances_records.append((
                    r_id,
                    assigned_plane[0],
                    departure,
                    arrival,
                    assigned_plane[1] # Set initial capacity liquidity pool to max plane capacity
                ))

        print(f"📥 Batch inserting {len(flight_instances_records):,} live temporal schedule paths to database tables...")
        psycopg2.extras.execute_values(
            cursor,
            "INSERT INTO flight_instances (route_id, aircraft_id, departure_timestamp, arrival_timestamp, current_seat_liquidity) VALUES %s",
            flight_instances_records
        )

        connection.commit()
        print(f"\n✅ RECONCILIATION SUCCESSFUL: Network infrastructure live and fully populated.")
        
    except Exception as error:
        print(f"❌ MATRIX PIPELINE FAULTED: {error}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
        print("Pool connection safely closed.")

if __name__ == "__main__":
    run_pipeline()