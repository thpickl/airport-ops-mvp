# Azure Digital Twins Portable Artifacts

> **Synthetic demonstration only.** No target endpoint is stored and no deployment occurs unless notebook 14 receives an approved runtime endpoint with `dry_run = False`.

## Contents

- `dtdl/`: fifteen DTDL v2 interfaces with stable `dtmi:com:fictionalairport:*;1` IDs, including Airport, Flight, Queue, BaggageAsset, Asset, EnergyMeter, MaintenanceWorkOrder, and Incident.
- `instances/sample-twins.json`: one deterministic sample per DTDL v2 interface using `SYN-TWIN-` identifiers.
- `relationships/sample-relationships.json`: deterministic graph-edge samples.
- `mapping.md`: DTDL-to-Lakehouse/Warehouse lineage.

Notebook `04_Generate_Physical_Spatial_Context` creates the configurable synthetic physical graph in `bronze_twin_relationships`; static JSON is a compact import sample and never represents a real airport layout.

## Parameterized deployment

1. Provision a private, governed Azure Digital Twins instance outside this repository.
2. Run `14_Deploy_Digital_Twin` with `dry_run = True` to validate models and graph endpoints.
3. Supply `digital_twins_endpoint` at runtime and run with `dry_run = False`.
4. The notebook reuses byte-equivalent immutable models, creates missing models, and fails version collisions.
5. Twins and relationships are upserted idempotently after model validation.

Azure permissions, endpoint names, tenant IDs, and live synchronization are intentionally absent from source. Deployment results are written to `digital_twin_deployment_results` when a Lakehouse is available.

## Safety boundary

The graph is descriptive and advisory. It must not issue commands to ATC, A-SMGCS, AODB, BHS, BMS, aircraft, or safety-of-flight systems. Any consequential recommendation remains subject to human approval.
