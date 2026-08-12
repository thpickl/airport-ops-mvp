# Governed Semantic Foundation

> **Synthetic demonstration data.** This model contains no real airport, passenger,
> workforce, security, cost, or capacity data. Recommendations are advisory.

The source-controlled TMDL project at `AirportOpsSharedModel.SemanticModel`
defines the shared semantic foundation over `AirportOpsWarehouse.ops` views.
Notebook `10_Deploy_Platform_Artifacts` replaces runtime Warehouse parameters
and submits the definition through supported Fabric item APIs. The PBIR report
project is generated from `reports/generate_pbir.py` and deployed after the model.

## Source aliases

Import each Warehouse view and rename it to the model table shown.

| Warehouse view | Model table | Grain |
|---|---|---|
| `ops.vw_dim_airport` | `dim_airport` | airport |
| `ops.vw_dim_terminal` | `dim_terminal` | terminal |
| `ops.vw_dim_zone` | `dim_zone` | zone |
| `ops.vw_dim_checkpoint` | `dim_checkpoint` | checkpoint |
| `ops.vw_dim_gate` | `dim_gate` | gate |
| `ops.vw_dim_stand` | `dim_stand` | stand |
| `ops.vw_dim_asset` | `dim_asset` | asset |
| `ops.vw_dim_location` | `dim_location` | location |
| `ops.vw_dim_date` | `dim_date` | date |
| `ops.vw_dim_time` | `dim_time` | hour |
| `ops.vw_fact_turnaround` | `fact_flight_turnaround_events` | flight turnaround |
| `ops.vw_fact_passenger_flow` | `fact_passenger_queue_metrics` | checkpoint interval |
| `ops.vw_fact_asset_state` | `fact_asset_state` | asset observation |
| `ops.vw_fact_zone_occupancy` | `fact_zone_occupancy` | zone/checkpoint interval |
| `ops.vw_fact_energy_metering` | `fact_energy_metering` | meter reading |
| `ops.vw_fact_maintenance_events` | `fact_maintenance_events` | maintenance event |
| `ops.vw_incident_details` | `fact_operational_incidents` | incident |
| `ops.vw_executive_scorecard` | `gold_executive_scorecard` | airport |
| `ops.vw_terminal_performance` | `gold_terminal_flow_summary` | terminal/hour |
| `ops.vw_gate_turnaround_performance` | `gold_gate_turnaround_performance` | gate/stand |
| `ops.vw_asset_reliability` | `gold_asset_reliability` | asset |
| `ops.vw_energy_efficiency` | `gold_energy_efficiency` | gate |
| `ops.vw_it_service_health` | `gold_it_service_health` | data product |
| `ops.vw_spatial_operational_context` | `gold_spatial_operational_status` | zone |
| `ops.vw_data_agent_grounding` | `agent_context` | gate |

Retain the original MVP tables `gold_kpi_daily_summary`,
`gold_turnaround_by_hour`, `gold_queue_by_hour`, `gold_gate_utilization`, and
`gold_energy_summary` in the model for backward-compatible report measures.

## Relationships

All relationships are single-direction from the `1` side to the `*` side.
Do not enable bidirectional filtering.

| One side | Many side | Active | Purpose |
|---|---|---:|---|
| `dim_airport[airport_id]` | `dim_terminal[airport_id]` | Yes | physical hierarchy |
| `dim_airport[airport_id]` | `dim_gate[airport_id]` | Yes | gate hierarchy |
| `dim_terminal[terminal_id]` | `dim_zone[terminal_id]` | Yes | indoor hierarchy |
| `dim_zone[zone_id]` | `dim_checkpoint[zone_id]` | Yes | checkpoint hierarchy |
| `dim_zone[zone_id]` | `dim_asset[zone_id]` | Yes | asset hierarchy |
| `dim_gate[gate_id]` | `dim_stand[gate_id]` | Yes | stand adjacency |
| `dim_gate[gate_id]` | `fact_flight_turnaround_events[gate_id]` | Yes | turnaround analysis |
| `dim_gate[gate_id]` | `fact_energy_metering[gate_id]` | Yes | gate energy |
| `dim_gate[gate_id]` | `fact_maintenance_events[gate_id]` | Yes | maintenance |
| `dim_gate[gate_id]` | `fact_operational_incidents[gate_id]` | Yes | incidents |
| `dim_asset[asset_id]` | `fact_asset_state[asset_id]` | Yes | telemetry |
| `dim_checkpoint[checkpoint_code]` | `fact_passenger_queue_metrics[checkpoint]` | Yes | legacy queue observations |
| `dim_checkpoint[checkpoint_id]` | `fact_zone_occupancy[checkpoint_id]` | Yes | conformed flow observations |
| `dim_airport[airport_id]` | `gold_executive_scorecard[airport_id]` | Yes | CEO scorecard |
| `dim_terminal[terminal_id]` | `gold_terminal_flow_summary[terminal_id]` | Yes | terminal flow |
| `dim_gate[gate_id]` | `gold_gate_turnaround_performance[gate_id]` | Yes | gate scorecard |
| `dim_asset[asset_id]` | `gold_asset_reliability[asset_id]` | Yes | reliability |
| `dim_gate[gate_id]` | `gold_energy_efficiency[gate_id]` | Yes | efficiency |
| `dim_zone[zone_id]` | `gold_spatial_operational_status[zone_id]` | Yes | map/status |
| `dim_gate[gate_id]` | `agent_context[gate_id]` | Yes | grounding; only active agent relation |
| `dim_date[date_key]` | `fact_flight_turnaround_events[date_key]` | Yes | scheduled departure date |
| `dim_date[date_key]` | `fact_flight_turnaround_events[arrival_date_key]` | No | scheduled arrival role |
| `dim_date[date_key]` | `fact_flight_turnaround_events[actual_departure_date_key]` | No | actual departure role |
| `dim_date[date_key]` | each other Silver fact `[date_key]` | Yes | event date |
| `dim_time[hour_key]` | each hourly fact/Gold `[event_hour]` | Yes | hour and shift |

The inactive date roles are activated in measures with `USERELATIONSHIP` when a
future multi-day demo needs arrival-date or actual-departure-date analysis.

## Metadata and hiding

- Mark `dim_date[calendar_date]` as the date table; sort `month_name` by
  `month_number` and `hour_label` by `hour_key`.
- Display hierarchy: Airport → Terminal → Zone → Checkpoint. Separate hierarchy:
  Airport → Gate → Stand.
- Hide all surrogate/business join columns, `is_synthetic`, `twin_id`,
  `map_feature_id`, `source_table_references`, raw latitude/longitude, and fact IDs.
  Keep them available for drill-through and provenance.
- Business-friendly names: `airport_name` → Airport, `terminal_name` → Terminal,
  `zone_name` → Zone, `gate_id` → Gate, `asset_name` → Asset.
- Put measures in display folders: `Executive`, `Operations`, `Passenger Flow`,
  `Reliability`, `Energy`, `IT Health`, and `Agent Grounding`.

## Formats and descriptions

| Measure group | Format string | Description rule |
|---|---|---|
| Rates / utilization / availability / adherence | `0.0%` if DAX returns 0-1; `0.0\%` for stored 0-100 values | State numerator, denominator, and threshold |
| Minutes | `0.0` | Always label `(min)` |
| Energy | `0.0 kWh` or `0.000 kWh` per passenger | Clearly separate per-flight and per-passenger |
| Counts | `#,0` | Distinct entity vs event count must be explicit |
| Risk score | `0.0` | Synthetic 0-100 composite, not a safety score |
| Cost/capacity proxy | `0.0` | Include `Synthetic` in display name and description |
| Observation timestamp | `yyyy-mm-dd hh:mm` | Fixed demo observation time, not wall-clock freshness |

Add measures from `measures.dax`. Perspective membership and report mappings are
defined in `perspectives.md` and `report-specifications/`.

## Deployment and validation

1. Run the ordered data graph through notebook `11_Orchestrate_Deployment`.
2. Run `reports/generate_pbir.py` and `tests/validate_platform.py` before import.
3. Supply the runtime Warehouse endpoint/database to notebook `10` and deploy
   the TMDL model followed by the PBIR report.
4. Validate the Airport, Airline, Executive, Operations, Maintenance,
   Commercial, and IT perspectives/pages.
5. Run `validation-queries.sql`, Warehouse KPI checks, and notebook `12`.

Target rejection of a TMDL/PBIR definition is a deployment failure, not an
implicit request to fabricate a `.pbix`. Use the same projects through supported
Fabric Git/PBIP import when item-definition behavior differs in the target.
