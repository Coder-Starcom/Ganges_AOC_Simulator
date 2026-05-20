import os
import random
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 1. CONFIGURATION AND CLOUD CONNECTION ---
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:admin123@ep-ganges-aviation-pool.east-us-2.aws.neon.tech/gi_aviation_db?sslmode=require"
)

# Simulation parameters: 40 simultaneous users attempting to book seats on the same flight block
TARGET_FLIGHT_ID = 309  # Flight 309 from your pathfinder run (YYC -> MSP)
TOTAL_STRESS_BOTS = 40

# Master list of synthetic user IDs created by your provisioning script
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
    to guarantee data safety during high concurrency.
    """
    connection = None
    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # --- PHASE A: ACQUIRE ROW-LEVEL LOCK ---
        # FOR UPDATE tells PostgreSQL to block any other thread trying to modify this specific flight row
        lock_query = """
            SELECT current_seat_liquidity, total_seat_capacity 
            FROM flight_instances f
            JOIN aircraft_fleet a ON f.aircraft_id = a.aircraft_id
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
        if current_seats <= 0:
            # Transaction safely rolled back automatically upon closing if no commit occurs
            return {"worker_id": worker_id, "status": "DENIED", "reason": "Flight completely full! Seat liquidity = 0"}
            
        # --- PHASE C: WRITE LEDGERS ---
        # 1. Create a parent booking record
        insert_booking = """
            INSERT INTO bookings (user_id, simulated_fuel_price_multiplier)
            VALUES (%s, 1.00) RETURNING booking_id;
        """
        cursor.execute(insert_booking, (user_id,))
        booking_id = cursor.fetchone()['booking_id']
        
        # 2. Calculate seat layout number assignment (e.g., "Seat 14A")
        allocated_seat_no = total_capacity - current_seats + 1
        seat_string = f"{allocated_seat_no}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
        
        # 3. Insert the physical ticket
        # Simulating a dynamic fare yield placeholder value for the stress test transaction
        simulated_fare = 5498.32 
        insert_ticket = """
            INSERT INTO tickets (booking_id, flight_id, seat_number, fare_paid_inr, class_tier)
            VALUES (%s, %s, %s, %s, 'Economy');
        """
        cursor.execute(insert_ticket, (booking_id, flight_id, seat_string, simulated_fare))
        
        # 4. Atomically decrement seat pool inventory
        update_flight = """
            UPDATE flight_instances 
            SET current_seat_liquidity = current_seat_liquidity - 1 
            WHERE flight_id = %s;
        """
        cursor.execute(update_flight, (flight_id,))
        
        # --- PHASE D: COMMIT TRANSACTION ---
        connection.commit()
        return {"worker_id": worker_id, "status": "SUCCESS", "seat": seat_string, "booking_id": booking_id}
        
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
    
    # Fire off ThreadPoolExecutor to force simultaneous thread execution blocks
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
    for res in sorted(results, key=lambda x: x['worker_id'])[:15]: # Show first 15 logs
        if res['status'] == "SUCCESS":
            print(f" 🟢 Bot {res['worker_id']:02d}: RESERVATION MADE successfully! Seat: {res['seat']} | Booking ID: {res['booking_id']}")
        elif res['status'] == "DENIED":
            print(f" 🟡 Bot {res['worker_id']:02d}: TRANSACTION DENIED ➔ {res['reason']}")
        else:
            print(f" 🔴 Bot {res['worker_id']:02d}: FAULT CRASHED ➔ {res['reason']}")
            
    print("\n💡 Tip: Run 'python .\\setup\\read_db.py' to observe seat reduction and new ledger lines!")

if __name__ == "__main__":
    run_booking_stress_test()