SELECT source_id, target_id, distance_km
FROM edges
WHERE RANDOM() < 0.3  
ORDER BY RANDOM();    
