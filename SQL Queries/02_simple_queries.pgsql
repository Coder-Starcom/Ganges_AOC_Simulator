-- 1. Check total node and edges count 
SELECT count(*) FROM airports;
SELECT count(*) FROM edges;

-- 2. Verify coordinate ranges for India
SELECT 
    min(latitude_deg) as south, 
    max(latitude_deg) as north,
    min(longitude_deg) as west, 
    max(longitude_deg) as east 
FROM airports;

-- 3. Check connectivity for a specific state (e.g., IN-TG for Telangana)
SELECT a.name, count(e.target_id) as connections
FROM airports a
LEFT JOIN edges e ON a.ident = e.source_id
WHERE a.iso_region = 'IN-TG'
GROUP BY a.name;