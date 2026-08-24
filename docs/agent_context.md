# `agent_context` - Extended Data Agent Grounding Contract

> This is a **synthetic, advisory** grounding surface. The published Data Agent has
> no action tools and no write path. Notebook `03` creates the legacy five-column
> table; notebook `05` replaces it with a backward-compatible superset at the same
> one-row-per-gate grain. Consequential recommendations require human approval.

## Purpose

The table joins gate performance, terminal flow, asset reliability, incidents,
and spatial references into a decision-oriented context with explicit freshness,
confidence, rationale, provenance, and approval fields.

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `airport_id` | string | Synthetic portfolio key for a public anchor (for example, `SYN-AP-CDG`) |
| `gate_id` | string | Synthetic gate identifier (for example, `SYN-GAT-CDG-01`) |
| `operational_status` | string | `Normal` / `Watch` / `Action` (derived from worst departure delay at the gate) |
| `delay_reason` | string | Dominant delay reason for the gate, else `None` |
| `recommended_action` | string | Advisory review/inspection action |
| `terminal_id`, `zone_id`, `stand_id`, `asset_id` | string | Physical context keys |
| KPI fields | numeric | On-time, turnaround, target adherence, utilization, queue wait, asset availability/anomalies |
| `relevant_incident_id`, `relevant_incident_category` | string | Highest-ranked gate incident when present |
| `spatial_location_id`, `spatial_ref` | string | `dim_location` and GeoJSON reference |
| `observation_timestamp` | timestamp | Fixed configured demo timestamp |
| `recommendation_rationale` | string | Evidence-based explanation |
| `severity`, `confidence_category` | string | Advisory classification |
| `source_table_references` | string | Curated provenance list |
| `human_approval_required` | boolean | True for consequential recommendations |
| `data_freshness_indicator` | string | Relative to fixed observation time |
| `advisory_only`, `is_synthetic` | boolean | Mandatory safety/scope flags |

## Status logic (MVP heuristic)

| Max departure delay at gate | Status | Recommended action |
|-----------------------------|--------|--------------------|
| > 30 min | `Action` | Escalate to duty manager; reassign ground crew |
| 16–30 min | `Watch` | Monitor turnaround; pre-stage baggage team |
| ≤ 15 min | `Normal` | No action required |

## Compatibility

The original columns (`airport_id`, `gate_id`, `operational_status`,
`delay_reason`, `recommended_action`) are unchanged. Existing consumers need no
migration. New consumers should prefer `ops.vw_data_agent_grounding`.

## How the Data Agent uses this

1. **Ground** only on curated Gold / Warehouse views per
   `ontology/data-agent-instructions.md`.
2. **Answer** synthetic operational questions ("which synthetic gates need attention at the CDG reference anchor in the configured demo window?").
3. **Recommend** with provenance, confidence, fixed as-of time, and explicit
   human approval. The agent must not execute the action.

No autonomous safety-critical or airport-equipment action is permitted.
