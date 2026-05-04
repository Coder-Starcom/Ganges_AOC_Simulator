-- Separate table for Economic Weights
DROP TABLE IF EXISTS edges_economic;

CREATE TABLE edges_economic (
    source_id VARCHAR(10) REFERENCES airports(ident),
    target_id VARCHAR(10) REFERENCES airports(ident),
    distance_km DOUBLE PRECISION,
    cost_inr DOUBLE PRECISION, -- The non-linear weight
    logic_applied TEXT,
    PRIMARY KEY (source_id, target_id)
);