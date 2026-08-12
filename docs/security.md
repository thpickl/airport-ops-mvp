# Security Design

## Data minimization

- No real passenger, customer, employee, booking, ticket, passport, payment, contact, loyalty, or biometric data.
- Synthetic people use deterministic opaque tokens that do not resemble government or loyalty identifiers.
- Data Agent and reports use aggregate Gold products; person, booking, bag, and employee tokens are hidden or excluded.
- Incident data is synthetic and contains no real vulnerability or security-procedure detail.

## Identity and secrets

- Fabric/Azure calls use notebook runtime identity (`notebookutils.credentials.getToken`).
- Workspace/capacity/endpoints are runtime parameters or environment placeholders.
- No credentials, tenant/subscription IDs, tokens, connection strings, or real endpoints are committed.
- `.gitignore` excludes local environment and secret material.

## Serving authorization

Warehouse roles:

- `airport_ops_report_reader`: SELECT on curated `ops` schema.
- `airport_ops_data_agent_reader`: object-level SELECT only on approved grounding views.
- `airport_ops_deployer`: deployment audit access.

Bronze, Silver, quarantine, raw Files, and unrestricted event payloads are not granted to the Data Agent role. TMDL includes read roles and an advisory/synthetic filter for agent context.

## Persona access pattern

All personas share one governed semantic model with perspectives. Perspectives improve discoverability but are not security boundaries. Deployers must use Fabric workspace/app audiences and semantic-model RLS/OLS where target-specific identity separation is required.

## Control boundary

The solution has no action tools or operational write-back. It cannot control or update ATC, AODB, BHS, BMS, aircraft, gates, equipment, assets, or staff assignments. High-impact recommendations require authorized human approval through an external governed process.

## Validation

Portable secret scanning, source allowlist tests, Warehouse grant checks, Data Agent refusal cases, advisory-only assertions, and scoped teardown ownership checks run in `tests/validate_platform.py` and notebooks 06/12.
