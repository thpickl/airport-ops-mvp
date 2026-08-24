# Configuration Guide

## Precedence

1. Runtime notebook/API parameters
2. `config/environments/<environment>.json`
3. `config/scale-profiles/<profile>.json`
4. `config/base/platform.json`

`config/demo_config.json` and `config/simulation_profiles.json` are compatibility views for the existing Fabric notebooks and must remain aligned with the versioned files.

## Defaults

| Setting | Default |
|---|---|
| Environment | `dev` |
| Resource prefix | `fao-demo` |
| Seed | `42` |
| Airport count | `18` |
| Fixed start | `2026-01-01T00:00:00Z` |
| Profile | `smoke` |
| Deployment | `dry-run` |
| Destructive operations | disabled |
| External adapters | disabled |
| Classification | `SyntheticOperational` |
| Recommendation mode | `AdvisoryOnly` |

Profiles are `unit`, `smoke`, `demo`, and `enterprise`. Enterprise output belongs in Fabric storage and must not be committed.

Runtime identifiers and tokens use the environment variable names in `config/base/platform.json` and [.env.example](../.env.example). Never populate `.env.example` with real values and never commit `.env`.

`config/streaming_sources.example.json` is the committed streaming source registry. Its namespace FQDN, Eventhouse and KQL database item IDs, query URI, and per-hub connection IDs are `${VARIABLE}` placeholders resolved from the environment at load time. A resolved `config/streaming_sources.json` may be kept locally; it is git-ignored and takes precedence when present.

The airport list is replaced by editing a versioned snapshot with equivalent provenance fields. The validator enforces 1-18 selected anchors, valid IANA zones, unique codes, and WGS84 ranges.

`reference_mode` selects the anchor source: `public_reference` (default) uses the sourced public snapshot; `fictional` uses `config/reference/airport-anchors.fictional.json` (regenerate with `python config/reference/generate_fictional_anchors.py`) when public data cannot be redistributed. Both modes are deterministic and produce 18 anchors.