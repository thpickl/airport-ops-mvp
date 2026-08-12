# Contributing

## Safety rules

- Keep every organization, region, airport, coordinate, airline, aircraft type, person, identifier, event, and outcome fictional.
- Never commit credentials, tokens, tenant/subscription/workspace IDs, real endpoints, personal data, operational schedules, incidents, vulnerabilities, or commercial data.
- Keep recommendations advisory and action tools disabled.
- Do not relabel `SKIPPED_PREREQUISITE`, `SKIPPED_UNSUPPORTED`, or unexecuted work as success.

## Change workflow

1. Update source generators before generated artifacts.
2. Preserve deterministic IDs, seed behavior, and schema compatibility unless a versioned migration is documented.
3. Normalize notebooks as nbformat 4 JSON with unique `metadata.id` and `metadata.language` on every cell.
4. Run:

```powershell
python data/reference/generate_fictional_reference.py
python geospatial/generate_geojson.py
python reports/generate_pbir.py
python tests/validate_platform.py
```

5. For Fabric-affecting changes, run notebook 00 preflight and all deployment notebooks in dry-run before authorized tenant execution.
6. Update data/KPI dictionaries, lineage, security, assumptions, limitations, rollback, and API support documentation.

## Pull-request evidence

Include portable test output, generated-file diff status, affected deployment dependencies, rollback path, and one of: tenant execution evidence, `BLOCKED_PREREQUISITE`, or `UNSUPPORTED_API` with the documented fallback.
