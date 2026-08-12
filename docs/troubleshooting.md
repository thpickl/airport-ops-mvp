# Troubleshooting

## Bootstrap notebook cannot find the repository

- Confirm `artifact_root` resolves on the Fabric driver.
- Use Fabric Git integration or sync the repository bundle to OneLake Files.
- Run notebook 00 in dry-run. `SKIPPED_PREREQUISITE` is expected until the bundle is mounted.

## Notebook job cannot find a default Lakehouse

- Rerun notebook 00. It injects `default_lakehouse`, name, workspace, and known-Lakehouse metadata into each IPYNB definition.
- Confirm the Lakehouse item ID in `deployment_results` still exists.

## Warehouse script fails on three-part names

- Confirm Lakehouse and Warehouse are in the same workspace.
- Confirm the Lakehouse SQL endpoint exposes the target Delta table.
- Keep the `ops.vw_*` contract stable if materialization is required by the target configuration.

## Warehouse connection fails

- Supply `warehouse_sql_endpoint` at runtime.
- Confirm the runtime identity has connect and DDL permissions.
- Confirm ODBC Driver 18 is available in the Fabric runtime.
- The notebook uses an Entra token, not a SQL credential.

## KQL deployment fails

- Supply the target KQL query URI and database name at runtime.
- Confirm runtime token audience and database permissions.
- Run scripts in numeric order. Update policies depend on raw and curated tables.
- Review the request ID in `deployment_results`.

## Semantic model deployment reports an unresolved parameter

- Supply `warehouse_sql_endpoint` and `warehouse_database_name`.
- Never replace placeholders in source control with a tenant endpoint.
- Rerun local validation after any TMDL change.

## PBIR report does not bind to the model

- Confirm `AirportOpsSharedModel` deployed successfully first.
- Target tenants can differ in path-binding behavior for item-definition import. Treat an API rejection as `FAILED`, then use the same PBIR project through supported Fabric Git/PBIP import.
- Do not edit the report to point at an unrelated model.

## Data Agent or Fabric app is skipped

- This is expected when the target does not accept the item type/definition API.
- Use the checked-in source definition in the documented product creation experience.
- Keep `SKIPPED_UNSUPPORTED` in deployment evidence; do not relabel it as success.

## Second-run idempotency fails

- Compare `validation_idempotency_current` with `validation_idempotency_manifest_production` by table name.
- Confirm seed, base date, scale, and observation timestamp are unchanged.
- Remove nondeterministic timestamps from source tables.
- Reset the baseline only when configuration intentionally changes.

## Digital twin model collision

- Azure Digital Twins model versions are immutable.
- If the existing definition is not byte-equivalent, increment the DTDL model version and update dependent instances.
- Do not replace an existing model ID silently.
