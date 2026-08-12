# IT Professional Thin Report

**Persistent banner:** `Synthetic diagnostics - no production telemetry`.

## Page 1: Pipeline and Table Health

| Visual | Mapping |
|---|---|
| KPI cards | Data Quality Pass %, Failed Data Products, Late Records, Quarantined Records |
| Product run table | product, layer, source table, expected/actual rows, run status, refresh status |
| Schema/quality exceptions | validation check, status, details (from `validation_results` if added to the model) |
| Freshness card | Latest Data Product Observation |

**Tooltip:** product, layer, source table, observation timestamp, synthetic flag.

**Drill-through:** `Data Product Troubleshooting`, keyed by `data_product`.

## Page 2: Telemetry and Incident Troubleshooting

| Visual | Mapping |
|---|---|
| KPI cards | Asset Availability %, Anomalous Assets, Current Grounding Context % |
| Telemetry freshness table | asset, event time, health status, telemetry age, terminal, zone, gate |
| Incident table | incident ID, airport, gate, category, severity, status, delay minutes |
| Agent lineage table | gate, source table references, spatial reference, freshness, confidence, approval required |

**Drill-through:** `Asset Telemetry Detail` keyed by `asset_id`; `Incident Detail` keyed by `incident_id`; `Agent Grounding Detail` keyed by `gate_id`.

## Page 3: Agent Grounding Detail

Show all `agent_context` provenance, KPI, recommendation, rationale, severity, confidence, freshness, advisory, and human-approval fields. Technical source IDs may be visible only on this troubleshooting page. Never expose or imply an autonomous actuation control.
