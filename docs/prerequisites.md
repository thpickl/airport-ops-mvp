# Prerequisites

## Portable development

- Windows, Linux, or macOS with Python 3.12+.
- No Azure/Fabric credential is required for source generation and portable validation.
- Run the fictional catalog, GeoJSON, PBIR, and portable validation commands from the repository root.

## Microsoft Fabric execution

- Existing Fabric workspace on an enabled capacity. The repository never creates or deletes a workspace.
- Runtime workspace/capacity references supplied through notebook parameters or environment variables.
- Contributor-equivalent permission for item create/update and notebook execution.
- Fabric Spark runtime with Delta Lake and `notebookutils`.
- Warehouse SQL endpoint and KQL query URI supplied at runtime when those deployment stages are enabled.
- Appropriate Entra permissions for Fabric item APIs; tokens are acquired only through runtime identity.

## Optional services

- Azure Digital Twins instance and data-owner authorization for notebook 14. The endpoint is runtime-only.
- Target support for TMDL/PBIR item definitions.
- Target support for Data Agent/Fabric app definition APIs if conditional deployment is enabled.

## Manual boundaries

Authentication, consent, target security controls, unsupported preview APIs, and app audience publication can require manual action. See `manual-fabric-steps.md` and `api-support-matrix.md` for exact fallbacks and impact.
