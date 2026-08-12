-- Semantic-model validation queries. Run in AirportOpsWarehouse.

-- Weighted network measures used by KPI cards.
SELECT
    SUM(on_time_departure_rate * flights) / NULLIF(SUM(flights), 0) AS expected_on_time_departure_pct,
    SUM(avg_turnaround_min * flights) / NULLIF(SUM(flights), 0) AS expected_avg_turnaround_min,
    SUM(flights) AS expected_total_flights
FROM ops.vw_kpi_daily_summary;

-- Executive measures.
SELECT
    AVG(operational_risk_score) AS expected_operational_risk_score,
    SUM(CASE WHEN risk_category = 'High' THEN 1 ELSE 0 END) AS expected_high_risk_airports,
    SUM(open_high_incidents) AS expected_open_high_incidents
FROM ops.vw_executive_scorecard;

-- Weighted turnaround target adherence.
SELECT
    SUM(target_adherence_pct * flights) / NULLIF(SUM(flights), 0) AS expected_target_adherence_pct
FROM ops.vw_gate_turnaround_performance;

-- Reliability and passenger-flow measures.
SELECT
    AVG(availability_pct) AS expected_asset_availability_pct,
    SUM(CASE WHEN reliability_status = 'Anomalous' THEN 1 ELSE 0 END) AS expected_anomalous_assets,
    SUM(open_maintenance_count) AS expected_open_maintenance_items
FROM ops.vw_asset_reliability;

SELECT
    SUM(passenger_throughput) AS expected_passenger_throughput,
    MAX(peak_queue_wait_min) AS expected_peak_queue_wait_min
FROM ops.vw_terminal_performance;

-- CIO/IT and agent measures.
SELECT
    AVG(data_quality_pass_pct) AS expected_data_quality_pass_pct,
    SUM(CASE WHEN pipeline_run_status <> 'SyntheticSuccess' THEN 1 ELSE 0 END) AS expected_failed_products,
    SUM(late_record_count) AS expected_late_records,
    SUM(quarantined_record_count) AS expected_quarantined_records,
    AVG(synthetic_capacity_usage_pct) AS expected_synthetic_capacity_pct,
    SUM(synthetic_cost_proxy_units) AS expected_synthetic_cost_proxy_units
FROM ops.vw_it_service_health;

SELECT
    SUM(CASE WHEN human_approval_required = 1 THEN 1 ELSE 0 END) AS expected_recommendations_requiring_approval,
    SUM(CASE WHEN operational_status = 'Action' THEN 1 ELSE 0 END) AS expected_action_status_gates,
    SUM(CASE WHEN data_freshness_indicator = 'CurrentWithin6Hours' THEN 1.0 ELSE 0.0 END) * 100.0 / NULLIF(COUNT(*), 0) AS expected_current_grounding_pct
FROM ops.vw_data_agent_grounding;
