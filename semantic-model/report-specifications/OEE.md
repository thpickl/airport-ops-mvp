# Operational Excellence Executive Thin Report

OEE means **Operational Excellence Executive**. This report does not calculate manufacturing OEE.

**Persistent banner:** `Synthetic operations - advisory only`.

## Page 1: Turnaround and Gate Performance

| Visual | Mapping |
|---|---|
| KPI cards | Turnaround Target Adherence %, Avg Turnaround (min), On-Time Departure %, Gate Utilization % |
| Gate/stand matrix | Rows: Airport → Terminal → Gate → Stand; Values: adherence %, turnaround, utilization %, max delay |
| Hour/shift comparison | Axis: Shift then Hour; Values: Turnaround by Hour, On-Time Departure % |
| Delay root-cause bar | Axis: primary delay reason; Value: Total Flights; small multiple: Airport |

**Tooltip:** flights, target, actual turnaround, max delay, reason, stand.

**Drill-through:** `Gate Root Cause`, keyed by `gate_id`.

## Page 2: Passenger Flow

| Visual | Mapping |
|---|---|
| KPI cards | Passenger Throughput, Avg Queue Wait (min), Peak Queue Wait (min) |
| Queue trend | Axis: Hour; Legend: Checkpoint; Values: avg and peak wait |
| Terminal bottleneck heatmap | Rows: Terminal/Zone; Columns: Hour; Value: avg occupancy; conditional color by flow status |
| Spatial status table/map | spatial reference, terminal, zone, status, peak wait, anomalous asset count |

**Drill-through:** `Terminal Flow Detail`, keyed by `terminal_id`.

## Page 3: Reliability and Energy

| Visual | Mapping |
|---|---|
| KPI cards | Asset Availability %, Anomalous Assets, Open Maintenance Items, Energy per Flight (kWh), Energy per Passenger (kWh) |
| Reliability bar | Axis: asset type; Values: availability %, anomaly count; legend: reliability status |
| Energy comparison | Axis: Airport → Gate; Values: energy per flight/passenger |
| Exception table | asset, criticality, latest health, maintenance anomalies, latest telemetry timestamp |

**Drill-through:** `Asset Reliability Detail`, keyed by `asset_id`.
