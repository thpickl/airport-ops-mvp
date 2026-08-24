# Known Issues

- Deployment used authenticated Fabric, Power BI, OneLake, Warehouse SQL, and Data Agent REST APIs directly rather than a Fabric MCP server.
- The target supports native Data Agent configuration and publication. Native `FabricApp` is unsupported: the item API returns `InvalidItemType`.
- Rayfin is not treated as a verified native Fabric capability. Its module is disabled by default behind `enable_rayfin_module`.
- PBIR/TMDL definitions were normalized to the target schemas and deployed. Target-version drift remains a rerun risk and must be caught by definition retrieval and semantic/report binding checks.
- Warehouse three-part Lakehouse references require a compatible same-workspace SQL endpoint; otherwise materialize Gold with a governed pipeline while preserving `ops.vw_*` contracts.
- The Azure Digital Twins dev runtime is deployed in West Europe because Germany West Central is not supported for this resource type in the target subscription. Public network access remains enabled; private endpoint, DNS, and diagnostic-log integration require a separate governed network design.
- Persona security roles and views are deployed, but `security.principal_scope` is intentionally empty until governed Entra mappings are approved.
- The `enterprise` profile can create substantial passenger, booking, bag, scan, queue, and POS volumes. Use it only on appropriately governed capacity.
- All coordinates, codes, organizations, aircraft models, operations, incidents, financial proxies, and outcomes are fictional and unsuitable for real decisions.
