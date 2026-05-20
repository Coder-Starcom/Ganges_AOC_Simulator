# ✈️Ganges International Quantum Operations Engine

## Operational Mathematics & Econometric Reference Ledger

This document establishes the official mathematical equations governing structural cost isolation, dynamic pricing vectors, and non-FIFO graph relaxation rules within the Ganges core backend network simulation.

---

## 🏛️ 1. The Cost Floor: Direct Operating Cost ($DOC$) Matrix

The system calculates an absolute financial floor for every single flight instance $f$ operating on a spatial network route $r$ using a specific assigned physical aircraft asset $a$.

### 1.1 The Primary Cost Model

$$DOC_{f} = \left[ \text{Dist}_r \times \kappa_a \times \left( P_{\text{fuel}} \times \phi_{\text{shock}} \right) \right] + \left[ \text{Dur}_{f} \times \left( C_{\text{crew}} + M_{\text{maint}} \right) \right] + \left[ L_{\text{origin}} + T_{\text{dest}} \right]$$

### 1.2 Variable Key and Metric Units

- **$DOC_f$** $\in \mathbb{R}^+$ $(\text{INR } ₹)$: Total baseline capital expenditure required to move the physical airframe over the vector.
- **$\text{Dist}_r$** $(\text{km})$: Total Great-Circle geodetic distance of the path edge.
- **$\kappa_a$** $(\text{L/km})$: Physical volumetric fuel burn coefficient unique to the fleet asset type.
- **$P_{\text{fuel}}$** $(₹/\text{L})$: Standard market baseline price per liter of Jet-A fuel.
- **$\phi_{\text{shock}}$** $(\phi \ge 0.0)$: Global macroeconomic state variable multiplier simulating supply shocks.
- **$\text{Dur}_f$** $(\text{hrs})$: Clock-to-clock block execution duration.
- **$C_{\text{crew}}$** $(₹/\text{hr})$: Fully-loaded combined salary and accommodation cost for the flight crew per block hour.
- **$M_{\text{maint}}$** $(₹/\text{hr})$: Mechanical lifecycle amortization and engine overhaul provisioning rate per block hour.
- **$L_{\text{origin}}$** $(₹)$: Base weight-class landing and runway infrastructure usage fee at the origin node.
- **$T_{\text{dest}}$** $(₹)$: Fixed terminal turnaround handling, catering, and security service toll at the destination node.

---

## 📈 2. The Pricing Ceiling: Stochastic Yield Optimization Engine

Once the structural $DOC_f$ cost floor is computed, the system maps the minimum break-even price boundary ($Base\_Fare_f$) before running an exponential time-inventory decay curve to find the market retail price $P(t)$.

### 2.1 The Basal Break-Even Fare

$$Base\_Fare_f = \frac{DOC_f}{\text{Cap}_a \times \text{Load\_Factor}_{\text{target}}}$$

- **$\text{Cap}_a$** $(\mathbb{N}^+)$: Absolute seating capacity layout of the assigned aircraft asset.
- **$\text{Load\_Factor}_{\text{target}}$** $(\% \text{ as a decimal})$: Target financial optimization threshold (e.g., $0.75$ or $75\%$).

### 2.2 The Non-Linear Asymmetric Pricing Ceiling $P(t)$

$$P(t) = Base\_Fare_f \times \exp\left( \lambda \cdot I_t \right) \times \left( 1 + \frac{\gamma}{\max(\tau, 0.01)^\delta} \right)$$

### 2.3 Structural Parameters & Shape Modifiers

- **$I_t = \frac{\text{Seats\_Booked}_f}{\text{Cap}_a}$**: Inventory Utilization Matrix ratio ($0.0 \le I_t \le 1.0$).
- **$\tau = t_{\text{departure}} - t_{\text{current}}$**: The temporal horizon window remaining until flight dispatch, measured in fractional days or hours.
- **$\lambda$**: Alpha Capacity Elasticity coefficient (controls curve steepness as seats sell out).
- **$\gamma$**: Temporal Velocity Scale coefficient (controls the maximum height of the final fare surge).
- **$\delta$**: Urgency Decay Factor exponent (controls the acceleration rate of prices near departure).

---

## 🗺️ 3. Multi-Objective Graph Strategy Matrices

During graph search execution, path traversal doesn't merely sort results at completion; it dynamically switches the edge relaxation weight function $w(e)$ used by the pathfinder based on the active corporate or leisure strategy.

### 3.1 🟢 The Cheapest Strategy (Stochastic Capital Minimization)

Optimizes strictly for dynamic retail prices. The algorithm hunts for capacity anomalies and deep discounts across winding paths, ignoring layover duration.

$$w(e) = P(t)_{f}$$

### 3.2 🔵 The Fastest Strategy (Absolute Temporal Matrix)

Optimizes for the minimum elapsed clock time from origin departure to terminal destination arrival, factoring in flight time and ground layover waits.

$$w(e) = \text{Dur}_{f} + \text{Layover\_Time}(\text{Arrival}_{f-1}, \text{Departure}_f)$$

$$\text{Subject to Connection Boundary Edge Rule: } \text{Departure}_f \ge \text{Arrival}_{f-1} + \Delta T_{\text{turnaround}}$$

_(If connection time is lower than the airport's physical terminal turnaround limit $\Delta T$, then $w(e) = \infty$)_

### 3.3 🟣 The Shortest Strategy (Geodetic Haversine Restraint)

Optimizes across pure, physical spatial lines around the Earth's atmosphere, ignoring seat availability, pricing variations, and schedule timelines completely.

$$w(e) = 2R \cdot \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$

- **$R$**: Mean radius of the Earth ($\approx 6,371 \text{ km}$).
- **$\phi_1, \phi_2$**: Latitude coordinates of the source and target nodes in radians.
- **$\Delta\phi, \Delta\lambda$**: Geodetic differences in latitude and longitude across the vector points.
