# Assumptions

- Public airport names, IATA/ICAO codes, approximate WGS84 points, elevation, and time zones come from the checked-in, attributed snapshot. They are geographic anchors only.
- The fictional organization does not own or operate the 18 airports. Every portfolio relationship, facility, layout, airline, operation, person, transaction, incident, KPI, forecast, recommendation, and outcome is synthetic.
- Seed `39039`, fixed start `2026-01-01T00:00:00Z`, generator version `4.0.0`, canonical configuration, and the 2026-08-08 reference snapshot define reproducibility.
- The default operating window is 30 days under the `smoke` profile; `unit`, `demo`, and `enterprise` are versioned alternatives.
- Passenger and worker records use deterministic pseudonymous tokens without source identity. Data Agent grounding excludes passenger-, booking-, bag-, and worker-level sources.
- Revenue, cost, capacity, NPS, ticket, and retail values are demonstration proxies, not financial or telemetry records.
- All WGS84 coordinates and geometry are illustrative and do not represent real airports, terminals, restricted areas, security boundaries, or navigation paths.
- The target Fabric workspace and capacity already exist. Workspace lifecycle is not automated to avoid cross-domain destructive behavior.
- Warehouse SQL and KQL execution require runtime endpoints supplied to notebook 10. They are not stored in source.
- Semantic model/report deployment depends on target support for TMDL/PBIR item definitions.
- Data Agent and Fabric app item-definition support is capability-checked. A blocked or unsupported path is not success.
- No documented native Rayfin artifact/API is assumed; Rayfin is the configurable app module in `fabric-app/rayfin-module.json`.
- Azure Digital Twins deployment is optional, separately governed, and uses a runtime endpoint. Source artifacts remain portable without deployment.
- The system has no action tools and no control path to operational or safety-critical systems.
- The `infra/` Terraform layer uses the verified `microsoft/fabric` provider (`~> 1.12`, checked against `1.12.1`) and only workspace, lakehouse, warehouse, eventhouse, and KQL database resources. It provisions the workspace and core items; the notebook/REST path deploys definitions and runs SQL/KQL. Both are alternative, complementary paths.
- `reference_mode` selects `public_reference` (default, sourced public anchors) or `fictional` (fully synthetic anchors) when public data cannot be redistributed.
