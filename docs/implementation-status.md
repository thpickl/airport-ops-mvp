# Implementation Status

Status values are `IMPLEMENTED`, `VALIDATED`, `DEPLOYED`, `BLOCKED`, or `UNSUPPORTED`. This file describes source and validation state as of 2026-08-24; runtime deployment evidence remains authoritative.

| Capability | Status | Evidence or blocker |
|---|---|---|
| Deterministic ID and checksum library | VALIDATED | Local ordering and UUIDv5 invariants pass |
| 18-airport public reference snapshot | VALIDATED | OurAirports records retrieved; IANA zones recorded with field provenance |
| Unit/smoke/demo/enterprise configuration | VALIDATED | Parameterized JSON profiles; smoke default, seed 42 |
| Event simulation and KPI outcomes | VALIDATED | 18-airport smoke outcomes and two-run checksums pass |
| Bronze/Silver/Gold local transformations | VALIDATED | Duplicate, late, correction, malformed, quarantine, lineage, and rerun tests pass |
| Fabric medallion notebooks | DEPLOYED | All 18 core notebook definitions (`00`-`16`) are deployed; Spark catalog validation confirms 29 enterprise Bronze, 30 enterprise Silver, and 65 Gold products, including 18-row agent context and 126-row persona scorecard |
| Eventhouse KQL | DEPLOYED | 14 tables, 13 functions, and 6 materialized views deployed and retrieved |
| Warehouse SQL | DEPLOYED | 77 `ops` views, 13 least-privilege roles, and empty-by-default persona scope deployed; queries return 18 agent rows, 126 persona rows, and 864 employees. Source now defines 79 core `ops` views after `vw_scenario_kpi` and `vw_scenario_outcome_comparison` were added, plus 14 EASA views and 5 EASA roles |
| TMDL semantic model | DEPLOYED | Definition retrieved with runtime Warehouse binding and no placeholders; DAX query returns 18 airports, 126 persona rows, and 18 agent rows |
| PBIR reports | DEPLOYED | Report retrieved with 25 pages, 12 GeoJSON resources, and a Power BI dataset binding to the deployed shared model. The source project now carries 26 pages after the scenario-outcomes detail page was added; that page is not in the retrieved item and requires a redeployment of notebook `10` |
| GeoJSON package | VALIDATED | 12 layers, 688 unique features, coordinate ranges, closure, and PBIR packaging pass |
| Fabric app source project | VALIDATED | 11 audience navigation targets and safety notices resolve locally; target API rejects native `FabricApp` as an invalid item type |
| Native Fabric app item | UNSUPPORTED | Target returned `InvalidItemType` for `FabricApp`; no native app item was created |
| Rayfin native Fabric artifact | UNSUPPORTED | No verified Microsoft Fabric item type or deployment API found |
| Rayfin app fallback | VALIDATED | Configurable advisory module with evidence, confidence, warnings, and decision audit contract |
| Portable digital twin | VALIDATED | 15 DTDL `;1` interfaces plus 5 `;2` observed-state interfaces, complete sample graph, relationship contracts, and telemetry/property separation pass local checks |
| Graph ontology | VALIDATED | Portable definitions, Gold nodes/edges, and governed source mappings pass local checks |
| Fabric Data Agent | DEPLOYED | Native item published with exactly two sources: 29 selected Warehouse `ops` views and 13 selected KQL functions/views; zero raw KQL tables or extra sources. `data-agent/definition.json` now allowlists 31 Warehouse views after the two scenario views were added |
| Terraform infrastructure (`infra/`) | DEPLOYED | Apply created the workspace, Lakehouse, Warehouse, Eventhouse, and read/write KQL database; Fabric REST retrieval and no-change second plan passed |
| Fictional reference mode | VALIDATED | Deterministic 18-anchor fictional snapshot; distinct from public mode and rerun-stable |
| Fabric workspace deployment | DEPLOYED | Workspace exists on the approved existing capacity; optional system-assigned workspace identity was disabled after target capability failure |
| Post-deployment retrieval validation | VALIDATED | Fabric REST retrieved the workspace and all Terraform-managed core items; second Terraform plan reported no changes |
| Azure Digital Twins runtime | DEPLOYED | West Europe dev runtime contains 15 immutable models, 15 twins, 14 relationships, and two telemetry messages; resource-scoped Data Owner RBAC, object retrieval, and representative query are verified |
| 3D scene package | VALIDATED | Deterministic 18-scene graph of 1,134 twins, 2,304 relationships, and 18 `.glb` models; applied to the dev runtime out of band, and a 3D Scenes Studio scene must still be created interactively |
| EASA regulatory foundation | BLOCKED | Warehouse schema/views/security, notebooks `17`-`18`, semantic model, and interactive report are deployed to the dev workspace; the annual submission inventory is unapproved, so coverage is `BLOCKED_NO_APPROVED_INVENTORY` and export/transmission stay disabled |
| EASA paginated report | UNSUPPORTED | The tenant rejects the documented `PaginatedReportDefinition` item format; the validated RDL remains a source artifact |

## Deployment truth

Terraform infrastructure, supported Fabric content, and the governed Azure Digital Twins dev runtime were deployed and independently retrieved or queried. Native Fabric app deployment remains unsupported by this target. The ADT runtime uses public network access for this bounded dev deployment; private networking remains a separate architecture decision.

## Local validation evidence

- Command: `python tests/validate_platform.py`
- Result: 33 tests, 0 failures, 0 errors
- Smoke logical records: 166,077
- Smoke pipeline checksum (`run_pipeline(...).logical_checksum()`): `85871e8b94b9f5df247dc24e939ed926f4fd93d87de136880b25d393ace10b5f`
- Simulated turnaround: 48.1534 to 39.1071 minutes
- Baseline missed preferred boarding-window rate: 34.87%
- P95 queue-wait reduction: 37.86%
- Revenue-per-passenger increase: 22.20%
- Simulated regulatory preparation automation: 79.41% (an operational KPI of the synthetic scenario; it is **not** EASA submission inventory coverage, which remains `BLOCKED_NO_APPROVED_INVENTORY`)
- Energy-per-passenger efficiency improvement: 14.33%