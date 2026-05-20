import os
import sys
import time
import random
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed

# Maintain relative module paths for importing your core engines
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pathfinder import NEON_DB_URI
from stress_test_bookings import execute_atomic_booking, SIMULATION_USERS

def fetch_valid_flights():
    """Quick helper to poll available flight inventory."""
    try:
        conn = psycopg2.connect(NEON_DB_URI)
        cursor = conn.cursor()
        # Focuses the parallel transaction threads on the next 200 closest departures
        query = """
            SELECT flight_id 
            FROM flight_instances 
            WHERE current_seat_liquidity > 0 
            AND departure_timestamp >= '2026-05-20 17:15:00'
            ORDER BY departure_timestamp ASC 
            LIMIT 200;
        """
        cursor.execute(query)
        flights = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return flights
    except Exception as e:
        print(f"❌ Database inventory fetch failed: {e}")
        return []

def fire_single_transaction(worker_id, flight_pool):
    """Worker task executed inside the parallel thread pool."""
    if not flight_pool:
        return "EMPTY_POOL"
    target_flight_id = random.choice(flight_pool)
    random_passenger = random.choice(SIMULATION_USERS)
    
    try:
        result = execute_atomic_booking(worker_id=worker_id, user_id=random_passenger, flight_id=target_flight_id)
        return result.get('status', 'ERROR')
    except Exception:
        return 'EXCEPTION'

def run_overclocked_simulator():
    print("=" * 60)
    print("🚀 GANGES INTERNATIONAL | OVERCLOCKED CONCURRENCY CANNON")
    print("🔥 PHASE 1: PARALLEL HYPER-BLAST MODE (Simultaneous Thread Pool)")
    print("🛑 Press CTRL+C at any time to abort.")
    print("=" * 60)
    
    # ---------------------------------------------------------
    # STEP 1: PARALLEL HYPER-BLAST MODE (Fires hundreds of rows instantly)
    # ---------------------------------------------------------
    TOTAL_BLAST_BOOKINGS = 2500   # Total tickets to write in the burst
    CONCURRENT_THREADS = 150      # How many parallel actions to run at the exact same millisecond
    
    blast_successful = 0
    batch_run = 1
    
    while blast_successful < TOTAL_BLAST_BOOKINGS:
        flights = fetch_valid_flights()
        if not flights:
            print("💤 No seat liquidity available. Pausing blast.")
            break
            
        remaining_needed = TOTAL_BLAST_BOOKINGS - blast_successful
        current_batch_size = min(CONCURRENT_THREADS, remaining_needed)
        
        print(f"\n⚡ Deploying Transaction Batch #{batch_run} ({current_batch_size} Parallel Threads)...")
        
        # Fire a multi-threaded batch down the wire concurrently
        with ThreadPoolExecutor(max_workers=current_batch_size) as executor:
            futures = [
                executor.submit(fire_single_transaction, worker_id=i, flight_pool=flights)
                for i in range(current_batch_size)
            ]
            
            for future in as_completed(futures):
                status = future.result()
                if status == "SUCCESS":
                    blast_successful += 1
        
        print(f"📈 Real-time Burst Progress: {blast_successful}/{TOTAL_BLAST_BOOKINGS} tickets written to database ledger.")
        batch_run += 1
        time.sleep(0.1) # Small cooling gap between batches to prevent DB pool choking

    # ---------------------------------------------------------
    # STEP 2: STEADY-STATE CRUISE MODE (Throttles down to be polite)
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("🐢 PHASE 2: CRUISE MODE ENGAGED (Stabilizing Network Baseline)")
    print("=" * 60)
    
    cruise_counter = blast_successful
    while True:
        try:
            flights = fetch_valid_flights()
            if flights:
                status = fire_single_transaction(worker_id=888, flight_pool=flights)
                if status == "SUCCESS":
                    cruise_counter += 1
                    print(f"[🐢 CRUISE] Ticket #{cruise_counter} written. Sleeping for 4.0s...")
            time.sleep(4.0)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down demand simulator gracefully.")
            break
        except Exception:
            time.sleep(4.0)

if __name__ == "__main__":
    run_overclocked_simulator()