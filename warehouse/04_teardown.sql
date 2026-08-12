/* Scoped rollback for demo-owned enterprise views and audit table. */

DROP VIEW IF EXISTS ops.vw_kpi_catalog;
DROP VIEW IF EXISTS ops.vw_retail_inventory_kpi;
DROP VIEW IF EXISTS ops.vw_aircraft_rotation_kpi;
DROP VIEW IF EXISTS ops.vw_incident_customer_kpi;
DROP VIEW IF EXISTS ops.vw_commercial_kpi;
DROP VIEW IF EXISTS ops.vw_energy_sustainability_kpi;
DROP VIEW IF EXISTS ops.vw_maintenance_kpi;
DROP VIEW IF EXISTS ops.vw_workforce_kpi;
DROP VIEW IF EXISTS ops.vw_baggage_kpi;
DROP VIEW IF EXISTS ops.vw_passenger_flow_kpi;
DROP VIEW IF EXISTS ops.vw_flight_operations_kpi;
DROP VIEW IF EXISTS ops.vw_data_agent_enterprise_grounding;
DROP VIEW IF EXISTS ops.vw_persona_scorecard;
DROP VIEW IF EXISTS ops.vw_turnaround_phase_performance;
DROP VIEW IF EXISTS ops.vw_customer_experience;
DROP VIEW IF EXISTS ops.vw_retail_performance;
DROP VIEW IF EXISTS ops.vw_workforce_coverage;
DROP VIEW IF EXISTS ops.vw_baggage_performance;
DROP VIEW IF EXISTS ops.vw_airline_route_performance;
DROP VIEW IF EXISTS ops.vw_fact_customer_experience;
DROP VIEW IF EXISTS ops.vw_fact_turnaround_phase;
DROP VIEW IF EXISTS ops.vw_fact_retail_pos;
DROP VIEW IF EXISTS ops.vw_fact_baggage_journey;
DROP VIEW IF EXISTS ops.vw_fact_booking;
DROP VIEW IF EXISTS ops.vw_fact_employee_roster;
DROP VIEW IF EXISTS ops.vw_bridge_flight_route;
DROP VIEW IF EXISTS ops.vw_dim_passenger;
DROP VIEW IF EXISTS ops.vw_dim_retail_product;
DROP VIEW IF EXISTS ops.vw_dim_retail_outlet;
DROP VIEW IF EXISTS ops.vw_dim_employee;
DROP VIEW IF EXISTS ops.vw_dim_work_team;
DROP VIEW IF EXISTS ops.vw_dim_aircraft_fleet;
DROP VIEW IF EXISTS ops.vw_dim_route;
DROP VIEW IF EXISTS ops.vw_dim_organization;
GO

/* Keep audit.deployment_run by default as rollback evidence. Remove only through explicit teardown approval. */
