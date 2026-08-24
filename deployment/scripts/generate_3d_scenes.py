from __future__ import annotations

import argparse
import json
import struct
import uuid
from pathlib import Path
from typing import Any

import digital_twin


ROOT = Path(__file__).resolve().parents[2]
DIGITAL_TWIN_ROOT = ROOT / "digital-twin"
SCENES_ROOT = DIGITAL_TWIN_ROOT / "3d-scenes"
MODELS_ROOT = SCENES_ROOT / "models"
TWINS_PATH = DIGITAL_TWIN_ROOT / "instances" / "scene-twins.json"
RELATIONSHIPS_PATH = DIGITAL_TWIN_ROOT / "relationships" / "scene-relationships.json"
PILOT_TWINS_PATH = DIGITAL_TWIN_ROOT / "instances" / "scene-pilot-cdg-twins.json"
PILOT_RELATIONSHIPS_PATH = (
    DIGITAL_TWIN_ROOT / "relationships" / "scene-pilot-cdg-relationships.json"
)
MANIFEST_PATH = SCENES_ROOT / "manifest.json"
ESTATE_PATH = DIGITAL_TWIN_ROOT / "estate.json"

# Kinds bound to an Eventhouse source use the ;2 interface, which adds observed state.
MODEL_IDS = {
    "Airport": "dtmi:com:fictionalairport:Airport;1",
    "Terminal": "dtmi:com:fictionalairport:Terminal;2",
    "Zone": "dtmi:com:fictionalairport:Zone;1",
    "Checkpoint": "dtmi:com:fictionalairport:Checkpoint;2",
    "Gate": "dtmi:com:fictionalairport:Gate;2",
    "Stand": "dtmi:com:fictionalairport:Stand;1",
    "MaintenanceAsset": "dtmi:com:fictionalairport:MaintenanceAsset;2",
    "EnergyMeter": "dtmi:com:fictionalairport:EnergyMeter;2",
}

CHECKPOINTS_PER_TERMINAL = 4
CHECKPOINT_NAMES = {1: "Check-in", 2: "Security", 3: "Immigration", 4: "Boarding"}

# Checkpoint and meter identifiers must match the producer's derivation so they join in the Eventhouse.
CHECKPOINT_ID = "{terminal_id}-CP{number}"
METER_ID = "MTR-{gate_id}"
METER_ASSET_TYPE = "EnergyMeter"
SERVICE_INTERVAL_HOURS = 720

COLORS = {
    "Airport": [0.32, 0.36, 0.39, 1.0],
    "Terminal": [0.11, 0.47, 0.64, 1.0],
    "Zone": [0.16, 0.68, 0.63, 1.0],
    "Checkpoint": [0.95, 0.75, 0.18, 1.0],
    "Gate": [0.91, 0.38, 0.16, 1.0],
    "Stand": [0.48, 0.53, 0.57, 1.0],
    "MaintenanceAsset": [0.78, 0.16, 0.20, 1.0],
    "EnergyMeter": [0.25, 0.66, 0.25, 1.0],
}


def twin_id(kind: str, business_key: str) -> str:
    return f"{kind.lower()}-{business_key}"


def twin(kind: str, business_key: str, properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "$dtId": twin_id(kind, business_key),
        "$metadata": {"$model": MODEL_IDS[kind]},
        **properties,
    }


def relationship(source: str, name: str, target: str) -> dict[str, str]:
    relationship_id = "SYN-SCENE-REL-" + str(
        uuid.uuid5(uuid.NAMESPACE_URL, f"{source}|{name}|{target}")
    )
    return {
        "$relationshipId": relationship_id,
        "$sourceId": source,
        "$relationshipName": name,
        "$targetId": target,
    }


def add_element(
    elements: list[dict[str, Any]],
    kind: str,
    business_key: str,
    translation: list[float],
    scale: list[float],
) -> None:
    identifier = twin_id(kind, business_key)
    elements.append(
        {
            "kind": kind,
            "modelId": MODEL_IDS[kind],
            "twinId": identifier,
            "meshName": identifier,
            "translation": translation,
            "scale": scale,
        }
    )


def build_airport(
    airport: dict[str, Any], estate: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, Any]]:
    code = airport["iata_code"]
    airport_id = airport["airport_id"]
    twins: list[dict[str, Any]] = []
    relationships: list[dict[str, str]] = []
    elements: list[dict[str, Any]] = []

    airport_twin_id = twin_id("Airport", airport_id)
    twins.append(
        twin(
            "Airport",
            airport_id,
            {
                "airportId": airport_id,
                "iataCode": code,
                "airportName": airport["airport_name"],
                "isSynthetic": False,
            },
        )
    )
    add_element(elements, "Airport", airport_id, [0.0, -0.2, 0.0], [12.0, 0.2, 8.0])

    terminal_x: dict[str, float] = {}
    terminal_zones: dict[str, list[dict[str, Any]]] = {}
    for index, terminal in enumerate(estate["terminals_by_airport"].get(airport_id, [])):
        terminal_id = terminal["terminal_id"]
        terminal_twin_id = twin_id("Terminal", terminal_id)
        position_x = -4.0 if index == 0 else 4.0
        terminal_x[terminal_id] = position_x
        twins.append(
            twin(
                "Terminal",
                terminal_id,
                {
                    "terminalId": terminal_id,
                    "terminalCode": terminal["terminal_code"],
                    "floorCount": int(terminal["floor_count"]),
                    "isSynthetic": True,
                },
            )
        )
        add_element(elements, "Terminal", terminal_id, [position_x, 0.45, 0.0], [3.2, 0.45, 2.6])
        relationships.append(relationship(airport_twin_id, "contains", terminal_twin_id))

        zones = estate["zones_by_terminal"].get(terminal_id, [])
        terminal_zones[terminal_id] = zones
        for zone_index, zone in enumerate(zones):
            zone_id = zone["zone_id"]
            zone_z = -1.25 if zone_index == 0 else 1.25
            twins.append(
                twin(
                    "Zone",
                    zone_id,
                    {
                        "zoneId": zone_id,
                        "zoneType": zone["zone_type"],
                        "floorLevel": int(zone["floor_level"]),
                        "isSynthetic": True,
                    },
                )
            )
            add_element(elements, "Zone", zone_id, [position_x, 1.0, zone_z], [2.7, 0.08, 1.0])
            relationships.append(
                relationship(terminal_twin_id, "containsZones", twin_id("Zone", zone_id))
            )

        for number in range(1, CHECKPOINTS_PER_TERMINAL + 1):
            checkpoint_id = CHECKPOINT_ID.format(terminal_id=terminal_id, number=number)
            zone = zones[0] if number <= 2 else zones[-1]
            zone_z = -1.25 if number <= 2 else 1.25
            twins.append(
                twin(
                    "Checkpoint",
                    checkpoint_id,
                    {
                        "checkpointId": checkpoint_id,
                        "checkpointCode": f"CP{number}",
                        "checkpointName": f"Synthetic {CHECKPOINT_NAMES[number]}",
                        "isSynthetic": True,
                    },
                )
            )
            add_element(
                elements,
                "Checkpoint",
                checkpoint_id,
                [position_x - 1.05 + ((number - 1) % 2) * 2.1, 1.4, zone_z],
                [0.45, 0.4, 0.45],
            )
            relationships.append(
                relationship(
                    twin_id("Zone", zone["zone_id"]),
                    "containsCheckpoints",
                    twin_id("Checkpoint", checkpoint_id),
                )
            )

    for terminal in estate["terminals_by_airport"].get(airport_id, []):
        terminal_id = terminal["terminal_id"]
        position_x = terminal_x[terminal_id]
        zones = terminal_zones[terminal_id]
        secure_zone_twin_id = twin_id("Zone", zones[-1]["zone_id"])
        gates = [
            gate
            for gate in estate["gates_by_airport"].get(airport_id, [])
            if gate["terminal_code"] == terminal["terminal_code"]
        ]
        for gate_index, gate in enumerate(gates):
            gate_id = gate["gate_id"]
            gate_twin_id = twin_id("Gate", gate_id)
            z = -1.6 + gate_index * 1.6
            twins.append(
                twin(
                    "Gate",
                    gate_id,
                    {
                        "gateId": gate_id,
                        "gateCode": gate["gate_code"],
                        "gateType": gate["gate_type"],
                        "isSynthetic": True,
                    },
                )
            )
            add_element(elements, "Gate", gate_id, [position_x + 2.6, 0.5, z], [0.5, 0.3, 0.5])
            relationships.extend(
                [
                    relationship(twin_id("Terminal", terminal_id), "containsGates", gate_twin_id),
                    relationship(gate_twin_id, "locatedIn", twin_id("Terminal", terminal_id)),
                ]
            )

            for stand in estate["stands_by_gate"].get(gate_id, []):
                stand_id = stand["stand_id"]
                twins.append(
                    twin(
                        "Stand",
                        stand_id,
                        {
                            "standId": stand_id,
                            "standName": stand["stand_name"],
                            "isSynthetic": True,
                        },
                    )
                )
                add_element(elements, "Stand", stand_id, [position_x + 4.1, 0.25, z], [0.9, 0.12, 0.9])
                relationships.append(
                    relationship(gate_twin_id, "serves", twin_id("Stand", stand_id))
                )

            gate_assets = estate["assets_by_gate"].get(gate_id, [])
            meter_id = METER_ID.format(gate_id=gate_id)
            meter_twin_id = twin_id("EnergyMeter", meter_id)
            twins.append(
                twin(
                    "EnergyMeter",
                    meter_id,
                    {
                        "assetId": meter_id,
                        "meterKind": "Electricity",
                        "unit": "kWh",
                        "isSynthetic": True,
                    },
                )
            )
            add_element(
                elements, "EnergyMeter", meter_id,
                [position_x + 3.15, 0.8, z], [0.16, 0.5, 0.16],
            )
            relationships.append(
                relationship(meter_twin_id, "locatedIn", secure_zone_twin_id)
            )

            maintenance = [a for a in gate_assets if a["asset_type"] != METER_ASSET_TYPE]
            for asset_index, asset in enumerate(maintenance):
                asset_id = asset["asset_id"]
                asset_twin_id = twin_id("MaintenanceAsset", asset_id)
                twins.append(
                    twin(
                        "MaintenanceAsset",
                        asset_id,
                        {
                            "assetId": asset_id,
                            "assetType": asset["asset_type"],
                            "criticality": asset["criticality"],
                            "isSynthetic": True,
                            "maintenanceClass": asset["asset_class"],
                            "serviceIntervalHours": SERVICE_INTERVAL_HOURS,
                        },
                    )
                )
                add_element(
                    elements, "MaintenanceAsset", asset_id,
                    [position_x + 1.7 + asset_index * 0.22, 1.15, z], [0.16, 0.5, 0.16],
                )
                relationships.extend(
                    [
                        relationship(secure_zone_twin_id, "containsAssets", asset_twin_id),
                        relationship(asset_twin_id, "locatedIn", secure_zone_twin_id),
                    ]
                )
                relationships.append(
                    relationship(asset_twin_id, "monitoredBy", meter_twin_id)
                )
    scene = {
        "sceneId": f"airport-{code.lower()}",
        "name": airport["airport_name"],
        "description": "Synthetic schematic airport scene; not a real operational layout.",
        "airportId": airport_id,
        "iataCode": code,
        "latitude": airport["latitude"],
        "longitude": airport["longitude"],
        "glbBlobPath": f"models/{code.lower()}-airport.glb",
        "expectedTwinCount": len(twins),
        "expectedRelationshipCount": len(relationships),
        "elements": elements,
    }
    return twins, relationships, scene


def cube_geometry() -> tuple[bytes, int, int]:
    positions = [
        -0.5, -0.5, 0.5, 0.5, -0.5, 0.5, 0.5, 0.5, 0.5, -0.5, 0.5, 0.5,
        0.5, -0.5, -0.5, -0.5, -0.5, -0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5,
        -0.5, -0.5, -0.5, -0.5, -0.5, 0.5, -0.5, 0.5, 0.5, -0.5, 0.5, -0.5,
        0.5, -0.5, 0.5, 0.5, -0.5, -0.5, 0.5, 0.5, -0.5, 0.5, 0.5, 0.5,
        -0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, -0.5, -0.5, 0.5, -0.5,
        -0.5, -0.5, -0.5, 0.5, -0.5, -0.5, 0.5, -0.5, 0.5, -0.5, -0.5, 0.5,
    ]
    normals = (
        [0.0, 0.0, 1.0] * 4
        + [0.0, 0.0, -1.0] * 4
        + [-1.0, 0.0, 0.0] * 4
        + [1.0, 0.0, 0.0] * 4
        + [0.0, 1.0, 0.0] * 4
        + [0.0, -1.0, 0.0] * 4
    )
    indices = [
        0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7, 8, 9, 10, 8, 10, 11,
        12, 13, 14, 12, 14, 15, 16, 17, 18, 16, 18, 19, 20, 21, 22, 20, 22, 23,
    ]
    position_bytes = struct.pack("<" + "f" * len(positions), *positions)
    normal_bytes = struct.pack("<" + "f" * len(normals), *normals)
    index_bytes = struct.pack("<" + "H" * len(indices), *indices)
    return position_bytes + normal_bytes + index_bytes, len(position_bytes), len(normal_bytes)


def build_glb(scene: dict[str, Any]) -> bytes:
    binary, position_length, normal_length = cube_geometry()
    index_offset = position_length + normal_length
    materials = [
        {
            "name": kind,
            "pbrMetallicRoughness": {
                "baseColorFactor": color,
                "metallicFactor": 0.0,
                "roughnessFactor": 0.72,
            },
        }
        for kind, color in COLORS.items()
    ]
    material_index = {kind: index for index, kind in enumerate(COLORS)}
    meshes = [
        {
            "name": element["meshName"],
            "primitives": [
                {
                    "attributes": {"POSITION": 0, "NORMAL": 1},
                    "indices": 2,
                    "material": material_index[element["kind"]],
                }
            ],
            "extras": {"twinId": element["twinId"], "synthetic": True},
        }
        for element in scene["elements"]
    ]
    nodes = [
        {
            "name": element["meshName"],
            "mesh": index,
            "translation": element["translation"],
            "scale": element["scale"],
            "extras": {"twinId": element["twinId"], "kind": element["kind"]},
        }
        for index, element in enumerate(scene["elements"])
    ]
    gltf = {
        "asset": {"version": "2.0", "generator": "fabric-airport-ops-mvp"},
        "scene": 0,
        "scenes": [{"name": scene["name"], "nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": position_length, "target": 34962},
            {"buffer": 0, "byteOffset": position_length, "byteLength": normal_length, "target": 34962},
            {"buffer": 0, "byteOffset": index_offset, "byteLength": len(binary) - index_offset, "target": 34963},
        ],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": 24, "type": "VEC3", "min": [-0.5, -0.5, -0.5], "max": [0.5, 0.5, 0.5]},
            {"bufferView": 1, "componentType": 5126, "count": 24, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5123, "count": 36, "type": "SCALAR", "min": [0], "max": [23]},
        ],
        "extras": {
            "sceneId": scene["sceneId"],
            "airportId": scene["airportId"],
            "synthetic": True,
            "disclaimer": "Illustrative synthetic geometry; not a real airport layout.",
        },
    }
    json_chunk = json.dumps(gltf, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)
    binary += b"\x00" * ((4 - len(binary) % 4) % 4)
    total_length = 12 + 8 + len(json_chunk) + 8 + len(binary)
    return b"".join(
        [
            struct.pack("<III", 0x46546C67, 2, total_length),
            struct.pack("<II", len(json_chunk), 0x4E4F534A),
            json_chunk,
            struct.pack("<II", len(binary), 0x004E4942),
            binary,
        ]
    )


def parse_glb(value: bytes) -> dict[str, Any]:
    magic, version, total_length = struct.unpack_from("<III", value, 0)
    if magic != 0x46546C67 or version != 2 or total_length != len(value):
        raise ValueError("Invalid GLB header")
    json_length, json_type = struct.unpack_from("<II", value, 12)
    if json_type != 0x4E4F534A:
        raise ValueError("GLB JSON chunk is missing")
    return json.loads(value[20 : 20 + json_length].decode("utf-8"))


def load_estate() -> dict[str, Any]:
    """Index the estate snapshot so scene identifiers match Eventhouse business keys."""
    estate = json.loads(ESTATE_PATH.read_text(encoding="utf-8"))
    index: dict[str, Any] = {"airports": estate["airports"]}
    for name, key, source in (
        ("terminals_by_airport", "airport_id", "terminals"),
        ("zones_by_terminal", "terminal_id", "zones"),
        ("gates_by_airport", "airport_id", "gates"),
        ("stands_by_gate", "gate_id", "stands"),
        ("assets_by_gate", "gate_id", "assets"),
    ):
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in estate[source]:
            grouped.setdefault(row[key], []).append(row)
        index[name] = grouped
    return index


def build_artifacts() -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, Any], dict[str, bytes]]:
    config = json.loads((ROOT / "config" / "demo_config.json").read_text(encoding="utf-8"))
    estate = load_estate()
    airports = sorted(estate["airports"], key=lambda row: row["airport_id"])
    if len(airports) != config["airport_count"]:
        raise ValueError("Configured airport count does not match the exported estate")

    all_twins: list[dict[str, Any]] = []
    all_relationships: list[dict[str, str]] = []
    scenes: list[dict[str, Any]] = []
    glbs: dict[str, bytes] = {}
    for airport in airports:
        twins, relationships, scene = build_airport(airport, estate)
        all_twins.extend(twins)
        all_relationships.extend(relationships)
        scenes.append(scene)
        glbs[scene["glbBlobPath"]] = build_glb(scene)

    manifest = {
        "schemaVersion": "1.0",
        "generatedFrom": ["config/demo_config.json", "digital-twin/estate.json", "digital-twin/dtdl"],
        "isSynthetic": True,
        "spatialDisclaimer": config["spatial_disclaimer"],
        "expectedTwinCount": len(all_twins),
        "expectedRelationshipCount": len(all_relationships),
        "sceneCount": len(scenes),
        "scenes": scenes,
    }
    return all_twins, all_relationships, manifest, glbs


def serialized_artifacts() -> dict[Path, bytes]:
    twins, relationships, manifest, glbs = build_artifacts()
    pilot_scene = next(scene for scene in manifest["scenes"] if scene["iataCode"] == "CDG")
    pilot_twin_ids = {element["twinId"] for element in pilot_scene["elements"]}
    pilot_twins = [twin for twin in twins if twin["$dtId"] in pilot_twin_ids]
    pilot_relationships = [
        relationship
        for relationship in relationships
        if relationship["$sourceId"] in pilot_twin_ids
        and relationship["$targetId"] in pilot_twin_ids
    ]
    artifacts = {
        TWINS_PATH: (json.dumps(twins, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"),
        RELATIONSHIPS_PATH: (json.dumps(relationships, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"),
        PILOT_TWINS_PATH: (json.dumps(pilot_twins, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"),
        PILOT_RELATIONSHIPS_PATH: (json.dumps(pilot_relationships, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"),
        MANIFEST_PATH: (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }
    artifacts.update({SCENES_ROOT / path: value for path, value in glbs.items()})
    return artifacts


def validate_generated() -> None:
    package = digital_twin.load_package(
        DIGITAL_TWIN_ROOT, "scene-twins.json", "scene-relationships.json"
    )
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if (
        len(package.twins) != manifest["expectedTwinCount"]
        or len(package.relationships) != manifest["expectedRelationshipCount"]
    ):
        raise ValueError("Scene twin or relationship count does not match the manifest")
    if manifest["sceneCount"] != len(manifest["scenes"]):
        raise ValueError("Manifest scene count is inconsistent")
    pilot = digital_twin.load_package(
        DIGITAL_TWIN_ROOT,
        "scene-pilot-cdg-twins.json",
        "scene-pilot-cdg-relationships.json",
    )
    pilot_scene = next(scene for scene in manifest["scenes"] if scene["iataCode"] == "CDG")
    if len(pilot.twins) != pilot_scene["expectedTwinCount"]:
        raise ValueError("CDG pilot twin count does not match its scene")
    for scene in manifest["scenes"]:
        gltf = parse_glb((SCENES_ROOT / scene["glbBlobPath"]).read_bytes())
        mesh_names = {mesh["name"] for mesh in gltf["meshes"]}
        expected_names = {element["meshName"] for element in scene["elements"]}
        if mesh_names != expected_names or len(mesh_names) != len(scene["elements"]):
            raise ValueError(f"Scene {scene['sceneId']} does not expose its mapped meshes")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic airport 3D Scenes assets")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    artifacts = serialized_artifacts()
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, value in artifacts.items() if not path.exists() or path.read_bytes() != value]
        if stale:
            print("STALE: " + ", ".join(stale))
            return 1
    else:
        for path, value in artifacts.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
    validate_generated()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    print(
        f"3D_SCENES models={manifest['sceneCount']} "
        f"twins={manifest['expectedTwinCount']} "
        f"relationships={manifest['expectedRelationshipCount']} "
        f"elements={sum(len(scene['elements']) for scene in manifest['scenes'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())