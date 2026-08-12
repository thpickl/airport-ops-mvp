# Implementation Plan

## Scope and decision

Extend the existing source-complete Fabric demonstration rather than replace it. Preserve its KQL, Warehouse SQL, TMDL, PBIR, app, ontology, Data Agent, digital-twin, and guarded deployment assets while replacing the old fictional 15-airport execution contract with a deterministic 18-anchor case-study core.

## Phases

| Phase | Deliverable | Exit check | Status |
|---|---|---|---|
| 1 | Repository inventory, capability ledger, dependency manifest | Existing assets classified and cloud boundary explicit | VALIDATED |
| 2 | Versioned configuration, stable IDs/hashes, public-reference snapshot | Two-run deterministic unit check and 18 unique anchors | IMPLEMENTED |
| 3 | Event-level baseline/improvement simulator across required domains | KPI outcomes produced from events within documented tolerances | IMPLEMENTED |
| 4 | Rerunnable Bronze, Silver, Gold local logic and Fabric notebook integration | Duplicate, correction, quarantine, lineage, and grain tests | IMPLEMENTED |
| 5 | Eventhouse KQL and Warehouse SQL serving/reconciliation | Static syntax/capability checks plus tenant execution when available | IMPLEMENTED |
| 6 | TMDL semantic model, PBIR reports, GeoJSON, app package | Structural validation and report disclaimer/accessibility checks | IMPLEMENTED |
| 7 | DTDL package, ontology, Rayfin fallback, governed Data Agent | Referential, source allow-list, refusal, and evaluation tests | IMPLEMENTED |
| 8 | Dry-run/apply orchestration, state, reset, teardown, recovery | Dry-run and second-run idempotency pass; cloud apply separately evidenced | IMPLEMENTED |

## Execution boundary

- Local validation must require no Fabric credentials and must not emit high-volume data into source control.
- Fabric apply requires runtime authentication and identifiers. A `202 Accepted` response is not success until the long-running operation completes and the item is retrieved.
- External adapters remain disabled unless configuration, authentication, and an explicit apply mode are supplied.
- No component has an operational write path. Recommendations are advisory and require human review.

## Continuation order

Run local validation, inspect `deployment/artifact-manifest.yaml`, execute the Fabric dry-run notebook, then enable apply only in an authorized demo workspace. Record retrieved item IDs and validation evidence in the runtime deployment ledger; never edit source status to `DEPLOYED` without that evidence.