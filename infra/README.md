# Fabric Infrastructure (Terraform)

Provisions the Fabric workspace and core items with the verified **`microsoft/fabric`** provider.

> Real airport identities are used only as public geographic reference anchors. All ownership, infrastructure, flights, passengers, employees, operations, performance, incidents, commercial activity, recommendations, and outcomes are synthetic.

## Verified provider

- Provider: `microsoft/fabric` (partner, Microsoft)
- Version pin: `~> 1.12` (latest verified `1.12.1`, published 2026-08-06)
- Terraform: `>= 1.8, < 2.0`
- Source: https://registry.terraform.io/providers/microsoft/fabric/latest/docs

Only resources whose schema was verified against v1.12.1 are used:

| Resource | Purpose | Verified attributes |
|---|---|---|
| `fabric_workspace` | Demo workspace | `display_name`, `capacity_id`, `identity`, `description` |
| `fabric_lakehouse` | Medallion lakehouse | `display_name`, `workspace_id`, `configuration.enable_schemas` |
| `fabric_warehouse` | Serving warehouse | `display_name`, `workspace_id`, `configuration.collation_type` |
| `fabric_eventhouse` | Real-time eventhouse | `display_name`, `workspace_id`, `configuration.minimum_consumption_units` |
| `fabric_kql_database` | KQL database | `display_name`, `workspace_id`, `configuration.database_type`, `configuration.eventhouse_id` |

## Layout

```
infra/
  modules/
    fabric-workspace/     # workspace + optional capacity + system-assigned identity
    fabric-core-items/    # lakehouse, warehouse, eventhouse, kql database
  environments/
    dev/                  # composition root, tfvars example, backend example
  platform/               # Bicep: ingestion, AI, and ML plane (AVM modules)
  digital-twin/           # Bicep: Azure Digital Twins instance and 3D scene storage
```

## Platform plane (Bicep)

[platform/main.bicep](platform/main.bicep) provisions the ingestion, AI, and ML services
that sit beside Fabric. It uses Azure Verified Modules only, assigns data-plane roles to a
user-assigned managed identity and the operator, and emits endpoints — never keys.

| Resource | Purpose | Auth posture |
|---|---|---|
| User-assigned identity | Single workload identity for cross-service access | — |
| Log Analytics + App Insights | Observability sink for all diagnostic settings | — |
| Key Vault | Runtime configuration and secret custody | RBAC only, purge protection on |
| Azure OpenAI | Ground-ops orchestration, retail personalisation, grounding | `disableLocalAuth: true` |
| Azure Maps | Terminal, stand, and flow geospatial layers | Entra ID, `Azure Maps Data Reader` |
| Event Hubs | Streaming ingestion consumed by Fabric | `disableLocalAuth: true` |
| IoT Hub | Stand, gate, checkpoint, and energy device telemetry | System-assigned identity |
| Azure ML | 15-minute passenger-flow forecasting | `systemDatastoresAuthMode: Identity` |

`operatorPrincipalId` is runtime-only. Supply it without committing a tenant principal ID:

```powershell
$env:AZ_OPERATOR_PRINCIPAL_ID = (az ad signed-in-user show --query id -o tsv)
az deployment group what-if -g <rg> -f platform/main.bicep -p platform/main.dev.bicepparam
az deployment group create  -g <rg> -f platform/main.bicep -p platform/main.dev.bicepparam
```

Azure Digital Twins is not offered in `francecentral`; the instance is deliberately placed in
`westeurope`. This is a recorded regional deviation, not a defect.

## Safety

- No tenant IDs, capacity IDs, workspace IDs, secrets, or tokens are committed.
- `capacity_id` and any principal IDs are runtime-only variables (prefer `TF_VAR_*`).
- `environment` accepts only `dev` or `test`; production is rejected by variable validation.
- `resource_prefix` is validated; the workspace carries a `prevent_destroy` lifecycle guard.
- `.gitignore` excludes state and non-example `*.tfvars`.

## Usage

For the full numbered runbook, see [DEPLOYMENT.md](DEPLOYMENT.md).

Authenticate first (Azure CLI, Managed Identity, or Service Principal env vars), then:

```powershell
cd infra/environments/dev
terraform init
terraform validate
terraform plan -out tfplan
terraform apply tfplan
```

Supply capacity at runtime without committing it:

```powershell
$env:TF_VAR_capacity_id = "<your-capacity-guid>"
```

## Relationship to the notebook deployment path

This Terraform layer **bootstraps** the workspace and core items. The notebook and
REST path ([deployment/scripts/fabric.py](../deployment/scripts/fabric.py), `notebooks/10`, `notebooks/11`)
then deploys item **definitions** (notebooks, TMDL, PBIR) and executes Warehouse SQL and
Eventhouse KQL. Use `terraform output workspace_id` as `FABRIC_WORKSPACE_ID` for that path.

## Teardown

`terraform destroy` is intentionally blocked by `prevent_destroy` on the workspace. To
tear down a demo environment, explicitly remove that guard, confirm the `dev`/`test`
environment and `fao-demo` prefix, and destroy. Never target a production workspace.

## Status

- Source and schema: `VALIDATED` against provider v1.12.1 documentation.
- `terraform validate`/`apply`: `BLOCKED` here — requires Terraform, authentication, and a self-provisioned Fabric Capacity. A plan/apply is not claimed as deployed until it succeeds and outputs are retrieved.
