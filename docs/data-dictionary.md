# Data Dictionary

This document covers the base operational, physical/spatial, enterprise, reliability, commercial, IT, and agent products.

## Bronze

### Fictional reference Bronze

| Table | Grain | Classification |
|---|---|---|
| `bronze_country` | fictional region/time-zone group | Synthetic master data |
| `bronze_airport` | fictional airport | Synthetic master data; exactly 15 |
| `bronze_airline` | fictional airline | Synthetic master data; exactly 20 |
| `bronze_aircraft` | fictional aircraft type | Synthetic master data and operating assumptions; exactly 16 |

`bronze_airport_group_assignment`, `bronze_airline_airport_service`, and `bronze_airline_aircraft_eligibility` are synthetic assumptions, not public commercial relationships.

| Table | Grain | Key | Purpose |
|---|---|---|---|
| `bronze_demo_config` | demo configuration | `config_id` | Runtime copy of seed/date/volume contract |
| `bronze_airport_spatial` | airport | `airport_id` | WGS84 point, DTDL and map IDs |
| `bronze_terminal_zones` | terminal-zone pair | `terminal_id`, `zone_id` | Source-shaped hierarchy and WKT |
| `bronze_checkpoint_registry` | checkpoint | `checkpoint_id` | Physical passenger processing points |
| `bronze_stand_registry` | stand | `stand_id` | Gate/stand adjacency source |
| `bronze_asset_registry` | asset | `asset_id` | Maintainable assets and energy meters |
| `bronze_twin_relationships` | graph edge | `relationship_id` | Replayable DTDL relationship export |

### Enterprise Bronze

All enterprise Bronze records include `source_event_timestamp`, `ingestion_timestamp`, `source_simulation_id`, `source_record_key`, `schema_version`, `payload_hash`, `batch_id`, `generated_at_utc`, `generator_version`, `random_seed`, `record_source`, `data_classification`, and `is_synthetic`.

| Table | Grain | Key | Purpose |
|---|---|---|---|
| `bronze_organization` | headquarters/region | `org_unit_id` | Fictional corporate hierarchy |
| `bronze_route` | route | `route_id` | Fictional origin/destination/airline schedule |
| `bronze_aircraft_fleet` | aircraft instance | `aircraft_instance_id` | Synthetic tail token and fleet attributes |
| `bronze_work_team` | airport/discipline | `work_team_id` | Service and maintenance teams |
| `bronze_employee` | pseudonymous worker | `employee_id` | Role/discipline token; no identity fields |
| `bronze_employee_roster` | worker/day | `roster_assignment_id` | Shift, terminal, and gate coverage |
| `bronze_skill`, `bronze_shift`, `bronze_employee_skill` | skill/shift/worker-skill | business ID | Synthetic workforce capability assumptions |
| `bronze_customer` | pseudonymous customer profile | `customer_token` | No names/contact/loyalty identity |
| `bronze_passenger` | pseudonymous passenger | `passenger_token` | Segment and assistance flag only |
| `bronze_booking` | passenger/flight | `booking_id` | Booking channel, fare class, checked bags, revenue proxy |
| `bronze_baggage_journey` | checked bag | `bag_token` | Synthetic load/reclaim journey and exception |
| `bronze_baggage_scan` | bag scan | `baggage_scan_id` | Synthetic scan sequence/completeness |
| `bronze_boarding_event` | booking/flight | `boarding_event_id` | Synthetic boarding and window risk |
| `bronze_flight_leg` | flight leg | `leg_id` | Synthetic origin/destination/timestamps |
| `bronze_ramp_service_task` | flight/task | `ramp_task_id` | Synthetic ramp milestone task |
| `bronze_maintenance_work_order` | work order | `work_order_id` | Synthetic analytical work order |
| `bronze_recommendation_event` | airport/recommendation | `recommendation_id` | Advisory recommendation/approval status |
| `bronze_retail_outlet`, `bronze_retail_product` | outlet/product | business ID | Fictional commercial master data |
| `bronze_retail_pos` | outlet/hour | `pos_event_id` | Aggregate transactions, sales/refund proxies |
| `bronze_turnaround_phase` | flight/phase | `phase_event_id` | Five deterministic turnaround milestones |
| `bronze_customer_experience` | flight/segment | `cx_event_id` | Aggregate satisfaction and NPS proxy |
| `bronze_event_quality_cases` | test case | `test_case_id` | Isolated late/duplicate/malformed/out-of-order cases |

## Silver dimensions and bridges

| Table | Grain | Key / relationship |
|---|---|---|
| `dim_terminal` | terminal | `terminal_id` → `dim_airport.airport_id` |
| `dim_zone` | zone | `zone_id` → `dim_terminal.terminal_id` |
| `dim_checkpoint` | checkpoint | `checkpoint_id` → `dim_zone.zone_id` |
| `dim_stand` | stand | `stand_id` → `dim_gate.gate_id` |
| `dim_asset` | asset | `asset_id` → zone/gate/terminal/airport |
| `dim_location` | spatial entity | `location_id`; includes `spatial_ref`, `twin_id` |
| `dim_date` | configured date | `date_key` |
| `dim_time` | hour | `hour_key`; includes synthetic shift |
| `bridge_asset_location` | asset-location assignment | `asset_id`, `location_id`, effective dates |
| `bridge_gate_stand` | gate-stand assignment | `gate_id`, `stand_id`, current flag |

## Silver facts

| Table | Grain | Key | Important fields |
|---|---|---|---|
| `fact_asset_state` | asset / six-hour observation | `asset_state_id` | health, availability, anomaly, telemetry age |
| `fact_zone_occupancy` | checkpoint / 15-minute observation | `zone_occupancy_id` | occupancy, throughput, wait time |

Base facts gain additive `date_key` fields. Flight turnaround also gains `arrival_date_key` and `actual_departure_date_key` for role-playing date analysis.

### Enterprise Silver

- Dimensions: `dim_organization`, `dim_route`, `dim_aircraft_fleet`, `dim_work_team`, `dim_skill`, `dim_shift`, `dim_employee`, `dim_retail_outlet`, `dim_retail_product`, `dim_customer`, `dim_passenger`, `dim_customer_segment`.
- Bridges: `bridge_flight_route`, `bridge_employee_skill`.
- Facts: `fact_flight_leg`, `fact_employee_roster`, `fact_booking`, `fact_boarding_event`, `fact_baggage_journey`, `fact_baggage_scan`, `fact_ramp_service_task`, `fact_maintenance_work_order`, `fact_retail_pos`, `fact_turnaround_phase`, `fact_customer_experience`, `fact_recommendation`.
- Quarantine: `silver_quarantine_events` contains intentional test cases only.

## Gold

| Table | Grain | Purpose |
|---|---|---|
| `gold_airport_operational_health` | airport | Composite operational health and risk category |
| `gold_terminal_flow_summary` | terminal/hour | Occupancy, wait, throughput, flow status |
| `gold_gate_turnaround_performance` | gate/stand | Target adherence, on-time, utilization, reason |
| `gold_asset_reliability` | asset | Availability, anomalies, maintenance, latest state |
| `gold_energy_efficiency` | gate | Total and normalized energy |
| `gold_spatial_operational_status` | zone | Queue, occupancy, assets, spatial status |
| `gold_executive_scorecard` | airport | CEO-facing KPI row and exception commentary |
| `gold_it_service_health` | data product | Synthetic row-count, quality, run, freshness, control, capacity/cost proxies |
| `agent_context` | gate | Grounded advisory context and provenance |
| `gold_airline_route_performance` | airline/route | Punctuality, load, turnaround, booking, baggage, CX |
| `gold_baggage_performance` | origin/destination | Bags, exceptions per 1,000, journey time, demo SLA |
| `gold_workforce_coverage` | team/shift | Pseudonymous roster coverage and training exceptions |
| `gold_retail_performance` | outlet | Transactions and synthetic commercial proxies |
| `gold_customer_experience` | route/segment | Aggregate satisfaction and NPS proxy |
| `gold_turnaround_phase_performance` | gate/phase | Phase duration, delay count, milestone adherence |
| `gold_persona_scorecard` | airport/persona | Seven-persona primary/secondary KPI contract |
| `gold_data_agent_enterprise_context` | airport | Curated enterprise recommendation, provenance, freshness, confidence, approval |
| `gold_flight_operations_kpi` | airport/day | Flight, delay, turnaround, milestone, gate/stand KPIs |
| `gold_passenger_flow_kpi` | airport/day | Queue, throughput, congestion, boarding/connection risk |
| `gold_baggage_kpi` | airport/day | Processed bags, exceptions, delivery, transfer/scan risk |
| `gold_workforce_kpi` | airport/day | Planned/actual/overtime, roster/skill/task coverage |
| `gold_maintenance_kpi` | airport/day | Availability, MTBF/MTTR, compliance, backlog, failure risk |
| `gold_energy_sustainability_kpi` | airport/day | Energy intensity, peak, benchmark variance, emissions proxy |
| `gold_commercial_kpi` | airport/day | Revenue, conversion, transaction/outlet and benchmark proxies |
| `gold_incident_customer_kpi` | airport/day | Incidents, severity, resolution, CX, complaints, recommendation acceptance |
| `gold_kpi_catalog` | KPI | Formula, grain, unit, target, value type, caveat |

Notebook 09 also materializes the requested `gold_dim_*` and `gold_fact_*` star contracts by full replacement for the configured demo window. See [kpi-dictionary.md](kpi-dictionary.md) for formulas and caveats.

## KPI definitions

- **Operational risk score:** synthetic 0-100 composite of on-time gap, queue wait, maintenance anomalies, high open incidents, and asset availability gap. It is not a safety/security score.
- **Turnaround target adherence:** percentage of flights whose turnaround duration does not exceed the aircraft-type target.
- **Asset availability:** average deterministic availability observation for the asset.
- **Data quality pass:** 100 when actual row count equals the configured expected row count; 0 otherwise in this MVP.
- **Synthetic capacity / cost proxy:** deterministic walkthrough indicators only, not Fabric telemetry or currency.
- **Mishandled bags per 1,000:** mishandled synthetic bag journeys divided by checked bags, multiplied by 1,000.
- **Staffing coverage:** rostered pseudonymous workers divided by a deterministic two-workers-per-covered-gate demo target, capped at 100%.
- **Synthetic revenue:** ticket or POS values generated from deterministic distributions; not financial records.
- **Customer satisfaction / NPS proxy:** aggregate synthetic survey indicators with no respondent identity.
