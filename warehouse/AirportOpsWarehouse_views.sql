-- ============================================================================
-- AirportOpsWarehouse_views.sql
-- Curated KPI views for the AirportOpsWarehouse, layered on top of the
-- Gold Delta tables in AirportOpsLakehouse.
--
-- PREREQUISITES:
--   * AirportOpsLakehouse and AirportOpsWarehouse exist in the SAME workspace.
--   * Notebooks 01 -> 02 -> 03 have run for the base views.
--   * Notebooks 04 -> 05 add the extended objects deployed by
--     AirportOpsWarehouse_extended.sql.
--   * Run this script in the AirportOpsWarehouse SQL query editor.
--
-- Cross-database three-part naming ([db].[schema].[object]) lets the Warehouse
-- read the Lakehouse SQL analytics endpoint (default schema = dbo).
-- Re-runnable: uses CREATE OR ALTER.
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'ops')
    EXEC('CREATE SCHEMA ops');
GO

CREATE OR ALTER VIEW ops.vw_kpi_daily_summary AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_kpi_daily_summary];
GO

CREATE OR ALTER VIEW ops.vw_turnaround_by_hour AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_turnaround_by_hour];
GO

CREATE OR ALTER VIEW ops.vw_queue_by_hour AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_queue_by_hour];
GO

CREATE OR ALTER VIEW ops.vw_gate_utilization AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_gate_utilization];
GO

CREATE OR ALTER VIEW ops.vw_energy_summary AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_energy_summary];
GO

CREATE OR ALTER VIEW ops.vw_incidents_recent AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_incidents_recent];
GO

CREATE OR ALTER VIEW ops.vw_agent_context AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[agent_context];
GO

-- Dimension passthrough (handy for report joins done in the Warehouse)
CREATE OR ALTER VIEW ops.vw_dim_airport AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_airport];
GO

CREATE OR ALTER VIEW ops.vw_dim_gate AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_gate];
GO

CREATE OR ALTER VIEW ops.vw_fact_flight_turnaround_events AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[fact_flight_turnaround_events];
GO

CREATE OR ALTER VIEW ops.vw_fact_passenger_queue_metrics AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[fact_passenger_queue_metrics];
GO

CREATE OR ALTER VIEW ops.vw_fact_operational_incidents AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[fact_operational_incidents];
GO
