import os
import random
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import your newly rewritten, math-aligned pathfinder pricing logic
from pathfinder import compute_edge_weights

# Strict Production Boundary: Pull target cloud environment string dynamically.
# Hardcoded fallbacks stripped to prevent credential leaks on public VCS commits.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise EnvironmentError(
        "❌ CRITICAL CONFIGURATION FAULT: The 'DATABASE_URL' environment variable is unassigned. "
        "Stress simulator initialization aborted to safeguard credentials."
    )

# Simulation parameters: 40 simultaneous users attempting to book seats on the same flight block
TARGET_FLIGHT_ID = 309  
TOTAL_STRESS_BOTS = 40

# Master list of synthetic user IDs matching the verified clean seed matrix
SIMULATION_USERS = [
    "usr_einstein_001", 
    "usr_curie_002", 
    "usr_tesla_003", 
    "usr_turing_004"
]

# --- 2. THE ATOMIC TRANSACTION WORKER ---
def execute_atomic_booking(worker_id, user_id, flight_id):
    """
    Executes an isolated transaction block using SELECT FOR UPDATE 
    to guarantee data safety during high-concurrency seat reservation bursts.
    """
    connection = None
    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # --- PHASE A: ACQUIRE ROW-LEVEL LOCK ---
        # FOR UPDATE forces incoming threads to block cleanly until previous locks commit or abort.
        # Pulls complete data required by compute_edge_weights matrix to compute real pricing.
        lock_query = """
            SELECT 
                f.flight_id, f.route_id, f.aircraft_id, f.departure_timestamp, f.arrival_timestamp, f.current_seat_liquidity,
                r.source_airport, r.target_airport, r.distance_km,
                a.total_seat_capacity, a.fuel_burn_liters_per_km, a.hourly_crew_cost_inr, a.hourly_maint_cost_inr,
                port_src.landing_fee_inr, port_tgt.turnaround_fee_inr, port_tgt.base_ground_turnaround_minutes
            FROM flight_instances f
            JOIN routes r ON f.route_id = r.route_id
            JOIN aircraft_fleet a ON f.aircraft_id = a.aircraft_id
            JOIN airports port_src ON r.source_airport = port_src.airport_code
            JOIN airports port_tgt ON r.target_airport = port_tgt.airport_code
            WHERE f.flight_id = %s 
            FOR UPDATE;
        """
        cursor.execute(lock_query, (flight_id,))
        flight_row = cursor.fetchone()
        
        if not flight_row:
            return {"worker_id": worker_id, "status": "FAILED", "reason": "Flight instance not found"}
            
        current_seats = flight_row['current_seat_liquidity']
        total_capacity = flight_row['total_seat_capacity']
        
        # --- PHASE B: SEAT LIQUIDITY VALIDATION ---
        # Handled by database check constraints, but caught here early to skip redundant execution
        if current_seats <= 0:
            return {"worker_id": worker_id, "status": "DENIED", "reason": "Flight completely full! Seat liquidity = 0"}
            
        # --- PHASE C: ECONOMETRIC PRICING EVALUATION ---
        # Dynamically invokes Section 2.2 formula from cost_calculation.md using exact live inventory counts
        edge_metrics = compute_edge_weights(flight_row, fuel_multiplier=1.00)
        calculated_fare = edge_metrics["cheapest_w"]
        
        # --- PHASE D: WRITE LEDGERS ---
        # 1. Create a parent booking record
        insert_booking = """
            INSERT INTO bookings (user_id, simulated_fuel_price_multiplier)
            VALUES (%s, 1.00) RETURNING booking_id;
        """
        cursor.execute(insert_booking, (user_id,))
        booking_id = cursor.fetchone()['booking_id']
        
        # 2. Calculate seat layout layout index (e.g., "Seat 14A")
        allocated_seat_no = total_capacity - current_seats + 1
        seat_string = f"{allocated_seat_no}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
        
        # 3. Insert the physical ticket mapping to the exact calculated fare pricing ceiling
        insert_ticket = """
            INSERT INTO tickets (booking_id, flight_id, seat_number, fare_paid_inr, class_tier)
            VALUES (%s, %s, %s, %s, 'Economy');
        """
        cursor.execute(insert_ticket, (booking_id, flight_id, seat_string, calculated_fare))
        
        # 4. Atomically decrement seat pool inventory (Raises check_seat_leakage constraint exception if less than 0)
        update_flight = """
            UPDATE flight_instances 
            SET current_seat_liquidity = current_seat_liquidity - 1 
            WHERE flight_id = %s;
        """
        cursor.execute(update_flight, (flight_id,))
        
        # --- PHASE E: COMMIT TRANSACTION ---
        connection.commit()
        return {"worker_id": worker_id, "status": "SUCCESS", "seat": seat_string, "booking_id": booking_id, "fare": calculated_fare}
        
    except Exception as e:
        if connection:
            connection.rollback()
        return {"worker_id": worker_id, "status": "ERROR", "reason": str(e)}
    finally:
        if connection:
            cursor.close()
            connection.close()

# --- 3. CONCURRENCY ORCHESTRATOR ---
def run_booking_stress_test():
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
    
    # --- 4. PROCESSING EXPERIMENTAL SIMULATION METRICS ---
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
            
if __name__ == "__main__":
    run_booking_stress_test()