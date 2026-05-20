# Ganges International Airline Operations Center (AOC) Simulator ✈️💼

A high-concurrency, data-driven Enterprise Airline Operations Center simulation engine. This platform models a live command dashboard used by commercial air carriers to optimize asset yield, route networks, and manage transactional state-mutations during systemic irregular operations (IROPS).

### 🌐 Live Production Application

👉 [**(https://ganges-aoc-simulator.streamlit.app/)**](https://ganges-aoc-simulator.streamlit.app/)

---

## 🧭 The High-Concept Architecture

To keep this project grounded: a production-grade commercial airline infrastructure requires hundreds of engineers and decades of investment. This simulator implements **~25% of a full-scale AOC ecosystem**, focusing 100% of its resources on the most complex engineering challenge: the **analytical data and transaction logic brain**.

The system completely decouples the visual presentation layer from the transactional mutation engine using a serverless cloud data topology:

- **Frontend Dashboard (Streamlit Cloud):** A real-time executive cockpit displaying fleet telemetry, live P&L data, and pathfinding routing analytics.
- **Background Mutation Engine (Local Python Workers):** A multi-threaded simulation pipeline that floods the database with chaotic, concurrent booking queries to mimic consumer demand spikes.
- **Central Database Layer (Neon Serverless PostgreSQL):** A fully transactional relational schema enforcing strict ACID compliance.

---

## 🛠️ Systemic Features & Tab Layout

### 📡 Tab 1: Live Tactical Radar

- **Chronological Gate-Lock Pinning:** Dynamically filters and pulls up imminent flights (`WHERE departure_timestamp >= NOW()`).
- **Real-Time Aviation Metrics:** Computes **Available Seat Kilometers (ASK)**, **Revenue Passenger Kilometers (RPK)**, and asset **Load Factors** on the fly.
- **🔴 High Leakage Alarm:** A programmatic alert that highlights flights operating under 35% capacity, signaling operators to enact immediate pricing or route consolidation maneuvers.

### 📊 Tab 2: Executive P&L Cockpit

- **Yield Viability Matrix:** Evaluates corporate financial health by tracking the live spread between **Revenue per Available Seat Kilometer (RASK)** and **Cost per Available Seat Kilometer (CASK)**.
- **Dynamic Jet Fuel Multiplier:** An interactive scenario simulator that dynamically scales variable cost curves, allowing executives to stress-test profit margins and cash runway against fuel price volatility.
- **High-Performance Plotly Grid:** Dense data visualizations analyzing aircraft model efficiency and carbon taxation liabilities.

### 🚨 Tab 3: IROPS & Goodwill Ledger

- **Deterministic Chaos Simulator:** Allows operators to trigger a systemic weather blockade, completely pruning a major hub node (e.g., Cairo CAI or Amman AMM) from the active graph topology.
- **Downstream Disruption Evaluator:** Calculates real-time cascading flight delays, regulatory financial penalties, and tracks crew legality metrics against mandatory **Legal Duty Ceiling** thresholds.
- **Concurrency Stress Injector:** Provides a diagnostic control to fire 100 simultaneous seat-booking queries via a `ThreadPoolExecutor`.
- **ACID Safety Proof:** Demonstrates row-level transaction safety using explicit `SELECT ... FOR UPDATE` syntax to eradicate dirty reads and double-bookings during extreme data traffic.

### 🎯 Tab 4: Strategic Playbook Analyst

- **Time-Dependent Graph Search Router:** A custom graph traversal engine that evaluates paths across network nodes while enforcing strict temporal boundaries.
- **Turnaround Buffer Validation:** A constraint layer ensuring that Leg 2 cannot be booked unless its departure timestamp accounts for Leg 1's arrival plus a mandatory 45-minute ground turnaround and baggage transfer window.
- **Multi-Objective Persona Selection:** Automatically optimizes paths across three distinct operational modes:
  - 🟢 **Leisure:** Optimizes for minimum total ticket price.
  - 🔵 **Business:** Optimizes for minimum total temporal duration.
  - 🟣 **Logistics:** Optimizes for minimum physical distance to reduce fleet engine wear.

---

## 📁 Repository Structure

```text
DB_Project/
├── setup/                      # Database schema initialization & seeding assets
├── engines/                    # Core pathfinding, simulation, and lock logic
├── data/                       # Structured CSV datasets and configuration JSONs
├── research/                   # Exploratory notebooks and ad-hoc query tests
├── app.py                      # Main Streamlit Production UI Entrypoint
├── Cost.md                     # Aviation unit economics documentation
├── requirements.txt            # Package manifest configuration
└── README.md                   # System presentation documentation
```

---

## 🚀 Local Quickstart Guide

### 1. Install Dependencies

Ensure you are using Python 3.10+ and run:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a secure `.env` file in the root directory (this file is explicitly locked out of GitHub tracking via `.gitignore`):

```text
DATABASE_URL="postgres://username:password@your-neon-host.neon.tech/dbname?sslmode=require"
```

### 3. Initialize the Database Schema

```bash
python setup/clean_init_db.py
python setup/add_routes.py
```

### 4. Run the Local Simulation Ecosystem

To simulate real-time transactional load, run the demand simulator in a background terminal:

```bash
python engines/demand_simulator.py
```

Then launch the web interface:

```bash
streamlit run app.py
```
