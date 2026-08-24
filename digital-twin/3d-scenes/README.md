# Azure Digital Twins 3D Scenes

This directory contains deterministic, synthetic 3D scene assets for all 18 airport reference anchors. The models are schematic demonstrations and do not represent real terminal layouts, security boundaries, navigation paths, infrastructure, or operations.

## Generated artifacts

- `models/*.glb`: one segmented glTF 2.0 binary scene per airport.
- `manifest.json`: scene metadata and the one-to-one mesh-name to twin-ID mapping contract.
- `../instances/scene-twins.json`: 630 DTDL-valid physical twins.
- `../relationships/scene-relationships.json`: 936 DTDL-valid graph relationships.

Regenerate and validate the package:

```powershell
python deployment/scripts/generate_3d_scenes.py
python deployment/scripts/generate_3d_scenes.py --check
```

The 3D Scenes Studio configuration file is created and maintained through the official Studio builder. Do not hand-edit it. Blob versioning and soft delete provide recovery for builder-managed configuration changes.