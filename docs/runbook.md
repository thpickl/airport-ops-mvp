# Operations Runbook

## Routine execution

1. Run notebook 15 and review recorded failures, unsupported operations, and missing evidence.
2. Confirm `demo_config.json`, runtime environment, feature flags, seed, base date, and scale.
3. Run notebook 11 with a stable orchestration run ID.
4. Require notebooks 06 and 12 to pass before consuming reports or Data Agent outputs.
5. Run notebook 15 again and retain runtime JSON/Delta evidence.

## Data refresh

- Full deterministic refresh: notebooks 01-09, then 05 if core agent context must be rebuilt after physical changes, followed by 06/12.
- Serving refresh: notebook 10 after Gold validation.
- Report source refresh: run `reports/generate_pbir.py`, portable tests, then notebook 10.
- Fictional catalog change: update `data/reference/generate_fictional_reference.py`, regenerate catalogs/spatial/report artifacts, and reset the idempotency baseline deliberately.

## Health checks

- `gold_it_service_health`: row-count, quality, refresh, security, synthetic capacity/cost proxies.
- `validation_results` and `validation_results_production`: mandatory checks.
- `deployment_results`: API/script outcomes and request IDs.
- `orchestration_checkpoint`: job submission/completion.
- `lineage_contract`: domain path coverage.

## Incident response

This runbook covers demonstration-platform failures only, never real airport incidents.

1. Preserve request ID, deployment run ID, notebook output, and validation evidence.
2. Stop on `FAILED`; do not relabel unsupported/missing prerequisites as success.
3. Use `docs/troubleshooting.md` for the failing layer.
4. Roll back source-controlled definitions or reset the scoped data layer.
5. Re-run portable validation and dry-run before live retry.

## Reset and teardown

Use notebook 13. Start with dry-run. Data reset requires `RESET AIRPORT OPS DATA`; item teardown requires explicit enablement and `DELETE AIRPORT OPS DEMO`. The workspace and reused items are never deleted.

## Safety

Reports and Data Agent answers are synthetic analytical demonstrations. No output is suitable for operational decisions or write-back. High-impact recommendations require authorized human review outside this solution.
