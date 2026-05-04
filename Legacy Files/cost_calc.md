# ✈️ Mathematical Model: Aviation Route Costing (INR) 🧮

This model shifts the edge weight in our graph from pure **Physical Distance ($d$)** to **Total Economic Cost ($C$)**. The goal is to create a "Bent Path" effect where Dijkstra's algorithm might intentionally prefer a longer physical route through a major metropolitan hub because it is mathematically and computationally "cheaper."

---

## 1. 💸 The Core Cost Function

The total economic cost of traversing an edge between node $u$ (source airport) and node $v$ (target airport) is defined by the following non-linear equation:

$$C(u, v) = [B + (\text{dist}(u,v) \times K)] \times \phi_{hub} \times \phi_{reg} + \tau_{takeoff}$$

### 📊 Component Breakdown & Economic Rationale

| Variable | Symbol | Description | Mathematical & Economic Purpose |
| :--- | :---: | :--- | :--- |
| **Base Fare** | $B$ 🎟️ | Flat minimum cost (approx. ₹1,800). | Covers booking infrastructure, baseline crew salaries, and fixed airline administrative overhead. |
| **Variable Rate** | $K$ ⛽ | Cost per kilometer (approx. ₹4.5 - ₹5.5). | Represents Aviation Turbine Fuel (ATF) burn at cruising altitude and cruise-phase wear-and-tear. |
| **Hub Discount** | $\phi_{hub}$ 🏢 | Reduces cost for `large_airport` pairs. | **Economies of Scale:** Hub flights use high-capacity jets (A320/B737) dropping the per-seat cost compared to small turboprops (ATR-72). |
| **Regional Surge**| $\phi_{reg}$ ⛰️ | Increases cost for remote/difficult terrain. | **Risk & Monopoly Premium:** Accounts for treacherous weather, specialized pilot training, and low passenger density in regions like the North East. |
| **Takeoff Tax** | $\tau_{takeoff}$ 🛫| Fixed penalty per hop (approx. ₹2,500). | **The "Stopover Penalty":** Covers airport landing fees, ATC (Air Traffic Control) charges, gate leasing, and high fuel burn during ascent. |

---

## 2. 🧠 Non-Linear Logic & "Logical" Constraints

By implementing these variables, we break the standard *Triangle Inequality* ($Distance(A \to C) \le Distance(A \to B) + Distance(B \to C)$). In our economic graph, an indirect route can actually be cheaper!

### A. The "Takeoff Tax" (Penalty for Graph Complexity) 🛑
In a pure distance graph, two 500 km hops equal one 1,000 km hop. To make Dijkstra act like a real-world passenger or airline, we add a flat **₹2,500 tax** per edge traversed.
* **Logical Result:** The algorithm fiercely penalizes "stopovers." It prevents the shortest path from blindly hopping through 5 small regional airports just because they form a slightly straighter geometric line.

### B. The Hub-and-Spoke Discount (Volume Economics) 🏙️
Major hubs like **VIDP (Delhi)**, **VABB (Mumbai)**, or **VOHS (Hyderabad)** handle massive passenger volumes, driving down operational costs.
* **Rule:** If both $u$ and $v$ are classified as `large_airport`, apply a **20% discount** ($\phi_{hub} = 0.80$).
* **Logical Result:** Dijkstra will create "Gravity Wells." The pathfinding will bend out of its way to hit a major city because the 20% discount on a 1,500 km flight vastly outweighs the extra fuel cost of a slight detour.

### C. The Geographic Difficulty Surge (Risk/Remote Pricing) 🏔️
Flying into geographically isolated regions like the Andaman Islands (`IN-AN`), Ladakh (`IN-LA`), or Arunachal Pradesh (`IN-AR`) requires higher insurance and faces less airline competition.
* **Rule:** If the target region ($v$) is in a designated remote zone, apply a **30% surge** ($\phi_{reg} = 1.30$).
* **Logical Result:** Creates "High-Cost Geofences." The algorithm will skirt around these regions entirely unless the target node $v$ is the absolute final destination.

---

## 3. 💻 Implementation Logic (Python Pseudocode)

To implement this dynamically in your data preprocessing pipeline, the logic should handle edge generation as follows:

```python
def calculate_economic_edge_weight(distance_km, s_type, t_type, t_region):
    # 0. Edge Case: Reject absurdly short physical hops (e.g., same city airports)
    if distance_km < 50:
        return float('inf') # Prevent algorithms from routing DEL -> Safdarjung

    # 1. Start with the Base Fare and Distance-rate
    base_fare = 1800.0
    per_km_rate = 5.2
    raw_cost = base_fare + (distance_km * per_km_rate)

    # 2. Apply Hub Multiplier (The "Large City" Logic)
    multiplier = 1.0
    if s_type == 'large_airport' and t_type == 'large_airport':
        multiplier *= 0.80  # Apply 20% Discount

    # 3. Apply Regional Multiplier (The "Remote" Logic)
    # E.g., Andaman, Assam, Arunachal Pradesh, Meghalaya, Nagaland, Ladakh
    remote_zones = ['IN-AN', 'IN-AS', 'IN-AR', 'IN-ML', 'IN-NL', 'IN-LA']
    if t_region in remote_zones:
        multiplier *= 1.30  # Apply 30% Premium Tax

    # 4. Add the Final Takeoff/Landing Tax (The "Hop" Penalty)
    takeoff_tax = 2500.0
    total_cost = (raw_cost * multiplier) + takeoff_tax

    return round(total_cost, 2)
```

---

## 4. 🗺️ Expected "Dijkstra" Behaviors to Observe

When running Dijkstra's algorithm on this newly weighted graph, you should document these specific routing anomalies for your thesis:

1.  **The "Shortcut" Trap 🪤:** A small regional airport might be physically closer, but lacking the "Hub Discount" and incurring the severe "Takeoff Tax," Dijkstra will route *around* it to stay on the high-speed, low-cost "Highway" of Large Hubs.
2.  **Island Isolation 🏝️:** Flights to Port Blair (`VOPB`) will correctly appear as expensive "premium" routes. The graph will naturally isolate it, preventing the algorithm from using it as a bizarre stopover for Southeast Asian routing.
3.  **Path Bending (The Triangle Violation) 📐:** For a route like **Surat (VASU) to Agartala (VEAT)**, the straight geometric line is ignored. The algorithm calculates:
    * *Direct (Small to Small):* Extremely high cost (Full distance rate + Remote Surge + Base Fare).
    * *Via Mumbai & Kolkata (Small $\to$ Hub $\to$ Hub $\to$ Small):* Actually cheaper! The massive physical detour is heavily subsidized by the 20% Hub Discount on the long BOM $\to$ CCU leg.



---

## 5. 🗄️ Future Database Schema (PostgreSQL DDL)

To persist this robust mathematical model, your relational database needs a dedicated table to store these pre-calculated economic weights. Here is the SQL schema to build it:

```sql
CREATE TABLE edges_economic_cost (
    edge_id SERIAL PRIMARY KEY,
    source_id VARCHAR(10) REFERENCES airports(ident),
    target_id VARCHAR(10) REFERENCES airports(ident),
    
    -- Physical Data
    distance_km NUMERIC(10, 2) NOT NULL CHECK (distance_km > 0),
    
    -- Economic Data (The Graph Weights)
    calculated_inr NUMERIC(10, 2) NOT NULL,
    hub_discount_applied BOOLEAN DEFAULT FALSE,
    regional_surge_applied BOOLEAN DEFAULT FALSE,
    
    -- Constraints to ensure clean graph traversal
    CONSTRAINT no_self_loops CHECK (source_id != target_id)
);

-- Indexing for Lightning-Fast Dijkstra Adjacency Lookups
CREATE INDEX idx_economic_source ON edges_economic_cost(source_id);
```