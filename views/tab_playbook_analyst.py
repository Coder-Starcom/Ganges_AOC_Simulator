# views/tab_network_strategy.py
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone

def render(neon_db_uri, active_airports, airport_df, fuel_shock, compute_edge_weights):
    st.markdown("### 🎯 Multi-Objective Network Arc Strategy Sandbox")
    st.markdown("""
        <div class="tooltip-box">
        <strong>🎯 Operations Research (OR) Sandbox Guide:</strong> This suite processes multi-variable constraints across your network topology. 
        When you execute an analysis, it evaluates flight itineraries along three Pareto-efficient frontiers: 
        <strong>Financial Yield</strong>, <strong>Temporal Velocity</strong>, and <strong>Geodetic Spatial Overhead</strong>.
        </div>
    """, unsafe_allow_html=True)
    
    # --------------------------------------------------------------------------
    # CONTROLS & LIVE ROUTE NETWORK MAP INTERFACE
    # --------------------------------------------------------------------------
    p_col1, p_col2 = st.columns([1, 2])
    with p_col1:
        st.markdown("#### 🗺️ Network Corridor Terminals")
        idx_origin = active_airports.index("CAI") if "CAI" in active_airports else 0
        idx_dest = active_airports.index("AMM") if "AMM" in active_airports else (1 if len(active_airports) > 1 else 0)
        
        origin = st.selectbox("Market Base Node (Origin)", active_airports, index=idx_origin, key="strat_origin")
        destination = st.selectbox("Target Node (Destination)", active_airports, index=idx_dest, key="strat_dest")
        
        st.markdown("---")
        st.markdown("#### 🎛️ Optimization Bias Weighting")
        alpha_yield = st.slider("💰 Maximize Yield Margin Focus", 0.0, 1.0, 0.8, step=0.1)
        beta_time = st.slider("⏱️ Minimize Passenger Connection Slack", 0.0, 1.0, 0.4, step=0.1)
        
        execute_analysis = st.button("Resolve Optimal Flight Frontiers 🎯", type="primary", use_container_width=True)
    
    with p_col2:
        st.markdown("#### 📡 System Active Network Node Topology Map")
        if not airport_df.empty:
            fig_map = px.scatter_mapbox(
                airport_df, 
                lat="latitude", 
                lon="longitude", 
                hover_name="city", 
                text="airport_code",
                color_discrete_sequence=["#3B82F6"], 
                zoom=2, 
                height=275
            )
            fig_map.update_layout(
                mapbox_style="open-street-map", 
                margin={"r":0,"t":0,"l":0,"b":0}, 
                template="plotly_dark"
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("Airport location metadata unavailable.")

    # --------------------------------------------------------------------------
    # GRAPH TRAVERSAL & MULTI-OBJECTIVE COMPILATION
    # --------------------------------------------------------------------------
    if execute_analysis:
        if origin == destination:
            st.error("Constraint Violation: Network source hub terminal cannot match target destination node.")
        else:
            with st.spinner("Executing time-dependent Dijkstra-variant graph traversal..."):
                try:
                    conn = psycopg2.connect(neon_db_uri)
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    query = """
                        SELECT f.flight_id, f.departure_timestamp, f.arrival_timestamp, f.current_seat_liquidity,
                               r.source_airport, r.target_airport, r.distance_km,
                               a.total_seat_capacity, a.model_name, a.fuel_burn_liters_per_km, a.hourly_crew_cost_inr, a.hourly_maint_cost_inr,
                               port_src.landing_fee_inr, port_tgt.turnaround_fee_inr, port_tgt.base_ground_turnaround_minutes
                        FROM flight_instances f
                        JOIN routes r ON f.route_id = r.route_id
                        JOIN aircraft_fleet a ON f.aircraft_id = a.aircraft_id
                        JOIN airports port_src ON r.source_airport = port_src.airport_code
                        JOIN airports port_tgt ON r.target_airport = port_tgt.airport_code
                        WHERE f.current_seat_liquidity > 0;
                    """
                    cursor.execute(query)
                    all_flights = cursor.fetchall()
                    cursor.close()
                    conn.close()
                except Exception as e:
                    st.error(f"Database Graph Resolution Error: {e}")
                    all_flights = []

                # Inject weights based on active fuel scalar inputs
                for f in all_flights:
                    f.update(compute_edge_weights(f, fuel_multiplier=fuel_shock))

                # Breadth-First Time-Aware Multi-Leg Structural Graph Build
                valid_itineraries = []
                queue = [(origin, datetime(2026, 5, 20, 0, 0, tzinfo=timezone.utc), [])]
                
                while queue:
                    curr_node, curr_time, path = queue.pop(0)
                    if curr_node == destination and len(path) > 0:
                        valid_itineraries.append(path)
                        continue
                    if len(path) >= 3: 
                        continue
                        
                    for flight in all_flights:
                        if flight['source_airport'] == curr_node:
                            if len(path) == 0:
                                is_valid = True
                            else:
                                last_leg = path[-1]
                                min_dep = last_leg['arrival_timestamp'] + timedelta(minutes=int(last_leg['base_ground_turnaround_minutes']))
                                is_valid = flight['departure_timestamp'] >= min_dep
                                
                            if is_valid:
                                queue.append((flight['target_airport'], flight['arrival_timestamp'], path + [flight]))

                # --------------------------------------------------------------------------
                # RENDER ANALYTICS FRONT-END PLOTS
                # --------------------------------------------------------------------------
                if not valid_itineraries:
                    st.warning(f"⚠️ Zero network flight arcs match legal minimum connection criteria between {origin} and {destination}.")
                else:
                    st.success(f"📈 Solved multi-objective matrix routing for corridor {origin} ➔ {destination}.")
                    
                    # Compute profile metrics for analysis
                    plot_rows = []
                    for idx, path in enumerate(valid_itineraries):
                        tot_cost = sum(f.get('cheapest_w', 0.0) for f in path)
                        tot_dist = sum(f.get('shortest_w', 0.0) for f in path)
                        tot_time = (path[-1]['arrival_timestamp'] - path[0]['departure_timestamp']).total_seconds() / 3600.0
                        plot_rows.append({
                            "Itinerary ID": f"Option #{idx+1}",
                            "Financial Cost (INR)": tot_cost,
                            "Elapsed Duration (Hrs)": tot_time,
                            "Geodetic Distance (KM)": tot_dist,
                            "Stops": len(path) - 1
                        })
                    df_plot = pd.DataFrame(plot_rows)

                    # --- PLOT 1: THE PARETO OPTIMIZATION FRONTIER SCATTER ---
                    st.markdown("#### 📊 1. Multi-Objective Strategy Efficient Frontier")
                    st.caption("Plots cost vs. duration to highlight the trade-offs between competing optimization metrics.")
                    
                    fig_pareto = px.scatter(
                        df_plot, x="Elapsed Duration (Hrs)", y="Financial Cost (INR)", 
                        color="Stops", size="Geodetic Distance (KM)", text="Itinerary ID",
                        color_continuous_scale="Viridis", hover_data=["Geodetic Distance (KM)"]
                    )
                    fig_pareto.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=15,b=15,l=15,r=15), height=300)
                    st.plotly_chart(fig_pareto, use_container_width=True)

                    st.markdown("---")
                    st.markdown("#### 📋 2. Comparative Playbook Performance Breakdown")
                    
                    # Sort out the three profile strategies with key fail-safes
                    leisure_best = sorted(valid_itineraries, key=lambda p: sum(f.get('cheapest_w', 0.0) for f in p))[0]
                    business_best = sorted(valid_itineraries, key=lambda p: (p[-1]['arrival_timestamp'] - p[0]['departure_timestamp']).total_seconds())[0]
                    logistics_best = sorted(valid_itineraries, key=lambda p: sum(f.get('shortest_w', 0.0) for f in p))[0]
                    
                    # Main comparative layout columns
                    sc1, sc2, sc3 = st.columns(3)
                    
                    strategies = [
                        ("🟢 LEISURE PLAYBOOK", leisure_best, sc1, "Yield-Optimized", "#10B981"),
                        ("🔵 BUSINESS PLAYBOOK", business_best, sc2, "Velocity-Optimized", "#3B82F6"),
                        ("purple", logistics_best, sc3, "Distance-Optimized", "#8B5CF6")
                    ]
                    
                    for name, path, column, metric_label, border_color in strategies:
                        tot_cost = sum(f.get('cheapest_w', 0.0) for f in path)
                        tot_dist = sum(f.get('shortest_w', 0.0) for f in path)
                        tot_time = (path[-1]['arrival_timestamp'] - path[0]['departure_timestamp']).total_seconds() / 3600.0
                        
                        with column:
                            st.markdown(f"""
                                <div style="background-color: #111827; padding: 18px; border-radius: 10px; border-left: 5px solid {border_color}; border-top: 1px solid #1F2937; border-bottom: 1px solid #1F2937; border-right: 1px solid #1F2937;">
                                    <div style="font-weight: 800; font-size: 1.05rem; color: {border_color};">{name.upper()}</div>
                                    <div style="font-size: 0.8rem; color: #64748B; text-transform: uppercase; margin-bottom: 12px;">{metric_label} Target Profile</div>
                                    <span style="font-size:0.75rem; color:#94A3B8; font-weight:600; text-transform:uppercase;">Calculated Core Operating Cost</span>
                                    <div style="font-size:1.6rem; font-weight:700; color:#FFFFFF; margin-top:2px; margin-bottom:12px;">Ref: ₹{tot_cost:,.2f}</div>
                                    <table style="width:100%; font-size:0.85rem; color:#CBD5E1;">
                                        <tr><td style="padding:4px 0; color:#94A3B8;">⏱️ Total Duration:</td><td style="text-align:right; font-weight:600;">{tot_time:.2f} Hrs</td></tr>
                                        <tr><td style="padding:4px 0; color:#94A3B8;">🗺️ Route Envelope:</td><td style="text-align:right; font-weight:600;">{tot_dist:,.1f} km</td></tr>
                                        <tr><td style="padding:4px 0; color:#94A3B8;">✈️ Layover Stops:</td><td style="text-align:right; font-weight:600;">{len(path)-1} Stop(s)</td></tr>
                                    </table>
                                </div>
                            """, unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            # Render distinct itinerary sector timelines underneath each column card
                            st.markdown("##### ⏱️ Sector Connection Timeline")
                            for leg_idx, leg in enumerate(path, 1):
                                layover_str = ""
                                if leg_idx > 1:
                                    prev_leg = path[leg_idx-2]
                                    layover_mins = int((leg['departure_timestamp'] - prev_leg['arrival_timestamp']).total_seconds() / 60)
                                    layover_str = f"⏳ *Layover Buffer: {layover_mins} mins*\n\n"
                                
                                st.caption(f"{layover_str}**Leg {leg_idx}: {leg['source_airport']} ➔ {leg['target_airport']}**")
                                
                                asset_model = leg.get('model_name', 'Commercial Fleet Asset')
                                current_seats = leg.get('current_seat_liquidity', 'N/A')
                                flight_id_num = leg.get('flight_id', 'Unknown')
                                dep_time_str = str(leg['departure_timestamp'])[11:16] if 'departure_timestamp' in leg else '--:--'
                                arr_time_str = str(leg['arrival_timestamp'])[11:16] if 'arrival_timestamp' in leg else '--:--'
                                
                                st.markdown(f"""
                                    <div style="background-color: #0F172A; padding: 10px; border-radius: 6px; border: 1px solid #1E293B; font-size: 0.8rem; margin-bottom:10px;">
                                        <strong>Asset ID:</strong> {flight_id_num} | ✈️ {asset_model}<br>
                                        <strong>Departs:</strong> {dep_time_str} Z | <strong>Arrives:</strong> {arr_time_str} Z<br>
                                        <strong>Available Seats:</strong> {current_seats} open slots
                                    </div>
                                """, unsafe_allow_html=True)