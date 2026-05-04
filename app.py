from flask import Flask, render_template, request, jsonify

import folium
from folium import plugins
import pandas as pd
import sqlalchemy
import heapq
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Database Configuration
DB_URI = os.getenv("DATABASE_URL", "postgresql://postgres:admin123@localhost:5432/india_aviation")
if DB_URI.startswith("postgres://"):
    DB_URI = DB_URI.replace("postgres://", "postgresql://", 1)

engine = sqlalchemy.create_engine(DB_URI)

def get_airports_from_db():
    # Fetching airport metadata for the map markers
    query = "SELECT ident, name, latitude_deg, longitude_deg, type FROM airports WHERE type != 'small_airport';"
    return pd.read_sql(query, engine).to_dict(orient='records')

def get_detailed_itinerary(start_node, end_node, start_time_str="16:00"):
    """
    Temporal Dijkstra adapted from your IPYNB logic.
    Handles multi-day connections and buffer times.
    """
    base_date = datetime(2026, 5, 4) 
    try:
        start_time = datetime.combine(base_date, datetime.strptime(start_time_str, "%H:%M").time())
    except:
        start_time = datetime(2026, 5, 4, 16, 0)

    # Load flight schedule
    try:
        query = "SELECT source_id, target_id, departure_time, arrival_time, cost_inr, distance_km FROM flights"
        all_flights = pd.read_sql(query, engine)
    except Exception as e:
        print(f"Database Error: {e}")
        return None

    # Priority Queue: (current_time, cost, current_node, itinerary_list, total_dist)
    queue = [(start_time, 0, start_node, [], 0)]
    earliest_arrival = {} 

    while queue:
        curr_time, cost, u, itinerary, dist = heapq.heappop(queue)

        if u == end_node:
            return cost, curr_time, itinerary, dist

        if u in earliest_arrival and earliest_arrival[u] <= curr_time:
            continue
        earliest_arrival[u] = curr_time

        # Prevent infinite searching (3-day cap)
        if (curr_time - start_time).days > 3:
            continue

        available_flights = all_flights[all_flights['source_id'] == u]

        for _, f in available_flights.iterrows():
            buffer_time = timedelta(minutes=45)
            
            # Convert time objects from DB to full datetimes on the current 'simulation' day
            f_dep = datetime.combine(curr_time.date(), f['departure_time'])
            f_arr = datetime.combine(curr_time.date(), f['arrival_time'])
            
            # Handle overnight flights
            if f_arr < f_dep: 
                f_arr += timedelta(days=1)

            # Determine if we need to wait for the next day's flight
            if f_dep < curr_time + buffer_time:
                f_dep += timedelta(days=1)
                f_arr += timedelta(days=1)
            
            layover_duration = (f_dep - curr_time)
            
            # Create the segment for the frontend
            new_leg = {
                'from': u,
                'to': f['target_id'],
                'dep': f_dep.strftime('%b %d, %I:%M %p'),
                'arr': f_arr.strftime('%b %d, %I:%M %p'),
                'fare': float(f['cost_inr']),
                'layover': str(layover_duration) if itinerary else "0:00:00"
            }

            heapq.heappush(queue, (
                f_arr, 
                cost + f['cost_inr'], 
                f['target_id'], 
                itinerary + [new_leg], 
                dist + f['distance_km']
            ))

    return None

def create_base_map(path_coords=None, path_nodes=None):
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB positron")
    airports = get_airports_from_db()
    
    path_nodes = path_nodes or []
    has_active_path = len(path_nodes) > 0

    for ap in airports:
        is_in_path = ap['ident'] in path_nodes
        
        if has_active_path and not is_in_path:
            color, radius, opacity = '#bdc3c7', 3, 0.4
        elif is_in_path:
            color = '#27ae60' if ap['ident'] == path_nodes[0] else '#e74c3c'
            radius, opacity = 7, 1.0
        else:
            color, radius, opacity = '#2980b9', 5, 0.7

        popup_html = f"""
            <div style="font-family: sans-serif; text-align: center;">
                <strong>{ap['name']}</strong><br>
                <button onclick="window.top.postMessage({{action: 'setPoint', id: '{ap['ident']}', type: 'source'}}, '*')">Start</button>
                <button onclick="window.top.postMessage({{action: 'setPoint', id: '{ap['ident']}', type: 'dest'}}, '*')">End</button>
            </div>
        """
        
        folium.CircleMarker(
            location=[ap['latitude_deg'], ap['longitude_deg']], 
            radius=radius, color=color, fill=True, fill_opacity=opacity,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=ap['ident']
        ).add_to(m)

    if path_coords:
        plugins.AntPath(path_coords, color='#2c3e50', weight=4).add_to(m)
        
    return m._repr_html_()

@app.route('/')
def index():
    return render_template('index.html', map_html=create_base_map())

@app.route('/reset')
def reset():
    return jsonify({"map_html": create_base_map()})

@app.route('/query', methods=['POST'], strict_slashes=False)
def run_query():
    data = request.json
    source = data.get('source')
    dest = data.get('dest')
    user_start_time = data.get('start_time',"16:00")
    
    result = get_detailed_itinerary(source, dest, start_time_str=user_start_time)
    
    if not result:
        return jsonify({"error": "No viable flight path found."}), 200

    total_cost, final_time, legs, total_km = result

    # Prepare coordinates for the map path
    airports_list = get_airports_from_db()
    route_nodes = [source] + [leg['to'] for leg in legs]
    path_coords = []
    for node in route_nodes:
        node_data = next((ap for ap in airports_list if ap['ident'] == node), None)
        if node_data:
            path_coords.append([node_data['latitude_deg'], node_data['longitude_deg']])

    return jsonify({
        "message": "Itinerary Found!",
        "map_html": create_base_map(path_coords=path_coords, path_nodes=route_nodes),
        "fare": round(total_cost, 2),
        "distance": round(total_km, 2),
        "route_str": " ➔ ".join(route_nodes),
        "itinerary": legs  # This matches your index.html expectations
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)