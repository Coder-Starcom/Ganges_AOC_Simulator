import os
import sys
import math
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, timedelta

# Strict Production Boundary: Pull target cloud environment string dynamically.
# Hardcoded fallbacks stripped to prevent credential leaks on public VCS commits.
NEON_DB_URI = os.getenv("DATABASE_URL")

if not NEON_DB_URI:
    raise EnvironmentError(
        "❌ CRITICAL CONFIGURATION FAULT: The 'DATABASE_URL' environment variable is unassigned. "
        "Pathfinder initialization aborted to safeguard credentials."
    )


# --- 2. THE QUANTITATIVE COST ENGINE ---
def compute_edge_weights(flight, fuel_multiplier=1.00):
    """
    Implements the official mathematical reference formulas for a flight edge:
    1. DOC (Direct Operating Cost Floor) - cost_calculation.md Section 1.1
    2. P(t) (Dynamic Stochastic Ticket Price Ceiling) - cost_calculation.md Section 2.2
    """
    # Extract structural database inputs mapped exactly from the verified schema
    dist = float(flight['distance_km'])
    burn_rate = float(flight['fuel_burn_liters_per_km'])       # \kappa_a asset coefficient
    hourly_crew = float(flight['hourly_crew_cost_inr'])         # C_crew baseline
    hourly_maint = float(flight['hourly_maint_cost_inr'])       # M_maint baseline
    landing_fee = float(flight['landing_fee_inr'])               # L_origin node matrix
    turnaround_fee = float(flight['turnaround_fee_inr'])         # T_dest node matrix
    capacity = flight['total_seat_capacity']                     # Cap_a airframe layout
    liquidity = flight['current_seat_liquidity']                 # Current database seats available
    
    dep_time = flight['departure_timestamp']
    arr_time = flight['arrival_timestamp']
    
    # Calculate flight duration block hours (Dur_f)
    duration_hours = (arr_time - dep_time).total_seconds() / 3600.0
    
    # --- Equation 1.1: Direct Operating Cost Floor (DOC) ---
    # P_fuel baseline = 105.50 INR per Liter
    p_fuel_baseline = 105.50 
    fuel_cost = dist * burn_rate * (p_fuel_baseline * fuel_multiplier)
    time_cost = duration_hours * (hourly_crew + hourly_maint)
    
    doc_floor = fuel_cost + time_cost + landing_fee + turnaround_fee
    
    # --- Equation 2.1: Basal Break-Even Fare ---
    # Targets structural Load_Factor_target = 0.75 (75%)
    base_fare = doc_floor / (capacity * 0.75)
    
    # --- Equation 2.2: Non-Linear Asymmetric Pricing Ceiling P(t) ---
    # Alpha capacity elasticity coefficient (\lambda) = 0.45
    # Temporal Velocity scale (\gamma) = 0.15
    # Urgency Decay factor exponent (\delta) = 0.60
    lam = 0.45
    gamma = 0.15
    delta = 0.60
    
    # Inventory Utilization Matrix Ratio: I_t = (Cap_a - Seats_Available_f) / Cap_a
    seats_booked = capacity - liquidity
    inventory_utilization = seats_booked / capacity  
    
    # Temporal Horizon Window remaining (\tau), handled in fractional days
    time_to_departure_days = (dep_time - datetime.now(timezone.utc)).total_seconds() / 86400.0
    time_to_departure_days = max(time_to_departure_days, 0.01)  # Safeguard boundary limit to eliminate zero-division
    
    # Final retail dynamic price execution
    price_inr = base_fare * math.exp(lam * inventory_utilization) * (1 + (gamma / (time_to_departure_days ** delta)))
    
    return {
        "cheapest_w": round(price_inr, 2),                                # Section 3.1: w(e) = P(t)_f
        "fastest_w": (arr_time - dep_time).total_seconds() / 60.0,       # Section 3.2: Dur_f (converted to minutes)
        "shortest_w": dist                                                # Section 3.3: Geodetic distance edge
    }


# --- 3. THE TIME-DEPENDENT GRAPH PATHFINDER ---
def find_optimal_itineraries(origin, destination, search_start_time):
    print(f"\n🧠 Querying routing paths: {origin} ➔ {destination}...")
    
    conn = psycopg2.connect(NEON_DB_URI)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Fetch all flight instances alongside their structural asset and network node metrics
    query = """
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
        WHERE f.departure_timestamp >= %s AND f.current_seat_liquidity > 0;
    """
    cursor.execute(query, (search_start_time,))
    all_flights = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Calculate operational weights for every valid flight edge across the topology map
    for flight in all_flights:
        weights = compute_edge_weights(flight)
        flight.update(weights)

    valid_itineraries = []

    # Queue layout for time-dependent traversal: [ (current_node, current_time, path_edges_list) ]
    queue = [(origin, search_start_time, [])]
    max_hops = 3  # Constrain search depth to prevent cyclical loop graph explosions

    while queue:
        curr_node, curr_time, path = queue.pop(0)
        
        if curr_node == destination:
            valid_itineraries.append(path)
            continue
            
        if len(path) >= max_hops:
            continue
            
        # Discover outgoing flight connections matching strict chronological path constraints
        for flight in all_flights:
            if flight['source_airport'] == curr_node:
                
                if len(path) == 0:
                    # Direct first leg boundary validation check
                    is_valid_connection = flight['departure_timestamp'] >= curr_time
                else:
                    # Multi-leg connection minimum turnaround safety limit check (Section 3.2 connection boundary)
                    last_flight = path[-1]
                    min_layover = timedelta(minutes=last_flight['base_ground_turnaround_minutes'])
                    is_valid_connection = flight['departure_timestamp'] >= (last_flight['arrival_timestamp'] + min_layover)
                
                if is_valid_connection:
                    queue.append((flight['target_airport'], flight['arrival_timestamp'], path + [flight]))

    if not valid_itineraries:
        print(f"⚠️ No active operational routing paths found between {origin} and {destination}.")
        return

    # --- 4. MULTI-CRITERIA STRATEGY SORTING MATRICES ---
    print(f"📊 Extracted {len(valid_itineraries)} valid flight combinations. Sorting optimization strategies...")
    
    # Mapping exact weight equations from Section 3 of cost_calculation.md
    strategies = {
        "🟢 CHEAPEST STRATEGY": lambda path: sum(f['cheapest_w'] for f in path),
        "🔵 FASTEST STRATEGY": lambda path: (path[-1]['arrival_timestamp'] - path[0]['departure_timestamp']).total_seconds() / 60.0,
        "🟣 SHORTEST STRATEGY": lambda path: sum(f['shortest_w'] for f in path)
    }
    
    for label, sorting_func in strategies.items():
        sorted_paths = sorted(valid_itineraries, key=sorting_func)
        best_path = sorted_paths[0]
        
        print("\n" + "="*80)
        print(f"{label}")
        print("="*80)
        
        total_fare = sum(f['cheapest_w'] for f in best_path)
        total_dist = sum(f['shortest_w'] for f in best_path)
        elapsed_time = (best_path[-1]['arrival_timestamp'] - best_path[0]['departure_timestamp']).total_seconds() / 3600.0
        
        for idx, leg in enumerate(best_path, start=1):
            print(f"  ✈️ Leg {idx}: {leg['source_airport']} ➔ {leg['target_airport']} | Flight ID: {leg['flight_id']}")
            print(f"     Departs: {leg['departure_timestamp']} | Arrives: {leg['arrival_timestamp']}")
            print(f"     Asset: {leg['total_seat_capacity']} seats | Price: ₹{leg['cheapest_w']:,} | Distance: {leg['shortest_w']} km")
            
        print("-"*80)
        print(f"📈 STRATEGY SUMMARY METRICS:")
        print(f"   💵 Total Cost Engine Yield:  ₹{total_fare:,.2f}")
        print(f"   ⏱️ Elapsed Operational Time: {elapsed_time:.2f} Hours")
        print(f"   🗺️ Total Spatial Distance:    {total_dist:,.2f} km")
        print("="*80)


if __name__ == "__main__":
    # Test pathfinder over a live operational window
    test_search_time = datetime.now(timezone.utc)
    # Target validation sample search parameter configuration
    find_optimal_itineraries(origin="DEL", destination="BOM", search_start_time=test_search_time)