# DTDL to Fabric Mapping

All identifiers are deterministic and synthetic. DTDL twin IDs use `<kind>:<business-key>` while Fabric and GeoJSON retain the business key itself.

| DTDL interface | Business key | Silver source | Gold/serving use |
|---|---|---|---|
| Airport | `airport_id` | `dim_airport` | `gold_airport_operational_health`, `gold_executive_scorecard` |
| Terminal | `terminal_id` | `dim_terminal` | `gold_terminal_flow_summary` |
| Zone | `zone_id` | `dim_zone`, `dim_location` | `gold_spatial_operational_status` |
| Checkpoint | `checkpoint_id` | `dim_checkpoint` | `gold_terminal_flow_summary` via `fact_zone_occupancy` |
| Gate | `gate_id` | `dim_gate` | `gold_gate_turnaround_performance`, `agent_context` |
| Stand | `stand_id` | `dim_stand`, `bridge_gate_stand` | `gold_gate_turnaround_performance` |
| Asset / MaintenanceAsset | `asset_id` | `dim_asset`, `bridge_asset_location` | `gold_asset_reliability`, `agent_context` |
| EnergyMeter | `asset_id` | `dim_asset` where `asset_class='EnergyMeter'` | `gold_energy_efficiency` through gate energy facts |

## Graph lineage

- `bronze_twin_relationships` preserves the generated graph edge list.
- `dim_*` and `bridge_*` tables are the conformed relational representation.
- GeoJSON `properties` carry the same business keys and `twin_id` values.
- `agent_context.spatial_ref` and `source_table_references` provide grounding provenance.
