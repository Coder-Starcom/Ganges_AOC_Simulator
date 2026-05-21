# views/tab_tactical_radar.py
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

def render(neon_db_uri, total_bookings, airport_df):
    st.markdown("### 📡 Chronological Dispatch & Advanced Capacity Optimization Horizon")
    st.markdown("""
        <div class="tooltip-box">
        <strong>📡 AOC Controller Mission Control Guide:</strong> Flights are chronologically prioritized by imminent departure time. 
        The ledger calculates structural unit capacity metrics (ASK/RPK) live. Use this screen to spot 
        <strong>🔴 High Leakage</strong> flights early enough to trigger systemic re-routing before gate closure.
        </div>
    """, unsafe_allow_html=True)
    
    # Define current operational simulation epoch timestamp (Locked to May 2026 reference window)
    AOC_SIM_NOW = datetime(2026, 5, 20, 17, 15, 0, tzinfo=timezone.utc)
    
    try:
        conn = psycopg2.connect(neon_db_uri)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Chronological sort: Grabs the next 15 flights departing after our current simulation time
        query = """
            SELECT f.flight_id, r.source_airport, r.target_airport, f.departure_timestamp, 
                   f.arrival_timestamp, f.current_seat_liquidity, a.total_seat_capacity, 
                   a.model_name, r.distance_km
            FROM flight_instances f
            JOIN routes r ON f.route_id = r.route_id
            JOIN aircraft_fleet a ON f.aircraft_id = a.aircraft_id
            WHERE f.departure_timestamp >= %s
            ORDER BY f.departure_timestamp ASC 
            LIMIT 15;
        """
        cursor.execute(query, (AOC_SIM_NOW,))
        radar_flights = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Database Read Disruption: {e}")
        radar_flights = []

    if radar_flights:
        rf_df = pd.DataFrame(radar_flights)
        
        # --- ADVANCED CAPACITY & OPERATIONS METRICS MATH ---
        rf_df['booked_seats'] = (rf_df['total_seat_capacity'] - rf_df['current_seat_liquidity']).clip(lower=0)
        rf_df['load_factor_%'] = ((rf_df['booked_seats'] / rf_df['total_seat_capacity']) * 100).round(1)
        
        # ASK (Available Seat Kilometers) = Total Seats * Distance
        rf_df['ASK'] = rf_df['total_seat_capacity'] * rf_df['distance_km']
        # RPK (Revenue Passenger Kilometers) = Booked Seats * Distance
        rf_df['RPK'] = rf_df['booked_seats'] * rf_df['distance_km']
        
        # Calculate time remaining until departure gate lock
        def calculate_countdown(dep_time):
            if dep_time.tzinfo is None:
                dep_time = dep_time.replace(tzinfo=timezone.utc)
            delta = dep_time - AOC_SIM_NOW
            total_mins = int(delta.total_seconds() / 60)
            if total_mins < 0:
                return "✈️ Airborne"
            elif total_mins < 60:
                return f"⏳ {total_mins}m (Boarding)"
            else:
                return f"⏱️ {total_mins // 60}h {total_mins % 60}m"
                
        rf_df['Time_To_Departure'] = rf_df['departure_timestamp'].apply(calculate_countdown)

        # Dynamic Status Routing Rules
        def assign_tactical_status(row):
            if row['Time_To_Departure'] == "✈️ Airborne":
                return "🟢 Sector Active"
            if row['load_factor_%'] < 35.0:
                return "🔴 High Leakage (Consolidate)"
            if row['load_factor_%'] < 75.0:
                return "🟡 Dynamic Fare Promotion"
            return "🟢 Max Yield Allocated"
            
        rf_df['Tactical_Action'] = rf_df.apply(assign_tactical_status, axis=1)

        # Network System Totals
        total_network_ask = rf_df['ASK'].sum()
        total_network_rpk = rf_df['RPK'].sum()
        system_load_factor = (total_network_rpk / total_network_ask * 100) if total_network_ask > 0 else 0.0
        imminent_leakage_nodes = sum(1 for status in rf_df['Tactical_Action'] if "🔴" in status)

        # Top-Level Flight Operational Metric Ribbons
        c_col1, c_col2, c_col3, c_col4 = st.columns(4)
        c_col1.metric("Live System Activity Pool", f"{total_bookings:,} Global Bookings")
        c_col2.metric(
            "Imminent Leakage Alarms", 
            f"{imminent_leakage_nodes} Nodes", 
            delta="Action Required" if imminent_leakage_nodes > 0 else "Nominal", 
            delta_color="inverse"
        )
        c_col3.metric("Systemic Load Factor (RPK/ASK)", f"{system_load_factor:.1f}%")
        c_col4.metric("Total Asset Production Capacity", f"{total_network_ask:,.0f} ASK")

        st.markdown("---")
        
        # Split layout: Main prioritized table on left, visual metrics on right
        radar_left, radar_right = st.columns([2, 1])
        
        with radar_left:
            st.markdown("#### 📋 Chronological Operations Dispatch Board")
            st.caption("Prioritized by imminent departure sequence. Re-runs live data rows directly against inventory mutations.")
            
            # Format display dataframe for clean visual presentation
            display_df = rf_df[[
                'flight_id', 'Time_To_Departure', 'source_airport', 'target_airport', 
                'model_name', 'load_factor_%', 'booked_seats', 'total_seat_capacity', 'Tactical_Action'
            ]].copy()
            
            display_df.columns = [
                'Flight ID', 'Countdown to Dep', 'Origin', 'Destination', 
                'Aircraft Asset', 'Load Factor', 'Booked Pax', 'Capacity Ceiling', 'Tactical Resolution Strategy'
            ]
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)

        with radar_right:
            st.markdown("#### 📊 Sector Revenue Potential (RPK vs ASK)")
            st.caption("Visual gap analysis between total production volume and actual ticket monetization per flight asset.")
            
            # Generate inline structural gap chart
            fig_gap = px.bar(
                rf_df, 
                x="flight_id", 
                y=["ASK", "RPK"],
                labels={"flight_id": "Flight ID Matrix Node", "value": "Passenger Kilometers"},
                barmode="overlay",
                color_discrete_sequence=["rgba(59, 130, 246, 0.2)", "#2563EB"]
            )
            fig_gap.update_layout(
                template="plotly_dark", 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10), 
                height=260,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_gap, use_container_width=True)
            
            st.markdown("""
                <div style="background-color: #111827; padding: 12px; border-radius: 8px; border: 1px solid #1F2937; font-size: 0.85rem;">
                    <strong>💡 Operations Blueprint Note:</strong> Overlaid bars display asset production volume. 
                    The translucent blue background is the maximum potential volume (ASK). The solid blue core is the revenue-generating volume (RPK). 
                    Your optimization goal is to eliminate the empty gaps before the countdown hits <code>✈️ Airborne</code>.
                </div>
            """, unsafe_allow_html=True)
            
    else:
        st.warning("💤 No flights matching active scheduling criteria were resolved inside the current temporal dispatch horizon window.")