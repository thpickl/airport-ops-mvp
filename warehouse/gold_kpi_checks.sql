-- ============================================================================
-- gold_kpi_checks.sql
-- Quick validation / KPI summary queries for the demo.
-- Run against the AirportOpsLakehouse SQL analytics endpoint OR the
-- AirportOpsWarehouse (swap table names for ops.vw_* views there).
-- These are read-only sanity checks used during the stakeholder walkthrough.
-- ============================================================================

-- 1. Headline KPIs per airport
SELECT airport_id, flights, on_time_departure_rate, avg_turnaround_min,
       avg_queue_wait_min, maintenance_anomaly_count,
       energy_kwh_per_flight, energy_kwh_per_pax, incident_count
FROM gold_kpi_daily_summary
ORDER BY airport_id;

-- 2. On-time departure rate (network-wide)
SELECT ROUND(AVG(on_time_departure_rate), 1) AS network_on_time_pct
FROM gold_kpi_daily_summary;

-- 3. Busiest queue hours (top 10 by average wait)
SELECT TOP (10) airport_id, [checkpoint], event_hour, avg_wait_min
FROM gold_queue_by_hour
ORDER BY avg_wait_min DESC;

-- 4. Lowest-utilised gates (candidates for consolidation)
SELECT TOP (10) airport_id, gate_id, flights, utilization_pct
FROM gold_gate_utilization
ORDER BY utilization_pct ASC;

-- 5. Incident count by airport and hour
SELECT airport_id, event_hour, COUNT(*) AS incident_count
FROM gold_incidents_recent
GROUP BY airport_id, event_hour
ORDER BY airport_id, event_hour;

-- 6. Agent context snapshot (future AI/agent hook)
SELECT airport_id, gate_id, operational_status, delay_reason, recommended_action
FROM agent_context
ORDER BY CASE operational_status WHEN 'Action' THEN 1 WHEN 'Watch' THEN 2 ELSE 3 END;
