-- ============================================================================
-- extended_quality_checks.sql
-- Read-only Warehouse validation. Every result returns PASS or FAIL visibly.
-- Run after AirportOpsWarehouse_views.sql and AirportOpsWarehouse_extended.sql.
-- Notebook 06 is the fail-fast executable validation surface.
-- ============================================================================

-- 1. Serving view accessibility and expected default row counts.
SELECT 'vw_executive_scorecard' AS check_name,
      CASE WHEN COUNT(*) = 15 THEN 'PASS' ELSE 'FAIL' END AS status,
      COUNT(*) AS actual_count, 15 AS expected_count
FROM ops.vw_executive_scorecard
UNION ALL
   SELECT 'vw_gate_turnaround_performance', CASE WHEN COUNT(*) = 90 THEN 'PASS' ELSE 'FAIL' END, COUNT(*), 90
FROM ops.vw_gate_turnaround_performance
UNION ALL
   SELECT 'vw_asset_reliability', CASE WHEN COUNT(*) = 540 THEN 'PASS' ELSE 'FAIL' END, COUNT(*), 540
FROM ops.vw_asset_reliability
UNION ALL
   SELECT 'vw_spatial_operational_context', CASE WHEN COUNT(*) = 60 THEN 'PASS' ELSE 'FAIL' END, COUNT(*), 60
FROM ops.vw_spatial_operational_context
UNION ALL
   SELECT 'vw_data_agent_grounding', CASE WHEN COUNT(*) = 90 THEN 'PASS' ELSE 'FAIL' END, COUNT(*), 90
FROM ops.vw_data_agent_grounding;

-- 2. Duplicate business keys.
SELECT 'duplicate_terminal_id' AS check_name,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
       COUNT(*) AS failure_count
FROM (SELECT terminal_id FROM ops.vw_dim_terminal GROUP BY terminal_id HAVING COUNT(*) > 1) d
UNION ALL
SELECT 'duplicate_zone_id', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM (SELECT zone_id FROM ops.vw_dim_zone GROUP BY zone_id HAVING COUNT(*) > 1) d
UNION ALL
SELECT 'duplicate_asset_id', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM (SELECT asset_id FROM ops.vw_dim_asset GROUP BY asset_id HAVING COUNT(*) > 1) d
UNION ALL
SELECT 'duplicate_agent_gate_id', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM (SELECT gate_id FROM ops.vw_data_agent_grounding GROUP BY gate_id HAVING COUNT(*) > 1) d;

-- 3. Orphan foreign keys.
SELECT 'orphan_terminal_airport' AS check_name,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
       COUNT(*) AS failure_count
FROM ops.vw_dim_terminal t
LEFT JOIN ops.vw_dim_airport a ON t.airport_id = a.airport_id
WHERE a.airport_id IS NULL
UNION ALL
SELECT 'orphan_zone_terminal', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM ops.vw_dim_zone z
LEFT JOIN ops.vw_dim_terminal t ON z.terminal_id = t.terminal_id
WHERE t.terminal_id IS NULL
UNION ALL
SELECT 'orphan_asset_zone', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM ops.vw_dim_asset x
LEFT JOIN ops.vw_dim_zone z ON x.zone_id = z.zone_id
WHERE z.zone_id IS NULL
UNION ALL
SELECT 'orphan_agent_gate', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM ops.vw_data_agent_grounding g
LEFT JOIN ops.vw_dim_gate d ON g.gate_id = d.gate_id
WHERE d.gate_id IS NULL;

-- 4. Null, freshness, and advisory safety checks.
SELECT 'agent_required_fields' AS check_name,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
       COUNT(*) AS failure_count
FROM ops.vw_data_agent_grounding
WHERE airport_id IS NULL OR terminal_id IS NULL OR zone_id IS NULL OR gate_id IS NULL
   OR stand_id IS NULL OR asset_id IS NULL OR observation_timestamp IS NULL
   OR source_table_references IS NULL OR data_freshness_indicator IS NULL
UNION ALL
SELECT 'agent_advisory_only', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM ops.vw_data_agent_grounding
WHERE advisory_only = 0 OR is_synthetic = 0
UNION ALL
SELECT 'agent_approval_for_consequential', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM ops.vw_data_agent_grounding
WHERE severity <> 'Informational' AND human_approval_required = 0
UNION ALL
SELECT 'executive_freshness', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM ops.vw_executive_scorecard
WHERE observation_timestamp <> CAST('2026-07-01T23:59:00' AS DATETIME2);

-- 5. KPI range checks.
SELECT 'executive_kpi_ranges' AS check_name,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS status,
       COUNT(*) AS failure_count
FROM ops.vw_executive_scorecard
WHERE on_time_departure_rate < 0 OR on_time_departure_rate > 100
   OR operational_risk_score < 0 OR operational_risk_score > 100
   OR avg_turnaround_min <= 0 OR avg_queue_wait_min < 0
UNION ALL
SELECT 'gate_kpi_ranges', CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END, COUNT(*)
FROM ops.vw_gate_turnaround_performance
WHERE target_adherence_pct < 0 OR target_adherence_pct > 100
   OR utilization_pct < 0 OR utilization_pct > 100;
