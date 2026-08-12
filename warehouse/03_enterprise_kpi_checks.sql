/* Every query must return zero failure rows. */

SELECT 'route_airport_orphans' AS check_name, COUNT_BIG(*) AS failure_count
FROM ops.vw_dim_route r
LEFT JOIN ops.vw_dim_airport o ON r.origin_airport_id = o.airport_id
LEFT JOIN ops.vw_dim_airport d ON r.destination_airport_id = d.airport_id
WHERE o.airport_id IS NULL OR d.airport_id IS NULL;
GO

SELECT 'booking_passenger_orphans' AS check_name, COUNT_BIG(*) AS failure_count
FROM ops.vw_fact_booking b
LEFT JOIN ops.vw_dim_passenger p ON b.passenger_token = p.passenger_token
WHERE p.passenger_token IS NULL;
GO

SELECT 'baggage_booking_orphans' AS check_name, COUNT_BIG(*) AS failure_count
FROM ops.vw_fact_baggage_journey b
LEFT JOIN ops.vw_fact_booking k ON b.booking_id = k.booking_id
WHERE k.booking_id IS NULL;
GO

SELECT 'invalid_kpi_ranges' AS check_name, COUNT_BIG(*) AS failure_count
FROM ops.vw_airline_route_performance
WHERE on_time_departure_pct NOT BETWEEN 0 AND 100
   OR load_factor_pct NOT BETWEEN 0 AND 100
   OR mishandled_bags_per_1000 < 0;
GO

SELECT 'unsafe_agent_rows' AS check_name, COUNT_BIG(*) AS failure_count
FROM ops.vw_data_agent_enterprise_grounding
WHERE advisory_only <> 1 OR is_synthetic <> 1
   OR source_table_references LIKE '%bronze_%'
   OR source_table_references LIKE '%silver_%'
   OR LOWER(recommendation_text) LIKE '%automatically%'
   OR LOWER(recommendation_text) LIKE '%dispatch %'
   OR LOWER(recommendation_text) LIKE '%command %';
GO

SELECT 'persona_coverage' AS check_name,
       CASE WHEN COUNT(DISTINCT persona) = 7 THEN 0 ELSE 1 END AS failure_count
FROM ops.vw_persona_scorecard;
GO

SELECT airport_id, SUM(checked_bags) AS checked_bags,
       SUM(mishandled_bags) AS mishandled_bags,
       CAST(1000.0 * SUM(mishandled_bags) / NULLIF(SUM(checked_bags), 0) AS decimal(12,2)) AS mishandled_bags_per_1000
FROM ops.vw_baggage_performance
GROUP BY airport_id;
GO
