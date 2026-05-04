-- Create a schedule table
DROP TABLE IF EXISTS flights;

CREATE TABLE flights (
    flight_id SERIAL PRIMARY KEY,
    source_id VARCHAR(10) REFERENCES airports(ident),
    target_id VARCHAR(10) REFERENCES airports(ident),
    departure_time TIME,
    arrival_time TIME,
    cost_inr DOUBLE PRECISION
);

-- Indexing for high-performance Dijkstra lookups
CREATE INDEX idx_flight_source ON flights(source_id);
CREATE INDEX idx_flight_times ON flights(departure_time);