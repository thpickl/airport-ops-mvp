# CIO Thin Report

**Persistent banner:** `Synthetic platform indicators - not tenant telemetry or billing data`.

## Page 1: Data Product Health

| Visual | Mapping |
|---|---|
| KPI cards | Data Quality Pass %, Failed Data Products, Late Records, Quarantined Records, Current Grounding Context % |
| Product status matrix | Rows: `data_product`; Columns: `layer`; Values: actual/expected rows, pipeline status, refresh status |
| Freshness timeline | Axis: observation timestamp; Legend: data product; Value: Data Quality Pass % |
| Control status table | data product, security control status, refresh status, source table |

**Tooltip:** expected/actual rows, observation timestamp, synthetic flag.

**Drill-through:** `Data Product Detail`, keyed by `data_product`.

## Page 2: Synthetic Usage and Reliability

| Visual | Mapping |
|---|---|
| KPI cards | Synthetic Capacity Usage %, Synthetic Cost Proxy Units, Latest Data Product Observation |
| Usage proxy bar | Axis: data product; Values: synthetic capacity %, synthetic cost proxy units |
| Service exceptions | product, pipeline status, refresh status, data quality %, late/quarantined counts |

All cost and capacity visuals must include `Synthetic proxy` in their titles. No real Fabric capacity, compliance posture, spend, or security assertion is represented.
