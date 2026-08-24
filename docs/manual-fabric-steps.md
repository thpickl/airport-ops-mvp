# Unavoidable Platform Boundaries

Normal deployment is automated by notebooks `00`, `10`, and `11`. Manual UI configuration is not part of the expected runbook except for these boundaries:

1. **Authentication and authorization:** sign in with an identity that can access the existing workspace and capacity.
2. **Initial bootstrap availability:** make notebook `00_Deploy_Fabric_Items` and the repository bundle available through Fabric Git integration, an external item-definition call, or one initial import.
3. **Runtime parameters:** supply workspace ID and optional Warehouse/KQL/Azure Digital Twins endpoints at execution time. Do not write them into source.
4. **Data Agent access mappings:** the native Data Agent is published with governed instructions, 29 curated Warehouse views, and 13 curated KQL functions/views. `data-agent/definition.json` now allowlists 31 Warehouse views, so a redeployment is required to pick up the two scenario views. Assign users through approved workspace/tenant governance; do not add source elements outside the allowlists or select raw KQL tables.
5. **App publication/audiences:** this target rejects native `FabricApp` items. Use the deployed Power BI report directly or a supported target-specific app publishing experience; preserve `UNSUPPORTED` for the native item.
6. **Azure Digital Twins target:** the dev runtime is deployed and verified. Future environments still require explicit resource group, supported region, lifecycle, cost, RBAC, network, and endpoint approval before notebook `14_Deploy_Digital_Twin` or the local deployment adapter runs in apply mode.

Semantic model/report source is packaged as TMDL/PBIR and deployed by notebook 10 when the target accepts those definition formats. Warehouse SQL and Eventhouse KQL are executed by notebook 10, not copied into a UI.

See [deployment-runbook.md](deployment-runbook.md) and [api-support-matrix.md](api-support-matrix.md).
