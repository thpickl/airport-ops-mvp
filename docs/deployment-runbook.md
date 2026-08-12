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
python tests/validate_platform.py
```

The second command must report zero failures. This validates portable artifacts and the 18-airport smoke scenario, not a tenant deployment.

Fabric dry-run dependency plan:

```powershell
python deployment/scripts/fabric.py plan
```

Fabric apply requires runtime-only `FABRIC_WORKSPACE_ID`, `FABRIC_CAPACITY_REFERENCE`, `FABRIC_ORCHESTRATOR_NOTEBOOK_ID`, and `FABRIC_ACCESS_TOKEN`:

```powershell
python deployment/scripts/fabric.py apply
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
- `dry_run = False`
- `run_second_pass = True`
- `include_platform_deployment = True` when serving and BI deployment is required
- `artifact_root`
- `warehouse_sql_endpoint`
- `kql_query_uri`

Execution order:

1. Base simulation and Bronze (`01`)
2. Base Silver (`02`)
3. Base Gold (`03`)
4. Physical/spatial context (`04`)
5. Extended Gold and core agent context (`05`)
6. Enterprise Bronze (`07`)
7. Enterprise Silver (`08`)
8. Enterprise Gold (`09`)
9. Core validation (`06`)
10. Production baseline validation (`12`)
11. Deterministic second pass of `01`-`09`
12. Second core validation (`06`)
13. Optional serving/TMDL/PBIR/app/agent deployment (`10`)
14. Required second-run fingerprint comparison (`12`)

Use a stable `orchestration_run_id` to resume the same run. Set `force = True` only when intentionally rerunning completed checkpoints.

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
