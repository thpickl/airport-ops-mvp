# Fabric Capability Matrix

Documentation was retrieved successfully from Microsoft Learn on 2026-08-08. Tenant acceptance and capacity-specific behavior still require runtime probes.

| Capability | Supported source/deployment format | Repository path | Status | Runtime condition |
|---|---|---|---|---|
| Lakehouse, Warehouse, Eventhouse, KQL database | Fabric Core item create/get APIs | `deployment/manifest.json` | IMPLEMENTED | Existing workspace and authorized token |
| Notebook definition | IPYNB item definition plus job scheduler API | `notebooks/` | IMPLEMENTED | Target accepts definition and job type |
| Warehouse objects | Fabric Warehouse T-SQL | `warehouse/` | IMPLEMENTED | Runtime SQL endpoint and Entra token |
| Eventhouse objects | KQL management/query commands | `eventhouse/` | IMPLEMENTED | Runtime KQL URI and database |
| Semantic model | PBIP semantic model project with TMDL | `semantic-model/AirportOpsSharedModel.SemanticModel/` | IMPLEMENTED | Target definition API accepts TMDL payload |
| Report | PBIP report project with PBIR | `reports/AirportOpsPersonaReports.Report/` | IMPLEMENTED | Target definition API accepts PBIR payload |
| Fabric app project | Fabric app source project | `app/` | IMPLEMENTED | Publication/audiences may require tenant-supported workflow |
| Fabric Data Agent | Product experience and capability-probed item definition | `data-agent/` | IMPLEMENTED | Item type/API acceptance must be proven in target |
| Azure Maps report visual | PBIR visual plus packaged WGS84 GeoJSON | `geospatial/azure-maps/` | IMPLEMENTED | Tenant visual policy and supported PBIR schema |
| Digital twin | Portable DTDL plus optional Azure Digital Twins REST adapter | `digital-twin/` | IMPLEMENTED | Disabled until endpoint and identity supplied |
| Fabric infrastructure (Terraform) | Verified `microsoft/fabric` provider `~> 1.12` | `infra/` | VALIDATED | `terraform validate` passed; `apply` needs auth and self-provisioned capacity |
| Rayfin native item | No verified Fabric item type/API | `fabric-app/rayfin-module.json` | UNSUPPORTED | Use app-module fallback; do not submit an invented item type |

## Verified references

- Fabric Core create item: https://learn.microsoft.com/en-us/rest/api/fabric/core/items/create-item
- Fabric Core update item definition: https://learn.microsoft.com/en-us/rest/api/fabric/core/items/update-item-definition
- Fabric on-demand item job: https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/run-on-demand-item-job
- PBIP, PBIR, and TMDL projects: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview
- Fabric Data Agent product workflow: https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent
- Fabric app project: https://learn.microsoft.com/en-us/fabric/apps/create-app
- Microsoft Fabric Terraform provider (verified `1.12.1` via `terraform validate`): https://registry.terraform.io/providers/microsoft/fabric/latest/docs

The capability probe must use the target tenant. Documentation availability is not deployment evidence.