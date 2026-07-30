import os
import random
import time
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from concurrent.futures import ThreadPoolExecutor, as_completed

from pathfinder import compute_edge_weights

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise EnvironmentError(
        "❌ CRITICAL CONFIGURATION FAULT: The 'DATABASE_URL' environment variable is unassigned. "
        "Stress simulator initialization aborted to safeguard credentials."
    )

# Target active seed flight_id from live DB inspection
TARGET_FLIGHT_ID = 1  
TOTAL_STRESS_BOTS = 40

# Valid seed users present in database
SIMULATION_USERS = [
    "usr_einstein_001", 
    "usr_curie_002", 
    "usr_tesla_003", 
    "usr_turing_004"
]

# Initialize ThreadedConnectionPool to handle parallel connections cleanly
connection_pool = None

def init_connection_pool():
    global connection_pool
    if connection_pool is None:
        connection_pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=TOTAL_STRESS_BOTS + 5,
            dsn=DATABASE_URL,
            connect_timeout=5
        )

# --- THE ATOMIC TRANSACTION WORKER ---
def execute_atomic_booking(worker_id, user_id, flight_id):
    max_retries = 3
    
    for attempt in range(max_retries):
        connection = None
        try:
            connection = connection_pool.getconn()
            connection.autocommit = False
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SET statement_timeout = 5000;")
            cursor.execute("SET lock_timeout = 3000;")
            
            # --- FIXED PHASE A: ACQUIRE TARGETED ROW LOCK VIA JOIN ---
            # Explicitly lock flight_instances ('FOR UPDATE OF f')
            lock_query = """
                SELECT 
                    f.flight_id, 
                    f.route_id, 
                    f.aircraft_id, 
                    f.departure_timestamp, 
                    f.arrival_timestamp, 
                    f.current_seat_liquidity,
                    r.source_airport, 
                    r.target_airport, 
                    r.distance_km,
                    a.total_seat_capacity, 
                    a.fuel_burn_liters_per_km, 
                    a.hourly_crew_cost_inr, 
                    a.hourly_maint_cost_inr,
                    port_src.landing_fee_inr, 
                    port_tgt.turnaround_fee_inr, 
                    port_tgt.base_ground_turnaround_minutes
                FROM flight_instances f
                JOIN routes r ON f.route_id = r.route_id
                JOIN aircraft_fleet a ON f.aircraft_id = a.aircraft_id
                JOIN airports port_src ON r.source_airport = port_src.airport_code
                JOIN airports port_tgt ON r.target_airport = port_tgt.airport_code
                WHERE f.flight_id = %s 
                FOR UPDATE OF f;
            """
            cursor.execute(lock_query, (flight_id,))
            flight_row = cursor.fetchone()
            
            if not flight_row:
                connection.rollback()
                cursor.close()
                connection_pool.putconn(connection)
                return {"worker_id": worker_id, "status": "FAILED", "reason": f"Flight instance {flight_id} not found."}
                
            current_seats = flight_row['current_seat_liquidity']
            total_capacity = flight_row['total_seat_capacity']

            # --- PHASE B: SEAT LIQUIDITY VALIDATION ---
            if current_seats <= 0:
                connection.rollback()
                cursor.close()
                connection_pool.putconn(connection)
                return {"worker_id": worker_id, "status": "DENIED", "reason": "Flight completely full! Seat liquidity = 0"}
                
            # --- PHASE C: ECONOMETRIC PRICING EVALUATION ---
            edge_metrics = compute_edge_weights(flight_row, fuel_multiplier=1.00)
            calculated_fare = edge_metrics["cheapest_w"]
            
            # --- PHASE D: WRITE LEDGERS ---
            insert_booking = """
                INSERT INTO bookings (user_id, simulated_fuel_price_multiplier)
                VALUES (%s, 1.00) RETURNING booking_id;
            """
            cursor.execute(insert_booking, (user_id,))
            booking_id = cursor.fetchone()['booking_id']
            
            allocated_seat_no = total_capacity - current_seats + 1
            seat_string = f"{allocated_seat_no}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
            
            insert_ticket = """
                INSERT INTO tickets (booking_id, flight_id, seat_number, fare_paid_inr, class_tier)
                VALUES (%s, %s, %s, %s, 'Economy');
            """
            cursor.execute(insert_ticket, (booking_id, flight_id, seat_string, calculated_fare))
            
            update_flight = """
                UPDATE flight_instances 
                SET current_seat_liquidity = current_seat_liquidity - 1 
                WHERE flight_id = %s;
            """
            cursor.execute(update_flight, (flight_id,))
            
            # --- PHASE E: COMMIT TRANSACTION ---
            connection.commit()
            cursor.close()
            connection_pool.putconn(connection)
            return {"worker_id": worker_id, "status": "SUCCESS", "seat": seat_string, "booking_id": booking_id, "fare": calculated_fare}
            
        except Exception as e:
            if connection:
                try:
                    connection.rollback()
                    cursor.close()
                    connection_pool.putconn(connection)
                except Exception:
                    pass
            
            if attempt < max_retries - 1:
                time.sleep(0.05 * (2 ** attempt))
                continue
                
            return {"worker_id": worker_id, "status": "ERROR", "reason": str(e)}

# --- CONCURRENCY ORCHESTRATOR ---
def run_booking_stress_test():
    init_connection_pool()
    
    print("=========================================================================")
    print(f"🔥 STARTING HIGH-CONCURRENCY TRANSACTION STRAIN ENGINE ON FLIGHT ID {TARGET_FLIGHT_ID} 🔥")
    print("=========================================================================")
    print(f"Spawning {TOTAL_STRESS_BOTS} parallel booking requests simultaneously...")
    
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=TOTAL_STRESS_BOTS) as executor:
        futures = []
        for i in range(1, TOTAL_STRESS_BOTS + 1):
            assigned_user = random.choice(SIMULATION_USERS)
            futures.append(
                executor.submit(execute_atomic_booking, worker_id=i, user_id=assigned_user, flight_id=TARGET_FLIGHT_ID)
            )
            
        for future in as_completed(futures):
            results.append(future.result())
            
    end_time = time.time()
    
    success_count = sum(1 for r in results if r['status'] == "SUCCESS")
    denied_count = sum(1 for r in results if r['status'] == "DENIED")
    error_count = sum(1 for r in results if r['status'] == "ERROR")
    
    print("\n" + "="*80)
    print("📊 TRANSACTION MATRIX METRICS SUMMARY")
    print("="*80)
    print(f"✅ Successful Transactions Written : {success_count}")
    print(f"🛑 Safely Blocked (Overbookings)   : {denied_count}")
    print(f"❌ Database Transaction Errors    : {error_count}")
    print(f"⏱️ Total Execution Window Duration: {end_time - start_time:.3f} Seconds")
    print("="*80)
    
    print("\n📋 LIVE TRANSACTION LOG EXTRACT:")
    for res in sorted(results, key=lambda x: x['worker_id'])[:15]:
        if res['status'] == "SUCCESS":
            print(f" 🟢 Bot {res['worker_id']:02d}: RESERVATION MADE! Seat: {res['seat']} | Fare Paid: ₹{res['fare']:,} | Booking ID: {res['booking_id']}")
        elif res['status'] == "DENIED":
            print(f" 🟡 Bot {res['worker_id']:02d}: TRANSACTION DENIED ➔ {res['reason']}")
        else:
            print(f" 🔴 Bot {res['worker_id']:02d}: FAULT CRASHED ➔ {res['reason']}")

    if connection_pool:
        connection_pool.closeall()

if __name__ == "__main__":
    run_booking_stress_test()