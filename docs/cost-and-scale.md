# Cost and Scale Considerations

## Default scale

The default 24-hour run creates 450 flights, 5,760 queue observations, 8,640 energy readings, 720 pseudonymous workers, 2,250 turnaround phases, and passenger/baggage facts driven by aircraft capacity and load. Exact deterministic row counts are validated where configuration determines them directly.

## Scale factor

`scale_factor` increases fictional fleet/workforce/retail volumes while preserving deterministic behavior for the same complete configuration. Catalog counts remain fixed at 15/20/16. Changing the scale factor intentionally changes fingerprint baselines.

## Fabric cost drivers

- Spark session startup and large passenger/bag/scan DataFrames.
- Delta writes and repeated full-replacement validation runs.
- DirectQuery/Warehouse query frequency from the semantic model.
- Eventhouse ingestion, retention (30 days), hot cache (3 days), and materialized views.
- Power BI/Fabric capacity and refresh concurrency.

No repository value estimates a real Fabric bill. `synthetic_capacity_usage_pct`, `synthetic_cost_proxy_units`, revenue, and emissions are scenario indicators only.

## Recommendation

Use scale 1 for stakeholder demos. Validate adoption before increasing passenger/baggage volume. For larger tests, partition operational facts by date/airport, switch supported tables to deterministic MERGE/replace-where, monitor capacity with real governed telemetry outside this synthetic model, and reset idempotency baselines only for intentional configuration changes.
