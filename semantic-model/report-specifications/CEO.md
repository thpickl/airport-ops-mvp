# CEO Thin Report

**Persistent banner:** `Synthetic demonstration - advisory only`

**Default filters:** configured demo date; all airports.

## Page 1: Network Health

| Visual | Mapping |
|---|---|
| KPI cards | On-Time Departure %, Avg Turnaround (min), Avg Queue Wait (min), Operational Risk Score, Energy per Flight (kWh) |
| Airport comparison bar | Axis: `dim_airport[airport_name]`; Value: Operational Risk Score; color: `risk_category` |
| Health matrix | Rows: Airport; Values: On-Time Departure %, Asset Availability %, Incident Count, Open High-Severity Incidents |
| Exception commentary table | Airport, `executive_commentary`, `risk_category`, `observation_timestamp` |

**Tooltip:** airport name, on-time %, turnaround, queue wait, asset availability, observation timestamp.

**Drill-through:** `Airport Executive Detail`, keyed by `airport_id`.

## Page 2: Airport Executive Detail

| Visual | Mapping |
|---|---|
| KPI cards | On-Time Departure %, Avg Turnaround (min), Energy per Passenger (kWh), Recommendations Requiring Approval |
| Hourly trend | Axis: `dim_time[hour_label]`; Values: Turnaround by Hour, Queue Wait by Hour |
| Exception table | Gate, operational status, severity, rationale, recommended action, human approval required |

Recommendations are phrased as review/approval actions, never automated operating commands.
