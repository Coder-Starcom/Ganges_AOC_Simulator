import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone

# Strict Production Boundary: Pull target cloud environment string dynamically.
# Hardcoded fallbacks stripped to prevent credential leaks on public VCS commits.
NEON_DB_URI = os.getenv("DATABASE_URL")

if not NEON_DB_URI:
    raise EnvironmentError(
        "❌ CRITICAL CONFIGURATION FAULT: The 'DATABASE_URL' environment variable is unassigned. "
        "Topology Engine initialization aborted to safeguard credentials."
    )


# --- 2. THE MATHEMATICAL UNION-FIND DATA STRUCTURE ---
class DisjointSetUnion:
    def __init__(self, nodes):
        """
        Initializes the disjoint set tree partitions. 
        Each node begins as its own unique structural subset parent.
        """
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in nodes}

    def find(self, node):
        """
        Resolves the absolute root representative of the given node partition.
        Implements recursive path compression to flatten tree depth to O(1).
        """
        if self.parent[node] != node:
            # Recursive Path Compression assignment
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, node1, node2):
        """
        Merges two distinct node components using rank-optimization balance.
        Returns True if a new structural edge merge occurred, False if already unified.
        """
        root1 = self.find(node1)
        root2 = self.find(node2)
        
        if root1 != root2:
            # Union by Rank Optimization to attach the shallower tree underneath the deeper tree
            if self.rank[root1] > self.rank[root2]:
                self.parent[root2] = root1
            elif self.rank[root1] < self.rank[root2]:
                self.parent[root1] = root2
            else:
                self.parent[root1] = root2
                self.rank[root2] += 1
            return True
        return False


# --- 3. THE LIVE TOPOLOGY ANALYZER ENGINE ---
def analyze_network_topology():
    print("\n🧠 Querying active route edges for network topology validation...")
    
    conn = psycopg2.connect(NEON_DB_URI)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Pull all distinct airport terminal nodes active in the system
    cursor.execute("SELECT airport_code FROM airports;")
    airport_rows = cursor.fetchall()
    active_airports = [row['airport_code'] for row in airport_rows]
    
    # 2. Pull all live operational routes representing the network graph arcs
    query = """
        SELECT r.source_airport, r.target_airport, f.flight_id
        FROM flight_instances f
        JOIN routes r ON f.route_id = r.route_id
        WHERE f.current_seat_liquidity > 0;
    """
    cursor.execute(query)
    active_flight_edges = cursor.fetchall()
    
    cursor.close()
    conn.close()

    if not active_airports:
        print("⚠️ No active network airport nodes found inside the target registry.")
        return

    # 3. Instantiate the rank-optimized DSU core structure
    dsu = DisjointSetUnion(active_airports)
    active_connections_count = 0

    # 4. Process structural row edges down the wire into the DSU context
    for edge in active_flight_edges:
        src = edge['source_airport']
        tgt = edge['target_airport']
        
        # Verify edge endpoints are valid tracked terminal nodes before processing
        if src in dsu.parent and tgt in dsu.parent:
            merged = dsu.union(src, tgt)
            if merged:
                active_connections_count += 1

    # 5. Resolve exact isolated component sets (Islands)
    unique_clusters = {}
    for airport in active_airports:
        root_rep = dsu.find(airport)
        if root_rep not in unique_clusters:
            unique_clusters[root_rep] = []
        unique_clusters[root_rep].append(airport)

    total_isolated_islands = len(unique_clusters)

    # --- 6. QUANTITATIVE CAPCITY/BOTTLENECK MATRIX CALCULATIONS ---
    print("📊 Computing structural centrality matrix indices over node degree vectors...")
    
    hub_edge_counts = {}
    total_network_traffic_weight = 0

    for edge in active_flight_edges:
        src, tgt = edge['source_airport'], edge['target_airport']
        hub_edge_counts[src] = hub_edge_counts.get(src, 0) + 1
        hub_edge_counts[tgt] = hub_edge_counts.get(tgt, 0) + 1
        total_network_traffic_weight += 2

    # Calculate structural Hub Centrality percentage values
    hub_centrality_matrix = {}
    for airport in active_airports:
        count = hub_edge_counts.get(airport, 0)
        share = (count / total_network_traffic_weight * 100) if total_network_traffic_weight > 0 else 0.0
        hub_centrality_matrix[airport] = round(share, 2)

    # Extract primary systemic bottleneck node profile
    sorted_hubs = sorted(hub_centrality_matrix.items(), key=lambda item: item[1], reverse=True)
    primary_bottleneck_node = sorted_hubs[0][0] if sorted_hubs else "None"
    primary_bottleneck_score = sorted_hubs[0][1] if sorted_hubs else 0.0

    # --- 7. TERMINAL RISK PERFORMANCE DISPLAY REPORT ---
    print("\n" + "="*80)
    print("🟢 TOPOLOGY RISK ANALYTICS: DSU CRITICAL INTEGRITY RADAR")
    print("="*80)
    
    if total_isolated_islands == 1:
        print(f" 📈 CONNECTIVITY STATUS: ✅ FULLY UNIFIED NETWORK | 0 Isolated Islands Detected")
    else:
        print(f" 🚨 CONNECTIVITY STATUS: ❌ FRAGMENTED SYSTEM NETWORK DETECTED")
        print(f" ℹ️ Structural Alert: The operational map has broken into {total_isolated_islands} isolated system clusters.")

    print(f" 🛠️ System Components Evaluated: {len(active_airports)} Nodes | {len(active_flight_edges)} Traversed Flight Arcs")
    print(f" 🛑 Primary Systemic Bottleneck Hub: {primary_bottleneck_node} ({primary_bottleneck_score}% global share)")
    print("-"*80)
    print("📋 DETAILED TOPOLOGY SECTOR BREAKDOWN MAP:")
    
    for idx, (root, members) in enumerate(unique_clusters.items(), start=1):
        print(f"   📍 Cluster Hub Component #{idx} (Root Node Representative: {root}):")
        print(f"      ✈️ Terminal Nodes: {', '.join(members)}")
        
    print("\n" + "="*80)
    print("📊 HUB STRUCTURAL CORE LOAD CAPACITY SHARE DISTRIBUTION MATRIX:")
    print("="*80)
    for hub, score in sorted_hubs:
        bar_visual = "█" * int(score // 2)
        print(f"   Hub Terminal {hub:3s} | Load Share: {score:6.2f}% | {bar_visual}")
    print("="*80)


if __name__ == "__main__":
    # Test topology risk metrics directly over active PostgreSQL records
    analyze_network_topology()