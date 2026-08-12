# Terraform Deployment — Step by Step

Provisions the Fabric workspace and core items (Lakehouse, Warehouse, Eventhouse, KQL database) with the verified `microsoft/fabric` provider (`~> 1.12`, checked against `1.12.1`).

> Real airport identities are used only as public geographic reference anchors. All ownership, infrastructure, flights, passengers, employees, operations, performance, incidents, commercial activity, recommendations, and outcomes are synthetic.

`terraform apply` creates real, billable Fabric resources in your tenant. Run it yourself after authenticating.

---

## Step 1 — Confirm prerequisites

- [ ] Terraform `>= 1.8` installed (`terraform -version`).
- [ ] A **self-provisioned Fabric Capacity** in Azure. Trial capacity is not supported by the provider. Create one in the [Azure Portal](https://portal.azure.com/#browse/Microsoft.Fabric%2Fcapacities) and note its **capacity ID (GUID)**.
- [ ] Your identity can create Fabric workspaces and assign the capacity.

## Step 2 — Authenticate (choose one)

**Azure CLI (simplest):**

```powershell
az login
# optional: az account set --subscription "<subscription-id>"
```

**Service Principal (CI/automation):**

```powershell
$env:FABRIC_TENANT_ID = "<tenant-guid>"
$env:FABRIC_CLIENT_ID = "<app-registration-client-id>"
$env:FABRIC_CLIENT_SECRET = "<client-secret>"   # or use OIDC / certificate
```

**Managed Identity:**

```powershell
$env:FABRIC_USE_MSI = "true"
```

Never place secrets in `.tf` or `.tfvars` files.

## Step 3 — Move to the environment root

```powershell
cd infra/environments/dev
```

## Step 4 — Provide the capacity ID at runtime

```powershell
$env:TF_VAR_capacity_id = "<your-fabric-capacity-guid>"
```

This keeps the capacity ID out of source control. Leave it unset only if your workspace does not require an explicit capacity assignment.

## Step 5 — (Optional) Set variables

Copy the example and edit values as needed. The real `terraform.tfvars` is git-ignored.

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

| Variable | Default | Notes |
|---|---|---|
| `environment` | `dev` | Only `dev` or `test` are accepted; production is rejected. |
| `resource_prefix` | `fao-demo` | 3-24 lowercase letters/digits/hyphens. |
| `capacity_id` | `""` | Supply via `TF_VAR_capacity_id` (Step 4). |
| `enable_workspace_identity` | `true` | System-assigned workspace identity. |
| `eventhouse_minimum_consumption_units` | `0` | `0` disables always-on minimum consumption. |

The workspace is named `${resource_prefix}-${environment}-airport-ops` (for example, `fao-demo-dev-airport-ops`).

## Step 6 — Initialize

```powershell
terraform init
```

## Step 7 — Validate

```powershell
terraform validate
```

Expected: `Success! The configuration is valid.`

## Step 8 — Plan

```powershell
terraform plan -out tfplan
```

Review the plan. Expect one workspace, one lakehouse, one warehouse, one eventhouse, and one KQL database to be created.

## Step 9 — Apply

```powershell
terraform apply tfplan
```

## Step 10 — Capture outputs

```powershell
terraform output workspace_id
terraform output -raw warehouse_connection_string   # sensitive
terraform output -raw eventhouse_query_uri           # sensitive
```

Outputs available: `workspace_id`, `workspace_display_name`, `lakehouse_id`, `warehouse_id`, `eventhouse_id`, `kql_database_id`, `warehouse_connection_string` (sensitive), `eventhouse_query_uri` (sensitive).

## Step 11 — Hand off to the content-deployment path

Terraform creates the workspace and empty items. Deploy item definitions (notebooks, TMDL, PBIR) and run Warehouse SQL / Eventhouse KQL through the Python/notebook path:

```powershell
cd ../../..
$env:FABRIC_WORKSPACE_ID = "<workspace_id from Step 10>"
python deployment/scripts/fabric.py plan       # dry-run
python deployment/scripts/fabric.py apply       # requires FABRIC_* auth
python deployment/scripts/fabric.py validate    # retrieval evidence
```

---

## Teardown (guarded)

The workspace has `prevent_destroy = true`, so `terraform destroy` is blocked by default.

1. Confirm you are targeting a `dev`/`test` environment with the `fao-demo` prefix.
2. Remove the `lifecycle { prevent_destroy = true }` block in [modules/fabric-workspace/main.tf](modules/fabric-workspace/main.tf).
3. Run:

```powershell
cd infra/environments/dev
terraform destroy
```

Never target a production workspace.

## Troubleshooting

- **`capacity_id must be empty or a GUID`** — the value is not a 36-character GUID. Re-check `TF_VAR_capacity_id`.
- **`environment must be dev or test`** — set `environment` to `dev` or `test`.
- **Authentication/authorization errors on apply** — re-run `az login` or verify the service principal has workspace-create and capacity-assign permissions.
- **Capacity inactive/suspended** — ensure the Fabric Capacity is running in the Azure Portal before apply.

## State and CI

- For team use, configure a remote backend using [backend.tf.example](environments/dev/backend.tf.example) instead of local state.
- CI runs `terraform fmt -check` and `terraform validate` via the `terraform-validation` job in [.github/workflows/validate.yml](../.github/workflows/validate.yml). `apply` is intentionally never run in CI.
