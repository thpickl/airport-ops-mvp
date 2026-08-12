-- ============================================================================
-- AirportOpsWarehouse_extended.sql
-- Extended, rerunnable serving views over AirportOpsLakehouse.
-- Run AFTER AirportOpsWarehouse_views.sql and deterministic data notebooks 01 -> 09.
-- Grain is documented above every view. CREATE OR ALTER avoids cleanup.
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'ops')
    EXEC('CREATE SCHEMA ops');
GO

-- DIMENSION GRAIN: one row per terminal.
CREATE OR ALTER VIEW ops.vw_dim_terminal AS
SELECT terminal_id, airport_id, terminal_code, terminal_name, floor_count,
       terminal_twin_id, terminal_map_feature_id
FROM [AirportOpsLakehouse].[dbo].[dim_terminal];
GO

-- DIMENSION GRAIN: one row per indoor zone.
CREATE OR ALTER VIEW ops.vw_dim_zone AS
SELECT zone_id, terminal_id, airport_id, zone_code, zone_name, zone_type,
       floor_level, zone_twin_id, zone_map_feature_id
FROM [AirportOpsLakehouse].[dbo].[dim_zone];
GO

-- DIMENSION GRAIN: one row per passenger checkpoint.
CREATE OR ALTER VIEW ops.vw_dim_checkpoint AS
SELECT checkpoint_id, airport_id, terminal_id, zone_id, checkpoint_code,
       checkpoint_name, longitude, latitude, twin_id, map_feature_id
FROM [AirportOpsLakehouse].[dbo].[dim_checkpoint];
GO

-- DIMENSION GRAIN: one row per aircraft stand.
CREATE OR ALTER VIEW ops.vw_dim_stand AS
SELECT stand_id, airport_id, terminal_id, gate_id, stand_name,
       longitude, latitude, twin_id, map_feature_id
FROM [AirportOpsLakehouse].[dbo].[dim_stand];
GO

-- DIMENSION GRAIN: one row per maintainable asset or energy meter.
CREATE OR ALTER VIEW ops.vw_dim_asset AS
SELECT asset_id, airport_id, terminal_id, zone_id, gate_id, asset_type,
       asset_name, asset_class, criticality, twin_id, map_feature_id,
       longitude, latitude
FROM [AirportOpsLakehouse].[dbo].[dim_asset];
GO

-- DIMENSION GRAIN: one row per physical/spatial location.
CREATE OR ALTER VIEW ops.vw_dim_location AS
SELECT location_id, location_type, airport_id, terminal_id, zone_id,
       longitude, latitude, spatial_ref, twin_id, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[dim_location];
GO

-- DIMENSION GRAIN: one row per calendar date in the configured demo range.
CREATE OR ALTER VIEW ops.vw_dim_date AS
SELECT date_key, calendar_date, year, month_number, month_name, day_of_month
FROM [AirportOpsLakehouse].[dbo].[dim_date];
GO

-- DIMENSION GRAIN: one row per hour (0-23), including synthetic shift labels.
CREATE OR ALTER VIEW ops.vw_dim_time AS
SELECT hour AS hour_key, hour_label, operating_period AS shift_name
FROM [AirportOpsLakehouse].[dbo].[dim_time];
GO

-- DIMENSION GRAIN: one row per airline.
CREATE OR ALTER VIEW ops.vw_dim_airline AS
SELECT airline_id, iata, airline_name, alliance
FROM [AirportOpsLakehouse].[dbo].[dim_airline];
GO

-- DIMENSION GRAIN: one row per aircraft type.
CREATE OR ALTER VIEW ops.vw_dim_aircraft AS
SELECT aircraft_type_id, model, manufacturer, category, seats,
       turnaround_target_min
FROM [AirportOpsLakehouse].[dbo].[dim_aircraft];
GO

-- DIMENSION GRAIN: one row per airport service team.
CREATE OR ALTER VIEW ops.vw_dim_service_team AS
SELECT team_id, airport_id, team_name, discipline, shift
FROM [AirportOpsLakehouse].[dbo].[dim_service_team];
GO

-- FACT GRAIN: one row per flight turnaround event.
CREATE OR ALTER VIEW ops.vw_fact_turnaround AS
SELECT flight_event_id, flight_no, airport_id, gate_id, airline_id,
       aircraft_type_id, scheduled_arrival, actual_arrival,
       scheduled_departure, actual_departure, turnaround_start,
       turnaround_end, passenger_count, status, delay_reason,
    turnaround_minutes, departure_delay_minutes, on_time_flag,
    date_key, arrival_date_key, actual_departure_date_key, event_hour
FROM [AirportOpsLakehouse].[dbo].[fact_flight_turnaround_events];
GO

-- FACT GRAIN: one row per checkpoint observation at a 15-minute interval.
CREATE OR ALTER VIEW ops.vw_fact_passenger_flow AS
SELECT queue_metric_id, airport_id, [checkpoint], event_time, queue_length,
    wait_time_min, throughput_pax, date_key, event_hour
FROM [AirportOpsLakehouse].[dbo].[fact_passenger_queue_metrics];
GO

-- FACT GRAIN: one row per asset telemetry observation (six-hour interval).
CREATE OR ALTER VIEW ops.vw_fact_asset_state AS
SELECT asset_state_id, asset_id, airport_id, terminal_id, zone_id, event_time,
    date_key, event_hour, health_status, availability_pct, anomaly_flag,
    telemetry_age_min, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[fact_asset_state];
GO

-- FACT GRAIN: one row per zone/checkpoint observation at a 15-minute interval.
CREATE OR ALTER VIEW ops.vw_fact_zone_occupancy AS
SELECT zone_occupancy_id, airport_id, terminal_id, zone_id, checkpoint_id,
    event_time, date_key, event_hour, occupancy_count, throughput_pax,
       wait_time_min, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[fact_zone_occupancy];
GO

-- FACT GRAIN: one row per energy meter reading.
CREATE OR ALTER VIEW ops.vw_fact_energy_metering AS
SELECT meter_reading_id, airport_id, gate_id, source, event_time, kwh,
       date_key, event_hour
FROM [AirportOpsLakehouse].[dbo].[fact_energy_metering];
GO

-- FACT GRAIN: one row per maintenance event.
CREATE OR ALTER VIEW ops.vw_fact_maintenance_events AS
SELECT maintenance_id, airport_id, gate_id, asset_type, team_id, event_time,
    severity, anomaly_flag, status, description, date_key, event_hour
FROM [AirportOpsLakehouse].[dbo].[fact_maintenance_events];
GO

-- FACT GRAIN: one row per airport weather snapshot.
CREATE OR ALTER VIEW ops.vw_fact_weather AS
SELECT weather_id, airport_id, event_time, temperature_c, wind_kph,
       visibility_km, precip_mm, condition, date_key, event_hour
FROM [AirportOpsLakehouse].[dbo].[fact_weather];
GO

-- SERVING GRAIN: one row per airport for CEO reporting.
CREATE OR ALTER VIEW ops.vw_executive_scorecard AS
SELECT airport_id, airport_name, operational_risk_score, risk_category,
       on_time_departure_rate, avg_turnaround_min, avg_queue_wait_min,
       asset_availability_pct, energy_kwh_per_flight, energy_kwh_per_pax,
       open_high_incidents, maintenance_anomaly_count, observation_timestamp,
       executive_commentary, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[gold_executive_scorecard];
GO

-- SERVING GRAIN: one row per airport for Operational Excellence reporting.
CREATE OR ALTER VIEW ops.vw_operational_excellence_scorecard AS
SELECT h.airport_id,
       h.on_time_departure_rate,
       h.avg_turnaround_min,
       h.avg_queue_wait_min,
       h.asset_availability_pct,
       h.energy_kwh_per_flight,
       h.maintenance_anomaly_count,
       h.incident_count,
       h.operational_risk_score,
       h.risk_category,
       h.observation_timestamp,
       h.is_synthetic
FROM [AirportOpsLakehouse].[dbo].[gold_airport_operational_health] h;
GO

-- SERVING GRAIN: one row per airport.
CREATE OR ALTER VIEW ops.vw_airport_performance AS
SELECT *
FROM [AirportOpsLakehouse].[dbo].[gold_airport_operational_health];
GO

-- SERVING GRAIN: one row per airport, terminal, and hour.
CREATE OR ALTER VIEW ops.vw_terminal_performance AS
SELECT airport_id, terminal_id, event_hour, avg_zone_occupancy,
       avg_queue_wait_min, peak_queue_wait_min, passenger_throughput,
       observed_checkpoints, flow_status, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[gold_terminal_flow_summary];
GO

-- SERVING GRAIN: one row per gate and adjacent stand.
CREATE OR ALTER VIEW ops.vw_gate_turnaround_performance AS
SELECT airport_id, terminal_id, gate_id, stand_id, flights,
       avg_turnaround_min, avg_turnaround_target_min, target_adherence_pct,
       on_time_departure_rate, max_departure_delay_min, primary_delay_reason,
       utilization_pct, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[gold_gate_turnaround_performance];
GO

-- SERVING GRAIN: one row per checkpoint and hour.
CREATE OR ALTER VIEW ops.vw_checkpoint_performance AS
SELECT o.airport_id, o.terminal_id, o.zone_id, o.checkpoint_id, o.event_hour,
       AVG(CAST(o.occupancy_count AS FLOAT)) AS avg_occupancy,
       AVG(o.wait_time_min) AS avg_wait_time_min,
       MAX(o.wait_time_min) AS peak_wait_time_min,
       SUM(o.throughput_pax) AS passenger_throughput
FROM [AirportOpsLakehouse].[dbo].[fact_zone_occupancy] o
GROUP BY o.airport_id, o.terminal_id, o.zone_id, o.checkpoint_id, o.event_hour;
GO

-- SERVING GRAIN: one row per asset.
CREATE OR ALTER VIEW ops.vw_asset_reliability AS
SELECT airport_id, terminal_id, zone_id, gate_id, asset_id, asset_type,
       asset_class, criticality, availability_pct, anomaly_count,
       maintenance_event_count, maintenance_anomaly_count,
       open_maintenance_count, latest_telemetry_timestamp,
       latest_health_status, reliability_status, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[gold_asset_reliability];
GO

-- SERVING GRAIN: one row per gate.
CREATE OR ALTER VIEW ops.vw_energy_efficiency AS
SELECT airport_id, terminal_id, gate_id, flights, passengers, total_kwh,
       energy_kwh_per_flight, energy_kwh_per_passenger,
       efficiency_status, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[gold_energy_efficiency];
GO

-- SERVING GRAIN: one row per incident.
CREATE OR ALTER VIEW ops.vw_incident_details AS
SELECT incident_id, airport_id, gate_id, event_time, event_hour, category,
    severity, delay_minutes, status, description, date_key
FROM [AirportOpsLakehouse].[dbo].[fact_operational_incidents];
GO

-- SERVING GRAIN: one row per governed data product.
CREATE OR ALTER VIEW ops.vw_it_service_health AS
SELECT data_product, layer, source_table, expected_row_count,
       actual_row_count, data_quality_pass_pct, late_record_count,
       quarantined_record_count, pipeline_run_status, refresh_status,
       synthetic_capacity_usage_pct, synthetic_cost_proxy_units,
       security_control_status, observation_timestamp, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[gold_it_service_health];
GO

-- SERVING GRAIN: one row per indoor zone.
CREATE OR ALTER VIEW ops.vw_spatial_operational_context AS
SELECT airport_id, terminal_id, zone_id, location_id, spatial_ref,
       avg_queue_wait_min, peak_queue_wait_min, avg_occupancy, asset_count,
       anomalous_asset_count, operational_status, observation_timestamp,
       is_synthetic
FROM [AirportOpsLakehouse].[dbo].[gold_spatial_operational_status];
GO

-- SERVING GRAIN: one row per gate. Authoritative Data Agent grounding view.
CREATE OR ALTER VIEW ops.vw_data_agent_grounding AS
SELECT airport_id, terminal_id, zone_id, gate_id, stand_id, asset_id,
       operational_status, delay_reason, recommended_action,
       on_time_departure_rate, avg_turnaround_min, avg_turnaround_target_min,
       target_adherence_pct, gate_utilization_pct, avg_queue_wait_min,
       asset_availability_pct, asset_anomaly_count, relevant_incident_id,
       relevant_incident_category, spatial_location_id, spatial_ref,
       observation_timestamp, recommendation_rationale, severity,
       confidence_category, source_table_references,
       human_approval_required, data_freshness_indicator,
       advisory_only, is_synthetic
FROM [AirportOpsLakehouse].[dbo].[agent_context];
GO
