# Testing Guide

## Local command

```powershell
python -m pip install -r requirements.txt
python tests/validate_platform.py
```

The suite runs without Fabric credentials and covers configuration, source provenance, two-run deterministic checksums, UUID stability, event fault handling, same-batch idempotency, Silver uniqueness/quarantine, Gold metadata, smoke outcomes, DST transitions, notebook syntax, KQL/SQL/TMDL/PBIR source structure, DTDL v2, GeoJSON, Data Agent controls, secret scanning, deployment planning, and teardown safeguards.

## Generated source check

```powershell
python data/reference/generate_fictional_reference.py
python geospatial/generate_geojson.py
python reports/generate_pbir.py
git diff --exit-code
```

## Fabric commands

```powershell
python deployment/scripts/fabric.py plan
python deployment/scripts/fabric.py apply
python deployment/scripts/fabric.py validate
python deployment/scripts/fabric.py status
```

`apply` requires runtime-only authentication and target identifiers. `validate` retrieves actual workspace items. A submitted job is not deployment success, and a source artifact is never labeled `DEPLOYED` without retrieval evidence.

Tenant-side notebooks `06` and `12` perform Delta row counts, referential integrity, KPI reconciliation, classification, source allow-list, and second-pass fingerprint checks.

## Terraform infrastructure

```powershell
terraform fmt -check -recursive infra
cd infra/environments/dev
terraform init -backend=false
terraform validate
```

`terraform validate` was verified against `microsoft/fabric` v1.12.1. `apply` requires authentication and a self-provisioned Fabric Capacity and is not run in portable validation.