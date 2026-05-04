-- Reset for clean import
DROP TABLE IF EXISTS edges;
DROP TABLE IF EXISTS airports;

-- The Node Table (Strictly following your 6 columns)
CREATE TABLE airports (
    ident VARCHAR(10) PRIMARY KEY,
    name TEXT,
    latitude_deg DOUBLE PRECISION NOT NULL,
    longitude_deg DOUBLE PRECISION NOT NULL,
    iso_region VARCHAR(10),
    type TEXT
);

-- The Edge Table for Dijkstra
CREATE TABLE edges (
    source_id VARCHAR(10) REFERENCES airports(ident),
    target_id VARCHAR(10) REFERENCES airports(ident),
    distance_km DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (source_id, target_id)
);