# API Support Matrix

This matrix records the automation path and the failure state for each artifact. It is a capability contract, not deployment evidence: what a target actually accepted is recorded in `deployment_results` and summarized in [implementation-status.md](implementation-status.md).

| Artifact | Automation path | Repository behavior | Status if unavailable |
|---|---|---|---|
| Existing workspace | Runtime parameter | Never created or deleted | `SKIPPED_PREREQUISITE` |
| Lakehouse | Fabric generic item API | Create or reuse | `FAILED` because required |
| Warehouse | Fabric generic item API | Create or reuse | `FAILED` because required |
| Eventhouse | Fabric generic item API | Create or reuse | `FAILED` because required |
| KQL Database | Fabric generic item API | Create under Eventhouse | `FAILED` because required |
| Notebooks | Item definition API | Deploy IPYNB and inject Lakehouse dependency | `FAILED` because required |
| Notebook execution | On-demand item job API | Submit, poll, checkpoint, resume | `FAILED` because required |
| Warehouse SQL | Runtime SQL endpoint with Entra token | Execute ordered idempotent batches | `SKIPPED_PREREQUISITE` if endpoint omitted |
| Eventhouse KQL | Runtime KQL URI with runtime token | Execute ordered commands and queries | `SKIPPED_PREREQUISITE` if URI omitted |
| Semantic model | Item definition API with TMDL | Replace runtime parameters and deploy | `FAILED` when requested and rejected |
| Power BI report | Item definition API with PBIR | Deploy 11 persona and 15 detail pages | `FAILED` when requested and rejected |
| Fabric Data Agent | Capability-checked item definition | Attempt only when enabled | `SKIPPED_UNSUPPORTED` |
| Fabric app | Capability-checked item definition | Attempt only when enabled | `SKIPPED_UNSUPPORTED` |
| Rayfin | Configurable app module | No native item assumed | `SKIPPED_UNSUPPORTED` for native path |
| Azure Digital Twins | Parameterized Azure Digital Twins REST | Validate, create missing models, upsert graph | `SKIPPED_PREREQUISITE` unless target supplied |
| Azure Maps | PBIR Azure Maps visual + packaged GeoJSON | Uses generated WGS84 report resources | No Azure Maps account required for source package |

## References

- Fabric create item: https://learn.microsoft.com/en-us/rest/api/fabric/core/items/create-item
- Fabric update item definition: https://learn.microsoft.com/en-us/rest/api/fabric/core/items/update-item-definition
- Fabric run item job: https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/run-on-demand-item-job
- PBIP/PBIR/TMDL projects: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview
- Fabric Data Agent creation: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- Fabric apps project: https://learn.microsoft.com/en-us/fabric/apps/create-app

API availability, accepted item definitions, and preview behavior can vary by tenant/capacity. The deployment ledger is authoritative for an actual run.
