# Implementation Status

Status values are `IMPLEMENTED`, `VALIDATED`, `DEPLOYED`, `BLOCKED`, or `UNSUPPORTED`. This file describes source and validation state as of 2026-08-09; runtime deployment evidence remains authoritative.

| Capability | Status | Evidence or blocker |
|---|---|---|
| Deterministic ID and checksum library | VALIDATED | Local ordering and UUIDv5 invariants pass |
| 18-airport public reference snapshot | VALIDATED | OurAirports records retrieved; IANA zones recorded with field provenance |
| Unit/smoke/demo/enterprise configuration | VALIDATED | Parameterized JSON profiles; smoke default, seed 42 |
| Event simulation and KPI outcomes | VALIDATED | 18-airport smoke outcomes and two-run checksums pass |
| Bronze/Silver/Gold local transformations | VALIDATED | Duplicate, late, correction, malformed, quarantine, lineage, and rerun tests pass |
| Fabric medallion notebooks | DEPLOYED | All 18 definitions are deployed; Spark catalog validation confirms 29 enterprise Bronze, 30 enterprise Silver, and 65 Gold products, including 18-row agent context and 126-row persona scorecard |
| Eventhouse KQL | DEPLOYED | 14 tables, 13 functions, and 6 materialized views deployed and retrieved |
| Warehouse SQL | DEPLOYED | 77 `ops` views, 13 least-privilege roles, and empty-by-default persona scope deployed; queries return 18 agent rows, 126 persona rows, and 864 employees |
| TMDL semantic model | DEPLOYED | Definition retrieved with runtime Warehouse binding and no placeholders; DAX query returns 18 airports, 126 persona rows, and 18 agent rows |
| PBIR reports | DEPLOYED | Report retrieved with 25 pages, 12 GeoJSON resources, and a Power BI dataset binding to the deployed shared model |
| GeoJSON package | VALIDATED | 12 layers, 688 unique features, coordinate ranges, closure, and PBIR packaging pass |
| Fabric app source project | VALIDATED | 11 audience navigation targets and safety notices resolve locally; target API rejects native `FabricApp` as an invalid item type |
| Native Fabric app item | UNSUPPORTED | Target returned `InvalidItemType` for `FabricApp`; no native app item was created |
| Rayfin native Fabric artifact | UNSUPPORTED | No verified Microsoft Fabric item type or deployment API found |
| Rayfin app fallback | VALIDATED | Configurable advisory module with evidence, confidence, warnings, and decision audit contract |
| Portable digital twin | VALIDATED | 15 DTDL v2 models, complete sample graph, and optional adapter pass local checks |
| Graph ontology | VALIDATED | Portable definitions, Gold nodes/edges, and governed source mappings pass local checks |
| Fabric Data Agent | DEPLOYED | Native item published with exactly two sources: 29 selected Warehouse `ops` views and 13 selected KQL functions/views; zero raw KQL tables or extra sources |
| Terraform infrastructure (`infra/`) | DEPLOYED | Apply created the workspace, Lakehouse, Warehouse, Eventhouse, and read/write KQL database; Fabric REST retrieval and no-change second plan passed |
| Fictional reference mode | VALIDATED | Deterministic 18-anchor fictional snapshot; distinct from public mode and rerun-stable |
| Fabric workspace deployment | DEPLOYED | Workspace exists on the approved existing capacity; optional system-assigned workspace identity was disabled after target capability failure |
| Post-deployment retrieval validation | VALIDATED | Fabric REST retrieved the workspace and all Terraform-managed core items; second Terraform plan reported no changes |
| Azure Digital Twins runtime | BLOCKED | Active subscription contains no Azure Digital Twins instance; resource group, region, lifecycle owner, RBAC, and endpoint are intentionally not invented |

## Deployment truth

Terraform infrastructure and supported Fabric content were deployed and independently retrieved or queried. Native Fabric app deployment is unsupported by this target. Azure Digital Twins deployment is blocked pending an approved instance and runtime endpoint; only the portable package is reported as validated.

## Local validation evidence

- Command: `python tests/validate_platform.py`
- Result: 19 tests, 0 failures, 0 errors
- Smoke logical records: 166,077
- Smoke checksum: `3bd939205079a861923b4e6abb1adac37ed3e2153c489a37b1eb3563f9dcd405`
- Simulated turnaround: 48.1534 to 39.1071 minutes
- Baseline missed preferred boarding-window rate: 34.87%
- P95 queue-wait reduction: 37.86%
- Revenue-per-passenger increase: 22.20%
- Regulatory automation coverage: 79.41%
- Energy-per-passenger efficiency improvement: 14.33%