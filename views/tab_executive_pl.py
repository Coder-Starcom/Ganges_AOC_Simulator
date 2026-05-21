# views/tab_executive_pl.py
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from psycopg2.extras import RealDictCursor

def render(neon_db_uri, gross_revenue, total_bookings, fuel_shock):
    st.markdown("### 📈 Real-Time Network Yield Intelligence & Operational Ledger Matrix")
    st.markdown("""
        <div class="tooltip-box">
        <strong>💡 Live Data Executive Cockpit:</strong> All metrics and visualizations displayed below are calculated in real time directly from active transactional ledgers and flight capacity states inside your Neon PostgreSQL instance.
        </div>
    """, unsafe_allow_html=True)

    # --- 1. RUN LIVE BUSINESS INTELLIGENCE AGGREGATIONS ---
    try:
        conn = psycopg2.connect(neon_db_uri)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Plot A: True Seating Class Dynamic Contribution
        cursor.execute("""
            SELECT class_tier, SUM(fare_paid_inr) as total_yield
            FROM tickets
            GROUP BY class_tier;
        """)
        class_data = cursor.fetchall()
        
        # Plot B: Top Profit Corridors (Origin -> Destination)
        cursor.execute("""
            SELECT r.source_airport, r.target_airport, SUM(t.fare_paid_inr) as corridor_revenue
            FROM tickets t
            JOIN flight_instances f ON t.flight_id = f.flight_id
            JOIN routes r ON f.route_id = r.route_id
            GROUP BY r.source_airport, r.target_airport
            ORDER BY corridor_revenue DESC
            LIMIT 5;
        """)
        corridor_data = cursor.fetchall()
        
        # Plot C: Real Seat Liquidity Scatter (Remaining Seats vs Capacity)
        cursor.execute("""
            SELECT f.flight_id, f.current_seat_liquidity, a.total_seat_capacity,
                   (a.total_seat_capacity - f.current_seat_liquidity) as booked_seats
            FROM flight_instances f
            JOIN aircraft_fleet a ON f.aircraft_id = a.aircraft_id;
        """)
        seat_liquidity_data = cursor.fetchall()
        
        # Plot D: Active Fleet Allocation Share
        cursor.execute("""
            SELECT a.model_name, COUNT(f.flight_id) as assigned_flights
            FROM flight_instances f
            JOIN aircraft_fleet a ON f.aircraft_id = a.aircraft_id
            GROUP BY a.model_name;
        """)
        fleet_allocation = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"❌ Failed to run live financial data aggregates: {e}")
        return

    # --- 2. DATA FRAME CONVERSIONS & PROTECTION FALLBACKS ---
    df_class = pd.DataFrame(class_data) if class_data else pd.DataFrame(columns=['class_tier', 'total_yield'])
    df_corridor = pd.DataFrame(corridor_data) if corridor_data else pd.DataFrame(columns=['source_airport', 'target_airport', 'corridor_revenue'])
    df_seats = pd.DataFrame(seat_liquidity_data) if seat_liquidity_data else pd.DataFrame(columns=['flight_id', 'current_seat_liquidity', 'total_seat_capacity', 'booked_seats'])
    df_fleet = pd.DataFrame(fleet_allocation) if fleet_allocation else pd.DataFrame(columns=['model_name', 'assigned_flights'])

    # Build unique labels for corridors safely
    if not df_corridor.empty:
        df_corridor['Corridor'] = df_corridor['source_airport'].astype(str) + " ➔ " + df_corridor['target_airport'].astype(str)

    # --- 3. EXECUTE METRICS RIBBON ---
    # Apply cost calculation metrics directly to live values
    simulated_fixed_doc = total_bookings * 4500.0
    simulated_variable_fuel = total_bookings * 2800.0 * fuel_shock
    total_operating_costs = simulated_fixed_doc + simulated_variable_fuel
    net_margin = float(gross_revenue) - total_operating_costs
    margin_pct = (net_margin / float(gross_revenue) * 100) if gross_revenue > 0 else 0.0

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Live Ledger Gross Revenue", f"₹{float(gross_revenue):,.2f}")
    m_col2.metric("Calculated DOC Burn", f"₹{total_operating_costs:,.2f}", delta=f"{fuel_shock:.2f}x Fuel Price Level", delta_color="inverse")
    m_col3.metric("Net Operational Margin", f"{margin_pct:.2f}%")

    st.markdown("---")

    # --- 4. THE 4-PLOT PRODUCTION GRID ---
    row1_c1, row1_c2 = st.columns(2)
    row2_c1, row2_c2 = st.columns(2)

    # Plot 1: Seating Tier Yield Weight
    with row1_c1:
        st.markdown("#### 🎯 1. Seating Class Yield Contribution Matrix")
        st.caption("True income division extracted across ticket tier types.")
        if not df_class.empty:
            fig1 = px.bar(df_class, x="class_tier", y="total_yield",
                          labels={"class_tier": "Fare Tier Class", "total_yield": "Aggregated Revenue (₹)"},
                          color="total_yield", color_continuous_scale="Blues")
            fig1.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No ticket records available in database.")

    # Plot 2: Top 5 Financial Corridors
    with row1_c2:
        st.markdown("#### 🗺️ 2. Top Profit-Generating Network Corridors")
        st.caption("Top 5 city-pairs ordered by gross seat reservation revenue.")
        if not df_corridor.empty:
            fig2 = px.bar(df_corridor, x="corridor_revenue", y="Corridor", orientation="h",
                          labels={"corridor_revenue": "Total Collected Revenue (₹)", "Corridor": "Route"},
                          color="corridor_revenue", color_continuous_scale="Purples")
            fig2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No route transaction history identified.")

    # Plot 3: Seat Inventory Depletion Scatter
    with row2_c1:
        st.markdown("#### ✈️ 3. Asset Inventory Depletion Scatter")
        st.caption("Live tracking of booked passengers versus total physical aircraft capacity bounds.")
        if not df_seats.empty:
            fig3 = px.scatter(df_seats, x="total_seat_capacity", y="booked_seats", size="current_seat_liquidity",
                              hover_data=["flight_id"], labels={"total_seat_capacity": "Total Seat Capacity", "booked_seats": "Booked Passengers Assigned"},
                              color="booked_seats", color_continuous_scale="Viridis")
            fig3.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No capacity rows returned from flight matrix tables.")

    # Plot 4: Aircraft Flight Allocations
    with row2_c2:
        st.markdown("#### 🍩 4. Aircraft Asset Utilization Share")
        st.caption("Breakdown of total scheduled flights assigned across aircraft fleet models.")
        if not df_fleet.empty:
            fig4 = px.pie(df_fleet, values="assigned_flights", names="model_name",
                          color_discrete_sequence=px.colors.sequential.Plotly3, hole=0.4)
            fig4.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=280)
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No asset scheduling footprints discovered.")