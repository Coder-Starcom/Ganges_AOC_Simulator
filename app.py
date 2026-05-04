from flask import Flask, render_template, request, jsonify
import folium
import pandas as pd
import sqlalchemy
import heapq
import os

app = Flask(__name__)

# Fetch the database URL from the server environment, or use localhost as a fallback for local testing
DB_URI = os.getenv("DATABASE_URL", "postgresql://postgres:admin123@localhost:5432/india_aviation")

# SQLAlchemy requires 'postgresql://' but some cloud providers give 'postgres://'
if DB_URI.startswith("postgres://"):
    DB_URI = DB_URI.replace("postgres://", "postgresql://", 1)

# -------------------------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------------------------
engine = sqlalchemy.create_engine(DB_URI)

def get_airports_from_db():
    """Fetches mainline airport nodes (excluding small_airports)."""
    query = """
        SELECT ident, name, latitude_deg, longitude_deg, iso_region, type 
        FROM airports
        WHERE type != 'small_airport';
    """
    df = pd.read_sql(query, engine)
    return df.to_dict(orient='records')

def get_economic_dijkstra_path(start_node, end_node):
    """The Core Pathfinding Algorithm."""
    query = "SELECT source_id, target_id, cost_inr, distance_km FROM edges_economic"
    try:
        edges_df = pd.read_sql(query, engine)
    except Exception as e:
        return float("inf"), 0, []

    graph = {}
    for _, row in edges_df.iterrows():
        u, v, w = row['source_id'], row['target_id'], row['cost_inr']
        dist = row['distance_km']
        
        if u not in graph: graph[u] = []
        if v not in graph: graph[v] = []
        
        graph[u].append((v, w, dist))
        graph[v].append((u, w, dist)) 

    queue = [(0, 0, start_node, [])]
    seen = set()
    min_costs = {start_node: 0}

    while queue:
        (cost, total_dist, v1, path) = heapq.heappop(queue)
        
        if v1 not in seen:
            seen.add(v1)
            path = path + [v1]
            
            if v1 == end_node:
                return cost, total_dist, path

            for v2, weight, edge_dist in graph.get(v1, []):
                if v2 in seen: continue
                
                prev_cost = min_costs.get(v2, None)
                next_cost = cost + weight
                
                if prev_cost is None or next_cost < prev_cost:
                    min_costs[v2] = next_cost
                    heapq.heappush(queue, (next_cost, total_dist + edge_dist, v2, path))

    return float("inf"), 0, []

def create_base_map(path_coords=None, path_nodes=None):
    """Generates Map. Automatically grays out and shrinks non-path nodes if a path exists."""
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB positron")
    airports = get_airports_from_db()
    
    if path_nodes is None:
        path_nodes = []
    
    has_active_path = len(path_nodes) > 0

    for ap in airports:
        is_in_path = ap['ident'] in path_nodes
        
        # --- UI Dynamic Marker Logic ---
        if has_active_path and not is_in_path:
            # Grayed out & further shrunken when a route is active
            marker_color = '#bdc3c7' # Gray
            marker_radius = 3
            marker_opacity = 0.4
        elif is_in_path:
            # Highlighted route nodes
            marker_color = '#e74c3c' # Red
            marker_radius = 8
            marker_opacity = 1.0
        else:
            # Default state (smaller than standard markers)
            marker_color = '#2980b9' # Blue
            marker_radius = 5
            marker_opacity = 0.8

        html = f"""
            <div style="font-family: Arial; text-align: center;">
                <h4 style="margin: 5px 0; color: #2c3e50;">{ap['name']} ({ap['ident']})</h4>
                <p style="margin: 2px 0; font-size: 12px; color: #7f8c8d;">Region: {ap['iso_region']}</p>
                <button style="margin: 3px; padding: 5px 10px; cursor: pointer; background: #27ae60; color: white; border: none; border-radius: 3px;" 
                        onclick="window.top.postMessage({{action: 'setPoint', id: '{ap['ident']}', type: 'source'}}, '*')">Set Source</button>
                <button style="margin: 3px; padding: 5px 10px; cursor: pointer; background: #2980b9; color: white; border: none; border-radius: 3px;" 
                        onclick="window.top.postMessage({{action: 'setPoint', id: '{ap['ident']}', type: 'dest'}}, '*')">Set Dest</button>
            </div>
        """
        iframe = folium.IFrame(html, width=220, height=120)
        popup = folium.Popup(iframe)
        
        # Using CircleMarker for size & color control
        folium.CircleMarker(
            location=[ap['latitude_deg'], ap['longitude_deg']], 
            radius=marker_radius,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=marker_opacity,
            popup=popup, 
            tooltip=f"{ap['name']} ({ap['ident']})"
        ).add_to(m)

    # Draw the path
    if path_coords:
        folium.PolyLine(
            path_coords, weight=4, color='#e74c3c', opacity=0.8, dash_array='10'
        ).add_to(m)
        
    return m._repr_html_()

@app.route('/')
def index():
    try:
        return render_template('index.html', map_html=create_base_map())
    except Exception as e:
        return f"Database Error: {str(e)}"

@app.route('/reset', methods=['GET'])
def reset_map():
    # Returns a fresh, unstyled map
    return jsonify({"map_html": create_base_map()})

@app.route('/query', methods=['POST'])
def run_query():
    data = request.json
    source_id = data.get('source')
    dest_id = data.get('dest')
    
    if not source_id or not dest_id:
        return jsonify({"error": "Select both source and destination!"}), 400
    if source_id == dest_id:
        return jsonify({"error": "Source and destination cannot be the same."}), 400

    # 1. Run Dijkstra Algorithm
    fare, dist, route_nodes = get_economic_dijkstra_path(source_id, dest_id)
    
    if not route_nodes:
        return jsonify({"error": "No valid economic path found between these nodes."}), 404

    # 2. Extract coordinates for the returned path nodes
    airports = get_airports_from_db()
    path_coords = []
    for node_id in route_nodes:
        node_data = next((ap for ap in airports if ap['ident'] == node_id), None)
        if node_data:
            path_coords.append([node_data['latitude_deg'], node_data['longitude_deg']])

    # 3. Generate updated map
    new_map_html = create_base_map(path_coords=path_coords, path_nodes=route_nodes)
    
    return jsonify({
        "message": "Path Computed!",
        "map_html": new_map_html,
        "fare": round(fare, 2),
        "distance": round(dist, 2),
        "route_str": " ➔ ".join(route_nodes)
    })

if __name__ == '__main__':
    app.run(debug=True)