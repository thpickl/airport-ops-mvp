# Warehouse to Ontology Mapping

This mapping is derived from notebooks `02`, `04`, `08`, and `09`, `warehouse/AirportOpsWarehouse_extended.sql`, `warehouse/01_enterprise_views.sql`, TMDL relationships, and the repository data dictionary. A missing view means the Delta table is modeled but is not directly exposed by the checked-in curated Warehouse SQL.

## Mapping conventions

- Domain classes describe airports, assets, events, observations, organizations, and other concepts.
- `*DimensionRecord`, `*FactRecord`, and `*BridgeRecord` classes describe relational rows.
- `ao:representsEntity` and `ao:representsEvent` link rows to domain instances.
- `ao:sourceTable`, `ao:sourceView`, `ao:warehouseGrain`, `ao:primaryKey`, and repeated `ao:foreignKey` annotations preserve the executable mapping.
- Source PK/FK uniqueness and referential integrity are validated by notebooks; representative RDF keys/cardinalities are validated by SHACL.

## Dimensions

The current generators overwrite dimensions and do not emit effective dates. They are current-state dimensions. Do not classify them as implemented SCD Type 2.

| Ontology record class | Delta table | Curated view | Grain | PK | Confirmed relationships |
|---|---|---|---|---|---|
| `AirportDimensionRecord` | `dim_airport` | `ops.vw_dim_airport` | airport | `airport_id` | Reference target for airport-bearing facts/dimensions |
| `TerminalDimensionRecord` | `dim_terminal` | `ops.vw_dim_terminal` | terminal | `terminal_id` | `airport_id` → airport |
| `ZoneDimensionRecord` | `dim_zone` | `ops.vw_dim_zone` | indoor zone | `zone_id` | `terminal_id` → terminal |
| `CheckpointDimensionRecord` | `dim_checkpoint` | `ops.vw_dim_checkpoint` | checkpoint | `checkpoint_id` | `zone_id` → zone; terminal/airport denormalized |
| `GateDimensionRecord` | `dim_gate` | `ops.vw_dim_gate` | gate | `gate_id` | airport and terminal assignments |
| `StandDimensionRecord` | `dim_stand` | `ops.vw_dim_stand` | stand | `stand_id` | `gate_id` → gate |
| `AssetDimensionRecord` | `dim_asset` | `ops.vw_dim_asset` | maintainable asset or meter | `asset_id` | zone/gate/terminal/airport columns; historical assignment via bridge |
| `LocationDimensionRecord` | `dim_location` | `ops.vw_dim_location` | physical/spatial location | `location_id` | polymorphic location row with spatial/twin references |
| `DateDimensionRecord` | `dim_date` | `ops.vw_dim_date` | calendar date | `date_key` | active and role-playing fact dates |
| `TimeDimensionRecord` | `dim_time` | `ops.vw_dim_time` | hour 0-23 | `hour_key` | event-hour and synthetic operating-period grouping |
| `AirlineDimensionRecord` | `dim_airline` | `ops.vw_dim_airline` | airline reference | `airline_id` | flight and route target |
| `AircraftTypeDimensionRecord` | `dim_aircraft` | `ops.vw_dim_aircraft` | aircraft type | `aircraft_type_id` | flight/fleet target; turnaround target attribute |
| `OrganizationDimensionRecord` | `dim_organization` | `ops.vw_dim_organization` | organization unit | `org_unit_id` | optional `parent_org_unit_id` hierarchy |
| `RouteDimensionRecord` | `dim_route` | `ops.vw_dim_route` | origin/destination/airline route | `route_id` | origin/destination airport; airline |
| `AircraftFleetDimensionRecord` | `dim_aircraft_fleet` | `ops.vw_dim_aircraft_fleet` | aircraft instance | `aircraft_instance_id` | aircraft type, airline, base airport |
| `WorkTeamDimensionRecord` | `dim_work_team` | `ops.vw_dim_work_team` | work team | `work_team_id` | airport assignment |
| `SkillDimensionRecord` | `dim_skill` | none | skill | `skill_id` | employee-skill bridge target |
| `ShiftDimensionRecord` | `dim_shift` | none | shift | `shift_id` | roster target |
| `EmployeeDimensionRecord` | `dim_employee` | `ops.vw_dim_employee` | pseudonymous workforce token | `employee_id` | work team and home airport |
| `RetailOutletDimensionRecord` | `dim_retail_outlet` | `ops.vw_dim_retail_outlet` | outlet | `outlet_id` | airport and terminal |
| `RetailProductDimensionRecord` | `dim_retail_product` | `ops.vw_dim_retail_product` | product | `product_id` | POS and inventory target |
| `CustomerDimensionRecord` | `dim_customer` | none | pseudonymous customer token | `customer_token` | passenger token and segment; restricted |
| `PassengerDimensionRecord` | `dim_passenger` | `ops.vw_dim_passenger` | pseudonymous passenger token | `passenger_token` | customer segment; restricted |
| `CustomerSegmentDimensionRecord` | `dim_customer_segment` | none | customer segment | `customer_segment_id` | aggregate CX grouping |

TMDL role-playing dates: `fact_flight_turnaround_events.date_key` is the active scheduled-departure relationship; `arrival_date_key` and `actual_departure_date_key` are inactive and require `USERELATIONSHIP` for alternate date analysis.

## Bridges and SCD semantics

| Ontology record class | Delta table | Grain | Key | Relationships | Implemented history |
|---|---|---|---|---|---|
| `AssetLocationBridgeRecord` | `bridge_asset_location` | asset/location assignment | `asset_id + location_id` | asset → `dim_asset`; location → `dim_location` | `effective_from`, nullable `effective_to`, `is_current`; current generator emits one open row per asset |
| `GateStandBridgeRecord` | `bridge_gate_stand` | gate/stand assignment | `gate_id + stand_id` | gate → `dim_gate`; stand → `dim_stand` | `effective_from`, `is_current`; no `effective_to` |
| `FlightRouteBridgeRecord` | `bridge_flight_route` | flight/route assignment | `flight_event_id` | route and aircraft instance | no effective dating |
| `EmployeeSkillBridgeRecord` | `bridge_employee_skill` | employee/skill capability | `employee_skill_id` | employee and skill | no effective dating |

`bridge_asset_location` is the only source contract that can represent closed historical assignments. `bridge_gate_stand` is partially effective-dated. The other bridges are current assignment/capability records.

## Facts

| Ontology record class | Delta table | Curated view | Grain / PK | Confirmed dimensions | Measures or outcomes |
|---|---|---|---|---|---|
| `FlightTurnaroundFactRecord` | `fact_flight_turnaround_events` | `ops.vw_fact_turnaround` | flight turnaround / `flight_event_id` | airport, gate, airline, aircraft type, date, hour | passengers, turnaround minutes, delay minutes, on-time flag, status |
| `PassengerQueueFactRecord` | `fact_passenger_queue_metrics` | `ops.vw_fact_passenger_flow` | checkpoint/15 min / `queue_metric_id` | airport, date, hour; legacy checkpoint text | queue length, wait minutes, throughput |
| `ZoneOccupancyFactRecord` | `fact_zone_occupancy` | `ops.vw_fact_zone_occupancy` | zone/checkpoint/15 min / `zone_occupancy_id` | airport, terminal, zone, checkpoint, date, hour | occupancy, throughput, wait minutes |
| `AssetStateFactRecord` | `fact_asset_state` | `ops.vw_fact_asset_state` | asset/6 hours / `asset_state_id` | asset, airport, terminal, zone, date, hour | health, availability, anomaly, telemetry age |
| `EnergyMeteringFactRecord` | `fact_energy_metering` | `ops.vw_fact_energy_metering` | meter reading / `meter_reading_id` | airport, gate, date, hour | kWh |
| `MaintenanceEventFactRecord` | `fact_maintenance_events` | `ops.vw_fact_maintenance_events` | maintenance event / `maintenance_id` | airport, gate, team, date, hour; asset type string | severity, anomaly, status |
| `OperationalIncidentFactRecord` | `fact_operational_incidents` | `ops.vw_incident_details` | incident / `incident_id` | airport, optional gate, date, hour | severity, delay minutes, status |
| `WeatherFactRecord` | `fact_weather` | `ops.vw_fact_weather` | airport snapshot / `weather_id` | airport, date, hour | temperature, wind, visibility, precipitation, condition |
| `FlightLegFactRecord` | `fact_flight_leg` | none | flight leg / `leg_id` | flight, route, origin/destination airports | scheduled/actual departure and arrival |
| `AircraftRotationFactRecord` | `fact_aircraft_rotation` | none | aircraft sequence/flight / `rotation_id` | aircraft instance, flight, previous flight | sequence, ground interval, overlap flag |
| `EmployeeRosterFactRecord` | `fact_employee_roster` | `ops.vw_fact_employee_roster` | worker/day / `roster_assignment_id` | employee, team, shift, airport, gate, date | planned, actual, overtime hours |
| `BookingFactRecord` | `fact_booking` | `ops.vw_fact_booking` | passenger/flight / `booking_id` | passenger token, flight, route, segment | ticket revenue proxy, checked bags, status |
| `BoardingEventFactRecord` | `fact_boarding_event` | none | booking/flight / `boarding_event_id` | booking, passenger token, flight, gate | boarding status and window risk |
| `BaggageJourneyFactRecord` | `fact_baggage_journey` | `ops.vw_fact_baggage_journey` | checked bag / `bag_token` | booking, flight, origin/destination airports | journey minutes, mishandled flag, expected scans |
| `BaggageScanFactRecord` | `fact_baggage_scan` | none | bag scan / `baggage_scan_id` | bag, flight | sequence, stage, timestamp |
| `RampServiceTaskFactRecord` | `fact_ramp_service_task` | none | flight/task / `ramp_task_id` | flight, airport, gate | sequence, duration, status |
| `MaintenanceWorkOrderFactRecord` | `fact_maintenance_work_order` | none | work order / `work_order_id` | maintenance event, airport, gate, team; asset type string | resolution hours, status, approval status |
| `AssetInspectionFactRecord` | `fact_asset_inspection` | none | inspection / `inspection_id` | asset, airport, gate | score, status, follow-up flag |
| `RetailTransactionFactRecord` | `fact_retail_pos` | `ops.vw_fact_retail_pos` | outlet/product/hour / `pos_event_id` | outlet, product, airport, terminal, date, hour | transaction count, gross/refund/basket proxies |
| `RetailInventoryFactRecord` | `fact_retail_inventory` | none | outlet/product snapshot / `inventory_snapshot_id` | outlet, product, airport, terminal | on-hand, reorder point, stock status |
| `TurnaroundPhaseFactRecord` | `fact_turnaround_phase` | `ops.vw_fact_turnaround_phase` | flight/phase / `phase_event_id` | flight, airport, gate, date | sequence, duration, milestone status |
| `CustomerExperienceFactRecord` | `fact_customer_experience` | `ops.vw_fact_customer_experience` | flight/segment / `cx_event_id` | flight, route, airport, segment, date | respondents, satisfaction, NPS proxy |
| `RecommendationFactRecord` | `fact_recommendation` | none | recommendation / `recommendation_id` | airport | type, text, status, approval/advisory flags |

Passenger, customer, booking, bag, and employee facts remain outside Data Agent grounding. Their ontology terms document source semantics; they do not grant agent access.

## Materialized Gold star contracts

Notebook `09_Enterprise_Silver_to_Gold` copies current conformed records to these requested star-contract names:

| Gold dimension | Source |
|---|---|
| `gold_dim_date`, `gold_dim_time`, `gold_dim_airport`, `gold_dim_terminal`, `gold_dim_zone`, `gold_dim_gate`, `gold_dim_stand` | matching base dimensions |
| `gold_dim_airline`, `gold_dim_aircraft_type`, `gold_dim_route` | airline, aircraft type, and route dimensions |
| `gold_dim_employee`, `gold_dim_team`, `gold_dim_asset`, `gold_dim_retail_outlet`, `gold_dim_customer_segment` | matching enterprise dimensions |

| Gold fact | Source |
|---|---|
| `gold_fact_flight`, `gold_fact_turnaround` | `fact_flight_turnaround_events` |
| `gold_fact_flight_rotation` | `fact_aircraft_rotation` |
| `gold_fact_turnaround_milestone` | `fact_turnaround_phase` |
| `gold_fact_passenger_flow` | `fact_zone_occupancy` |
| `gold_fact_queue` | `fact_passenger_queue_metrics` |
| `gold_fact_baggage` | `fact_baggage_journey` |
| `gold_fact_roster` | `fact_employee_roster` |
| `gold_fact_maintenance` | `fact_maintenance_work_order` |
| `gold_fact_asset_inspection` | `fact_asset_inspection` |
| `gold_fact_asset_state` | `fact_asset_state` |
| `gold_fact_energy` | `fact_energy_metering` |
| `gold_fact_retail_transaction` | `fact_retail_pos` |
| `gold_fact_retail_inventory` | `fact_retail_inventory` |
| `gold_fact_incident` | `fact_operational_incidents` |
| `gold_fact_customer_experience` | `fact_customer_experience` |
| `gold_fact_recommendation` | `fact_recommendation` |

These are full-replacement materializations for the configured demo window. They do not add new SCD semantics.

## Gold aggregates and measures

| Ontology class | Gold table | Curated view | Grain | Principal measures/outcomes |
|---|---|---|---|---|
| `AirportOperationalHealth` | `gold_airport_operational_health` | `ops.vw_airport_performance` | airport | OTD, turnaround, queue, availability, energy, incidents, risk |
| `TerminalFlowSummary` | `gold_terminal_flow_summary` | `ops.vw_terminal_performance` | airport/terminal/hour | occupancy, wait, throughput, checkpoint count, status |
| `GateTurnaroundPerformance` | `gold_gate_turnaround_performance` | `ops.vw_gate_turnaround_performance` | gate/stand | adherence, OTD, utilization, reason |
| `AssetReliability` | `gold_asset_reliability` | `ops.vw_asset_reliability` | asset | availability, anomalies, maintenance, latest state |
| `EnergyEfficiency` | `gold_energy_efficiency` | `ops.vw_energy_efficiency` | gate | total and normalized energy |
| `SpatialOperationalStatus` | `gold_spatial_operational_status` | `ops.vw_spatial_operational_context` | zone | queue, occupancy, asset status |
| `ExecutiveScorecard` | `gold_executive_scorecard` | `ops.vw_executive_scorecard` | airport | network operational scorecard |
| `ITServiceHealth` | `gold_it_service_health` | `ops.vw_it_service_health` | data product | quality, run, freshness, control, synthetic capacity/cost proxies |
| `AirlineRoutePerformance` | `gold_airline_route_performance` | `ops.vw_airline_route_performance` | airline/route | punctuality, load, turnaround, booking, baggage, CX |
| `BaggagePerformance` | `gold_baggage_performance` | `ops.vw_baggage_performance` | origin/destination | bags, exceptions/1,000, journey time, demo SLA |
| `WorkforceCoverage` | `gold_workforce_coverage` | `ops.vw_workforce_coverage` | team/shift | pseudonymous roster coverage and training exceptions |
| `RetailPerformance` | `gold_retail_performance` | `ops.vw_retail_performance` | outlet | transactions and synthetic commercial proxies |
| `CustomerExperience` | `gold_customer_experience` | `ops.vw_customer_experience` | route/segment | satisfaction and NPS proxy |
| `TurnaroundPhasePerformance` | `gold_turnaround_phase_performance` | `ops.vw_turnaround_phase_performance` | gate/phase | duration, delays, milestone adherence |
| `PersonaScorecard` | `gold_persona_scorecard` | `ops.vw_persona_scorecard` | airport/persona | persona KPI contract |
| `FlightOperationsKPI` | `gold_flight_operations_kpi` | `ops.vw_flight_operations_kpi` | airport/day | flights, delay, turnaround, milestones, gate/stand |
| `PassengerFlowKPI` | `gold_passenger_flow_kpi` | `ops.vw_passenger_flow_kpi` | airport/day | queue, throughput, congestion, boarding/connection risk |
| `BaggageKPI` | `gold_baggage_kpi` | `ops.vw_baggage_kpi` | airport/day | bags, exceptions, delivery, transfer/scan risk |
| `WorkforceKPI` | `gold_workforce_kpi` | `ops.vw_workforce_kpi` | airport/day | planned/actual/overtime, coverage, skill/task risk |
| `MaintenanceKPI` | `gold_maintenance_kpi` | `ops.vw_maintenance_kpi` | airport/day | availability, MTBF/MTTR, backlog, inspection score/compliance/follow-up |
| `EnergySustainabilityKPI` | `gold_energy_sustainability_kpi` | `ops.vw_energy_sustainability_kpi` | airport/day | intensity, peak, benchmark variance, emissions proxy |
| `CommercialKPI` | `gold_commercial_kpi` | `ops.vw_commercial_kpi` | airport/day | revenue/conversion/transaction/outlet proxies |
| `IncidentCustomerKPI` | `gold_incident_customer_kpi` | `ops.vw_incident_customer_kpi` | airport/day | incidents, severity, resolution, CX, complaints, recommendation acceptance |
| `AircraftRotationKPI` | `gold_aircraft_rotation_kpi` | `ops.vw_aircraft_rotation_kpi` | airport/day | rotations, ground interval, overlap/reserve indicators |
| `RetailInventoryKPI` | `gold_retail_inventory_kpi` | `ops.vw_retail_inventory_kpi` | airport/day | on-hand, reorder, stock status/stockout indicators |
| `KPICatalog` | `gold_kpi_catalog` | `ops.vw_kpi_catalog` | KPI | formula text, grain, unit, target, value type, caveat |

For semantic-model measures, `semantic-model/measures.dax` is authoritative. Gold SQL/table formulas are source-product implementations; KPI catalog formula strings are descriptive metadata.

## Relationship strength

- Exact-one OWL cardinalities are used only where source contracts require one parent/reference: terminal→airport, zone→terminal, checkpoint→zone, gate→terminal, stand→gate, route→origin/destination/airline, and flight→gate/aircraft type/airline/route/turnaround.
- Optional relational foreign keys remain optional in OWL. For example, incident gate and several asset location columns are not strengthened.
- Fact-to-dimension joins are represented as record metadata and generic `hasDimensionMember`; representative instance data does not fabricate all 78 table mappings as rows.
- DTDL inverses are explicit in OWL even when DTDL stores only the forward edge.

## Unresolved gaps

1. No source table declares database-enforced PK/FK constraints; notebook validation is authoritative for uniqueness and referential integrity.
2. The source does not define a surrogate-key strategy separate from business IDs for these generated dimensions.
3. No complete SCD Type 2 history is generated. Only the asset-location bridge has both effective start and optional end.
4. Maintenance events and work orders use `asset_type` in some paths rather than a mandatory `asset_id`; the ontology does not invent a one-asset link for those rows.
5. The five turnaround phase names have no dimension table or controlled hierarchy.
6. Shift linkage across base service teams and time periods is a string convention, not a key-backed relationship.
7. The source has no native RDF persistence, named-graph policy, graph ACL model, or SPARQL service deployment contract.