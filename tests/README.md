# Validation

## Local portable-artifact validation

From the repository root:

```powershell
python tests/validate_platform.py
```

This standard-library script returns exit code `1` on any failure. It validates:

- versioned seed/date/profile and public-reference configuration;
- all notebook JSON documents, required metadata, and Python cell syntax;
- DTDL v2 model IDs, relationship targets, complete twin instances, and graph endpoints;
- GeoJSON layer coverage, WGS84 ranges, stable keys, public-anchor/synthetic classification, and polygon closure;
- core and enterprise ontology completeness and Gold/Warehouse-only source mappings;
- Warehouse and Eventhouse serving coverage, security, and rerunnable syntax markers;
- Date/Time and event-grain TMDL, 11 persona perspectives/pages plus 14 detail PBIR pages, Azure Maps/GeoJSON resources, and explicit measures;
- Fabric app, Rayfin fallback, Data Agent allowlist/evaluations, deployment manifest, orchestration, and scoped teardown;
- absence of common credential patterns.

VS Code persists standard Jupyter cell IDs at the cell level. The validator accepts either that representation or `metadata.id`, while requiring unique IDs and parseable code.

## Fabric data validation

1. Run the data notebooks in the order defined by `deployment/manifest.json`.
2. Run notebook `06_Validate_Extended_MVP` and notebook `12_Validate_Production_Demo` to create both baselines.
3. Rerun deterministic data notebooks `01`-`09` unchanged.
4. Rerun notebook `06`, then run notebook `12` with `require_second_run = True`.
5. Run ordered Warehouse/Eventhouse validation scripts through notebook `10` when those serving layers are enabled.

Notebooks `06` and `12` persist results before raising `AssertionError` on mandatory failures.
