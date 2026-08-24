# Deployment Runbook

## Scope and safety

This repository uses public airport geographic reference anchors and deploys deterministic synthetic operating artifacts. It contains no real PII, biometrics, schedules, incidents, credentials, tenant identifiers, customer endpoints, or operational integrations. Recommendations remain advisory and no component can command ATC, AODB, BHS, BMS, aircraft, gates, equipment, assets, or staff.

## Prerequisites

- Existing Fabric-enabled workspace and capacity. Workspace lifecycle is intentionally outside this repository.
- Workspace Contributor or higher for the deploying runtime identity.
- Fabric notebook runtime identity able to call Fabric item APIs.
- Repository bundle available to the bootstrap notebook at `artifact_root`, normally through Fabric Git integration or a OneLake Files sync.
- Runtime Warehouse SQL endpoint only when Warehouse scripts are enabled.
- Runtime KQL query URI only when Eventhouse scripts are enabled.
- Optional Azure Digital Twins endpoint and data-owner permissions only when notebook 14 is explicitly enabled.

No endpoint, workspace ID, credential, or tenant ID is stored in source.

## Local preflight

From the repository root:

```powershell
python -m pip install -r requirements.txt
python ontology/generate_ontology.py --check
python ontology/validate_ontology.py
python tests/validate_platform.py
```

The validation commands must report zero failures. They validate portable artifacts and the 18-airport smoke scenario, not a tenant deployment.

Fabric dry-run dependency plan:

```powershell
python deployment/scripts/fabric.py plan
```

Fabric apply requires runtime-only `FABRIC_WORKSPACE_ID`, `FABRIC_CAPACITY_REFERENCE`, `FABRIC_ORCHESTRATOR_NOTEBOOK_ID`, and `FABRIC_ACCESS_TOKEN`:

```powershell
python deployment/scripts/fabric.py apply
```

Optional runtime variables:

| Variable | Effect |
|---|---|
| `FABRIC_TOKEN_COMMAND` | Command printing a fresh bearer token. Without it a run outliving the token lifetime fails the poll with `401` even though the Fabric job is still running. |
| `FABRIC_WAREHOUSE_SQL_ENDPOINT` | Serving endpoint for notebook 10. |
| `FABRIC_KQL_QUERY_URI` | Eventhouse query URI for notebook 10. |

`include_platform_deployment` is derived: it is enabled only when **both** endpoints are supplied. Without them notebook 10 reports `SKIPPED_PREREQUISITE` and **no semantic model, report, or Data Agent is deployed** — the apply result records this explicitly rather than implying BI content exists.

```powershell
$env:FABRIC_TOKEN_COMMAND = "az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv"
$env:FABRIC_WAREHOUSE_SQL_ENDPOINT = "<warehouse-sql-endpoint>"
$env:FABRIC_KQL_QUERY_URI = "<eventhouse-query-uri>"
```

Post-deployment retrieval validation:

```powershell
python deployment/scripts/fabric.py validate
```

## Bootstrap

1. Make the repository available at the configured `artifact_root`.
2. Import or invoke `00_Deploy_Fabric_Items` in the existing workspace. This one notebook is the bootstrap boundary if Fabric Git or an external caller has not already created it.
3. Run with `dry_run = True`. Review only `DRY_RUN` and intentional skip states.
4. Set `workspace_id` at runtime and run with `dry_run = False`.
5. Confirm `AirportOpsLakehouse`, `AirportOpsWarehouse`, `AirportOpsEventhouse`, and `AirportOpsRealtime` exist.
6. Confirm notebook definitions were deployed and contain the default Lakehouse dependency injected by notebook 00.

Notebook 00 reuses same-name/same-type items. Duplicate matches are a hard failure.

## Orchestrated deployment

Run `11_Orchestrate_Deployment` with runtime parameters:

- `workspace_id`
- `capacity_reference`
- `deployment_mode = 'apply'` (`dry-run` and `plan` both validate without submitting jobs)
- `run_second_pass = True`
- `include_platform_deployment = True` when serving and BI deployment is required
- `include_lakehouse_maintenance = True` only when Delta maintenance is intended
- `deploy_conditional_artifacts = True` only when Data Agent/app deployment is intended
- `artifact_root`
- `warehouse_sql_endpoint`
- `kql_query_uri`

Execution order:

1. Preflight (`00_Validate_Prerequisites`)
2. First pass data: `01`, `02`, `03`, `04`, `05`, `07`, `08`, `09`
3. First pass validation: core (`06`), then production baseline (`12` with `validation_phase = BASELINE`, `require_second_run = False`)
4. Second pass data: the same `01`-`09` sequence, when `run_second_pass = True`
5. Second pass validation: core (`06`), then required fingerprint comparison (`12` with `validation_phase = SECOND_RUN`, `require_second_run = True`)
6. Optional Delta maintenance (`16`) when `include_lakehouse_maintenance = True`
7. Optional serving/TMDL/PBIR/app/agent deployment (`10`) when `include_platform_deployment = True`
8. Read-only status summary (`15`)

Notebook `12` therefore runs its required second-run comparison before notebook `10`. Platform deployment does not gate idempotency evidence, and idempotency evidence does not depend on BI content existing.

Use a stable `orchestration_run_id` to resume the same run. Set `force = True` only when intentionally rerunning completed checkpoints.

The EASA notebooks `17` and `18` are not part of this orchestration. They are run separately and remain fail-closed until a named compliance owner approves a submission inventory; see [easa/README.md](easa/README.md).

## Platform artifacts

Notebook 10:

- executes Warehouse scripts transactionally through runtime identity;
- executes KQL schema, mappings, functions, policies, materialized views, and validation;
- replaces TMDL Warehouse placeholders at runtime;
- deploys semantic model and report definitions through item-definition APIs;
- capability-checks Data Agent and Fabric app item types when enabled;
- records native Rayfin as `UNSUPPORTED` and retains the configurable module package.

Accepted result states are `SUCCEEDED`, `DRY_RUN`, `SKIPPED_PREREQUISITE`, `SKIPPED_UNSUPPORTED`, and `FAILED`. A submission or HTTP 202 is not success until its long-running operation reports completion.

## Digital twin

Run notebook 14 separately after notebook 05 when an approved Azure Digital Twins target exists.

1. Run with `dry_run = True` and no endpoint to validate DTDL and graph integrity.
2. Supply `digital_twins_endpoint` at runtime.
3. Run with `dry_run = False`.

Existing identical model versions are reused. A different definition under the same immutable model ID fails. Twins and relationships are idempotent PUT operations.

## Conditional limitations

- Data Agent definition deployment is attempted only when `deploy_conditional_artifacts = True`. If the target tenant rejects the item type or definition shape, artifact deployment remains `UNSUPPORTED`; use the checked-in definition and documented product creation experience.
- Fabric app publication/audience assignment may require platform support beyond item-definition import.
- No verified native Rayfin item/API is assumed. `fabric-app/rayfin-module.json` is the executable configuration contract.
- Authentication and the initial bootstrap notebook/import are unavoidable platform boundaries.

## Validation evidence

Required evidence tables:

- `validation_results`
- `validation_results_production`
- `validation_idempotency_manifest`
- `validation_idempotency_manifest_production`
- `lineage_contract`
- `deployment_results`
- `orchestration_checkpoint`
- runtime JSON manifests written according to `deployment/evidence-schema.json`

Run notebook `15_Deployment_Status` for an evidence-based status summary. `NOT_AVAILABLE`, `SKIPPED_PREREQUISITE`, and `SKIPPED_UNSUPPORTED` are not success states.

The final notebook 12 run must pass with `require_second_run = True`. A first-run baseline alone is not idempotency evidence.
