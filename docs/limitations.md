# Assumptions and Limitations

- Airport identity and point coordinates are sourced public reference facts; all operational records, relationships, layouts, incidents, costs, and capacity indicators are synthetic and deterministic from seed `39039`.
- The default configured window is 30 synthetic days from `2026-01-01T00:00:00Z`. “Current” is relative to the recorded fixed clock, never wall-clock time.
- GeoJSON airport points are public anchors. All region polygons, terminals, zones, gates, stands, routes, flows, incidents, assets, and energy layers are illustrative synthetic geometry and do not represent boundaries, indoor navigation, security areas, evacuation routes, or restricted areas.
- GeoJSON is packaged into PBIR Azure Maps visuals. No Azure Maps account or customer endpoint is stored.
- Azure Digital Twins deployment is optional through notebook 14 and requires a separately governed runtime endpoint and identity.
- Fabric MCP is not connected in this development session, so no live deployment was attempted. Notebooks `00`, `10`, and `11` automate supported target operations.
- The checked-in sample twin graph is illustrative; notebook `04` produces the configurable synthetic physical graph around all selected reference anchors.
- A `.pbix` is not generated. Source-controlled TMDL and PBIR projects are provided; target definition support and lineage binding are capability-dependent.
- Warehouse cross-database references require the Lakehouse and Warehouse to be in the same supported workspace configuration; a materialization fallback is documented.
- The risk score, data-quality result, synthetic capacity, synthetic cost, and security-control status are walkthrough indicators, not production telemetry or assurance.
- Recommendations are advisory. There is no autonomous control, no safety-of-flight function, and no command path to ATC, A-SMGCS, AODB, BHS, BMS, aircraft, equipment, or staff.
- No real PII, biometrics, source passenger/workforce identity, credentials, tenant IDs, secrets, or customer operational endpoints are present. Pseudonymous synthetic tokens are excluded from Data Agent grounding.
- Fabric Data Agent and Fabric app item-definition support can vary by target. Source packages are `IMPLEMENTED`; unverified tenant deployment is `BLOCKED` and rejected capability is `UNSUPPORTED`.
- No verified native Rayfin item/API is assumed; Rayfin is implemented as a configurable app module.
