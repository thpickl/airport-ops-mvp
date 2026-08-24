/* Curated enterprise serving views. Lakehouse and Warehouse must share a supported workspace. */

CREATE OR ALTER VIEW ops.vw_dim_organization AS SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_organization];
GO
CREATE OR ALTER VIEW ops.vw_dim_route AS SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_route];
GO
CREATE OR ALTER VIEW ops.vw_dim_aircraft_fleet AS SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_aircraft_fleet];
GO
CREATE OR ALTER VIEW ops.vw_dim_work_team AS SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_work_team];
GO
CREATE OR ALTER VIEW ops.vw_dim_employee AS SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_employee];
GO
CREATE OR ALTER VIEW ops.vw_dim_retail_outlet AS SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_retail_outlet];
GO
CREATE OR ALTER VIEW ops.vw_dim_retail_product AS SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_retail_product];
GO
CREATE OR ALTER VIEW ops.vw_dim_passenger AS SELECT * FROM [AirportOpsLakehouse].[dbo].[dim_passenger];
GO
CREATE OR ALTER VIEW ops.vw_bridge_flight_route AS SELECT * FROM [AirportOpsLakehouse].[dbo].[bridge_flight_route];
GO
CREATE OR ALTER VIEW ops.vw_fact_employee_roster AS SELECT * FROM [AirportOpsLakehouse].[dbo].[fact_employee_roster];
GO
CREATE OR ALTER VIEW ops.vw_fact_booking AS SELECT * FROM [AirportOpsLakehouse].[dbo].[fact_booking];
GO
CREATE OR ALTER VIEW ops.vw_fact_baggage_journey AS SELECT * FROM [AirportOpsLakehouse].[dbo].[fact_baggage_journey];
GO
CREATE OR ALTER VIEW ops.vw_fact_retail_pos AS SELECT * FROM [AirportOpsLakehouse].[dbo].[fact_retail_pos];
GO
CREATE OR ALTER VIEW ops.vw_fact_turnaround_phase AS SELECT * FROM [AirportOpsLakehouse].[dbo].[fact_turnaround_phase];
GO
CREATE OR ALTER VIEW ops.vw_fact_customer_experience AS SELECT * FROM [AirportOpsLakehouse].[dbo].[fact_customer_experience];
GO
CREATE OR ALTER VIEW ops.vw_airline_route_performance AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_airline_route_performance];
GO
CREATE OR ALTER VIEW ops.vw_baggage_performance AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_baggage_performance];
GO
CREATE OR ALTER VIEW ops.vw_workforce_coverage AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_workforce_coverage];
GO
CREATE OR ALTER VIEW ops.vw_retail_performance AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_retail_performance];
GO
CREATE OR ALTER VIEW ops.vw_customer_experience AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_customer_experience];
GO
CREATE OR ALTER VIEW ops.vw_turnaround_phase_performance AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_turnaround_phase_performance];
GO
CREATE OR ALTER VIEW ops.vw_persona_scorecard AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_persona_scorecard];
GO
CREATE OR ALTER VIEW ops.vw_data_agent_enterprise_grounding AS
SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_data_agent_enterprise_context]
WHERE advisory_only = 1 AND is_synthetic = 1;
GO

CREATE OR ALTER VIEW ops.vw_flight_operations_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_flight_operations_kpi];
GO
CREATE OR ALTER VIEW ops.vw_passenger_flow_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_passenger_flow_kpi];
GO
CREATE OR ALTER VIEW ops.vw_baggage_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_baggage_kpi];
GO
CREATE OR ALTER VIEW ops.vw_workforce_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_workforce_kpi];
GO
CREATE OR ALTER VIEW ops.vw_maintenance_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_maintenance_kpi];
GO
CREATE OR ALTER VIEW ops.vw_energy_sustainability_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_energy_sustainability_kpi];
GO

-- SERVING GRAIN: one row per scenario and airport. Optimised rows are modelled projections.
CREATE OR ALTER VIEW ops.vw_scenario_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_scenario_kpi];
GO

-- SERVING GRAIN: one row per programme outcome measure.
CREATE OR ALTER VIEW ops.vw_scenario_outcome_comparison AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_scenario_outcome_comparison];
GO
CREATE OR ALTER VIEW ops.vw_commercial_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_commercial_kpi];
GO
CREATE OR ALTER VIEW ops.vw_incident_customer_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_incident_customer_kpi];
GO
CREATE OR ALTER VIEW ops.vw_kpi_catalog AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_kpi_catalog];
GO
CREATE OR ALTER VIEW ops.vw_aircraft_rotation_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_aircraft_rotation_kpi];
GO
CREATE OR ALTER VIEW ops.vw_retail_inventory_kpi AS SELECT * FROM [AirportOpsLakehouse].[dbo].[gold_retail_inventory_kpi];
GO
