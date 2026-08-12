# Lakehouse-to-Warehouse Lineage

| Bronze source | Silver target | Gold product | Warehouse serving view |
|---|---|---|---|
| `bronze_flight_turnaround` | `fact_flight_turnaround_events` | base KPI + gate performance | `ops.vw_fact_turnaround`, `ops.vw_gate_turnaround_performance` |
| `bronze_passenger_queue` | `fact_passenger_queue_metrics`, `fact_zone_occupancy` | terminal flow | `ops.vw_fact_passenger_flow`, `ops.vw_checkpoint_performance` |
| `bronze_energy` | `fact_energy_metering` | energy efficiency | `ops.vw_energy_efficiency` |
| `bronze_maintenance` | `fact_maintenance_events` | asset reliability | `ops.vw_asset_reliability` |
| `bronze_weather` | `fact_weather` | event-level grounding | `ops.vw_fact_weather` |
| `bronze_operational_incidents` | `fact_operational_incidents` | health + agent context | `ops.vw_incident_details` |
| `bronze_terminal_zones` | `dim_terminal`, `dim_zone`, `dim_location` | terminal/spatial status | `ops.vw_terminal_performance`, `ops.vw_spatial_operational_context` |
| `bronze_checkpoint_registry` | `dim_checkpoint` | terminal flow | `ops.vw_dim_checkpoint` |
| `bronze_stand_registry` | `dim_stand`, `bridge_gate_stand` | gate performance | `ops.vw_dim_stand` |
| `bronze_asset_registry` | `dim_asset`, `bridge_asset_location`, `fact_asset_state` | reliability/spatial | `ops.vw_asset_reliability` |
| all curated products | validation fingerprints | executive / IT / agent | `ops.vw_executive_scorecard`, `ops.vw_it_service_health`, `ops.vw_data_agent_grounding` |
| `bronze_route`, `bronze_flight_route` | `dim_route`, `bridge_flight_route` | airline/route performance | `ops.vw_airline_route_performance` |
| `bronze_aircraft_fleet` | `dim_aircraft_fleet` | airline/route performance | `ops.vw_dim_aircraft_fleet` |
| `bronze_employee`, `bronze_employee_roster` | `dim_employee`, `fact_employee_roster` | workforce coverage | `ops.vw_workforce_coverage` |
| `bronze_passenger`, `bronze_booking` | `dim_passenger`, `fact_booking` | aggregate airline/CX only | `ops.vw_airline_route_performance`, `ops.vw_customer_experience` |
| `bronze_baggage_journey` | `fact_baggage_journey` | baggage performance | `ops.vw_baggage_performance` |
| `bronze_retail_pos` | `fact_retail_pos` | retail performance | `ops.vw_retail_performance` |
| `bronze_turnaround_phase` | `fact_turnaround_phase` | phase performance | `ops.vw_turnaround_phase_performance` |
| `bronze_customer_experience` | `fact_customer_experience` | customer experience | `ops.vw_customer_experience` |
| `bronze_skill`, `bronze_employee_skill` | `dim_skill`, `bridge_employee_skill` | workforce KPIs | `ops.vw_workforce_kpi` |
| `bronze_boarding_event` | `fact_boarding_event` | passenger-flow risk | `ops.vw_passenger_flow_kpi` |
| `bronze_baggage_scan` | `fact_baggage_scan` | baggage scan completeness | `ops.vw_baggage_kpi` |
| `bronze_ramp_service_task` | `fact_ramp_service_task` | turnaround/workforce KPIs | `ops.vw_flight_operations_kpi`, `ops.vw_workforce_kpi` |
| `bronze_maintenance_work_order` | `fact_maintenance_work_order` | maintenance KPIs | `ops.vw_maintenance_kpi` |
| `bronze_recommendation_event` | `fact_recommendation` | acceptance/approval KPI | `ops.vw_incident_customer_kpi` |

Warehouse objects are views, not copied tables. Cross-database three-part names point from `AirportOpsWarehouse` to the Lakehouse SQL analytics endpoint in the same workspace. Notebook 12 materializes the same contract in `lineage_contract` and validates coverage.

Data Agent sources stop at approved Gold/`ops` views or curated KQL functions. Passenger, booking, bag, employee, Bronze, Silver, and raw-file objects are excluded from its allowlist.
