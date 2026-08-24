# Cost and Scale Considerations

## Default scale

The default `smoke` profile simulates 30 days across 18 airports and produces 166,077 logical source records: 4,320 flight operations, 17,280 queue observations, 17,280 passenger journeys, 17,280 baggage journeys, 25,920 turnaround milestones, 66,333 retail transactions, 6,480 asset telemetry rows, 4,320 energy observations, 4,320 customer feedback rows, 540 maintenance work orders, and 216 pseudonymous employees. These counts are deterministic for the committed configuration and are asserted by the portable test suite.

## Scale factor

`scale_factor` increases fictional fleet/workforce/retail volumes while preserving deterministic behavior for the same complete configuration. Catalog counts remain fixed at 18 airports, 20 airlines, and 16 aircraft types. Changing the scale factor intentionally changes fingerprint baselines.

## Fabric cost drivers

- Spark session startup and large passenger/bag/scan DataFrames.
- Delta writes and repeated full-replacement validation runs.
- DirectQuery/Warehouse query frequency from the semantic model.
- Eventhouse ingestion, retention (30 days), hot cache (3 days), and materialized views.
- Power BI/Fabric capacity and refresh concurrency.

No repository value estimates a real Fabric bill. `synthetic_capacity_usage_pct`, `synthetic_cost_proxy_units`, revenue, and emissions are scenario indicators only.

## Recommendation

Use the `smoke` profile for stakeholder demos. Validate adoption before increasing passenger/baggage volume with `demo` or `enterprise`. For larger tests, partition operational facts by date/airport, switch supported tables to deterministic MERGE/replace-where, monitor capacity with real governed telemetry outside this synthetic model, and reset idempotency baselines only for intentional configuration changes.
