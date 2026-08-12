# Reset, Rollback, and Teardown

## Principles

- Prefer rerun over delete: data notebooks overwrite or create/replace their owned tables.
- Preserve evidence by default: deployment and teardown ledgers remain unless explicitly removed.
- Delete only objects this demo created. Reused Fabric items are never eligible for item teardown.
- Never delete a workspace.

## Reset validation baseline

Run notebook 13 with:

```text
operation = RESET_VALIDATION
dry_run = True
```

Review the list, then rerun with `dry_run = False`. This removes validation results, lineage output, and fingerprint baselines only. Run notebook 12 once to create a new baseline, rerun data notebooks, then run notebook 12 with `require_second_run = True`.

## Reset all demo data

Run notebook 13 with:

```text
operation = RESET_DATA
dry_run = False
confirmation = RESET AIRPORT OPS DATA
```

Only the explicit table allowlist is dropped. Rebuild through notebook 11. Warehouse views remain and can temporarily fail until Gold tables are recreated.

## Roll back definitions

Definitions are source-controlled. To roll back semantic model, report, app module, Data Agent, SQL, or KQL artifacts:

1. Restore the desired repository revision through normal source control.
2. Run `python tests/validate_platform.py`.
3. Run notebook 10 in dry-run.
4. Run notebook 10 live to reapply definitions and idempotent serving scripts.
5. Run notebook 12 and the Warehouse/Eventhouse validation scripts.

Model IDs in DTDL are immutable. Use the prior definition only when it is byte-equivalent; otherwise publish a new DTDL model version and update instances deliberately.

## Teardown Fabric items

Run notebook 13 first in dry-run, then live with:

```text
operation = TEARDOWN_ITEMS
allow_destructive_teardown = True
confirmation = DELETE AIRPORT OPS DEMO
workspace_id = <runtime value>
```

Eligibility requires all of the following:

- item name and type are on the notebook allowlist;
- `deployment_results` records `SUCCEEDED`;
- `status_detail` is exactly `Created item`;
- an item ID is present.

Items are deleted in reverse dependency order. Same-name items that were reused are excluded.

## Warehouse rollback

Run `warehouse/04_teardown.sql` to remove enterprise views only. It retains `audit.deployment_run` by default. Core views can be restored by rerunning their source scripts.

## Eventhouse rollback

KQL objects are not deleted automatically. This avoids deleting shared or preexisting Eventhouse objects. Use a separately approved, database-scoped teardown after confirming ownership from deployment evidence.
