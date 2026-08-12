from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "reference"
OUTPUT = ROOT / "geospatial" / "azure-maps"
CONFIG = json.loads((ROOT / "config" / "demo_config.json").read_text(encoding="utf-8"))
AIRPORTS = json.loads((REFERENCE / "airports.json").read_text(encoding="utf-8"))["records"]
RNG = random.Random(CONFIG["random_seed"] + 1400)


def feature(identifier: str, properties: dict[str, Any], geometry_type: str, coordinates: Any) -> dict[str, Any]:
    return {
        "type": "Feature",
        "id": identifier,
        "properties": properties,
        "geometry": {"type": geometry_type, "coordinates": coordinates},
    }


def polygon(center_lon: float, center_lat: float, half_width: float, half_height: float) -> list[list[list[float]]]:
    ring = [
        [center_lon - half_width, center_lat - half_height],
        [center_lon + half_width, center_lat - half_height],
        [center_lon + half_width, center_lat + half_height],
        [center_lon - half_width, center_lat + half_height],
        [center_lon - half_width, center_lat - half_height],
    ]
    return [ring]


def synthetic_properties(**values: Any) -> dict[str, Any]:
    return {
        **values,
        "is_synthetic": True,
        "data_classification": "Synthetic master data",
        "geometry_disclaimer": "Illustrative synthetic geometry; not a real airport layout, boundary, route, or operational location.",
        "generator_version": CONFIG["generator_version"],
        "random_seed": CONFIG["random_seed"],
    }


def build_layers() -> dict[str, dict[str, Any]]:
    layers: dict[str, list[dict[str, Any]]] = {
        "airports.geojson": [], "operating_regions.geojson": [], "terminals.geojson": [],
        "zones.geojson": [], "gates.geojson": [], "stands.geojson": [], "routes.geojson": [],
        "passenger_flows.geojson": [], "baggage_flows.geojson": [], "assets.geojson": [],
        "energy.geojson": [], "incidents.geojson": [],
    }
    for airport_index, airport in enumerate(AIRPORTS):
        airport_id = airport["airport_id"]
        longitude, latitude = float(airport["longitude"]), float(airport["latitude"])
        layers["airports.geojson"].append(feature(
            "airport-" + airport_id.lower(),
            {
                "airport_id": airport_id, "iata_code": airport["iata_code"], "icao_code": airport["icao_code"],
                "airport_name": airport["airport_name"], "country": airport["country"],
                "iana_time_zone": airport["iana_time_zone"], "is_synthetic": False,
                "reference_anchor_only": True,
                "fictional_group_assignment": True, "data_classification": "Synthetic master data",
                "geometry_disclaimer": "Public approximate airport reference point; no operational layout, boundary, or ownership is represented.",
                "source_name": airport["source_name"], "source_url": airport["source_url"],
                "source_as_of_date": airport["source_as_of_date"],
            }, "Point", [longitude, latitude]))

        terminal_centers: dict[str, tuple[float, float]] = {}
        for terminal_number in range(1, CONFIG["terminals_per_airport"] + 1):
            terminal_id = f"{airport_id}-T{terminal_number}"
            terminal_lon = longitude + (-0.003 if terminal_number == 1 else 0.003)
            terminal_lat = latitude
            terminal_centers[terminal_id] = (terminal_lon, terminal_lat)
            layers["terminals.geojson"].append(feature(
                "terminal-" + terminal_id.lower(), synthetic_properties(
                    airport_id=airport_id, terminal_id=terminal_id, feature_type="Terminal"),
                "Polygon", polygon(terminal_lon, terminal_lat, 0.0025, 0.0021)))
            for zone_number in range(1, CONFIG["zones_per_terminal"] + 1):
                zone_id = f"{terminal_id}-Z{zone_number}"
                zone_lon = terminal_lon
                zone_lat = terminal_lat + (-0.001 if zone_number == 1 else 0.001)
                layers["zones.geojson"].append(feature(
                    "zone-" + zone_id.lower(), synthetic_properties(
                        airport_id=airport_id, terminal_id=terminal_id, zone_id=zone_id,
                        feature_type="Zone", zone_type="PublicProcessing" if zone_number == 1 else "SecureOperations"),
                    "Polygon", polygon(zone_lon, zone_lat, 0.0019, 0.0008)))

            passenger_from = [terminal_lon - 0.0015, terminal_lat - 0.0008]
            passenger_to = [terminal_lon + 0.0015, terminal_lat + 0.0008]
            layers["passenger_flows.geojson"].append(feature(
                f"passenger-flow-{terminal_id.lower()}", synthetic_properties(
                    airport_id=airport_id, terminal_id=terminal_id, flow_type="Departures", illustrative_only=True),
                "LineString", [passenger_from, [terminal_lon, terminal_lat], passenger_to]))

        for gate_number in range(1, CONFIG["gates_per_airport"] + 1):
            terminal_number = 1 if gate_number <= 3 else 2
            terminal_id = f"{airport_id}-T{terminal_number}"
            terminal_lon, terminal_lat = terminal_centers[terminal_id]
            gate_id, stand_id = f"{airport_id}-G{gate_number}", f"{airport_id}-S{gate_number}"
            gate_lat = terminal_lat + (gate_number - 3.5) * 0.00035
            gate_lon, stand_lon = terminal_lon, terminal_lon + 0.0015
            layers["gates.geojson"].append(feature(
                "gate-" + gate_id.lower(), synthetic_properties(
                    airport_id=airport_id, terminal_id=terminal_id, gate_id=gate_id,
                    stand_id=stand_id, feature_type="Gate"), "Point", [gate_lon, gate_lat]))
            layers["stands.geojson"].append(feature(
                "stand-" + stand_id.lower(), synthetic_properties(
                    airport_id=airport_id, terminal_id=terminal_id, gate_id=gate_id,
                    stand_id=stand_id, feature_type="Stand"), "Point", [stand_lon, gate_lat]))
            intensity = round(0.55 + ((airport_index * 7 + gate_number * 11 + CONFIG["random_seed"]) % 40) / 100, 2)
            layers["energy.geojson"].append(feature(
                "energy-" + gate_id.lower(), synthetic_properties(
                    airport_id=airport_id, terminal_id=terminal_id, gate_id=gate_id,
                    feature_type="EnergyHeatPoint", synthetic_intensity=intensity, unit="normalized proxy"),
                "Point", [gate_lon + 0.0003, gate_lat]))
            asset_id = f"SYN-AST-{airport['iata_code']}-{gate_number:03d}"
            layers["assets.geojson"].append(feature(
                "asset-" + asset_id.lower(), synthetic_properties(
                    airport_id=airport_id, terminal_id=terminal_id, gate_id=gate_id,
                    asset_id=asset_id, feature_type="OperationalAsset", illustrative_only=True),
                "Point", [gate_lon + 0.0006, gate_lat + 0.00015]))

        baggage_coordinates = [
            [terminal_centers[f"{airport_id}-T1"][0], latitude + 0.001],
            [longitude, latitude],
            [terminal_centers[f"{airport_id}-T2"][0], latitude - 0.001],
        ]
        layers["baggage_flows.geojson"].append(feature(
            "baggage-flow-" + airport_id.lower(), synthetic_properties(
                airport_id=airport_id, flow_type="IllustrativeOutboundBaggage", illustrative_only=True),
            "LineString", baggage_coordinates))

        for incident_number in range(1, 4):
            angle_marker = airport_index * 3 + incident_number
            incident_lon = longitude + (RNG.random() - 0.5) * 0.005
            incident_lat = latitude + (RNG.random() - 0.5) * 0.004
            incident_id = f"SYN-MAP-INC-{airport['iata_code']}-{incident_number:02d}"
            layers["incidents.geojson"].append(feature(
                "incident-" + incident_id.lower(), synthetic_properties(
                    airport_id=airport_id, incident_id=incident_id,
                    severity=["Low", "Medium", "High"][angle_marker % 3], feature_type="Incident"),
                "Point", [round(incident_lon, 7), round(incident_lat, 7)]))

        destination = AIRPORTS[(airport_index + 1) % len(AIRPORTS)]
        route_id = f"SYN-ROUTE-{airport['iata_code']}-{destination['iata_code']}"
        layers["routes.geojson"].append(feature(
            "route-" + route_id.lower(), synthetic_properties(
                route_id=route_id, origin_airport_id=airport_id,
                destination_airport_id=destination["airport_id"], feature_type="SyntheticRoute",
                illustrative_only=True, schedule_representation=False),
            "LineString", [[longitude, latitude], [float(destination["longitude"]), float(destination["latitude"])]]))

    for region_name in sorted({airport["country"] for airport in AIRPORTS}):
        region_airports = [airport for airport in AIRPORTS if airport["country"] == region_name]
        longitudes = [float(airport["longitude"]) for airport in region_airports]
        latitudes = [float(airport["latitude"]) for airport in region_airports]
        min_lon, max_lon = min(longitudes) - 0.35, max(longitudes) + 0.35
        min_lat, max_lat = min(latitudes) - 0.25, max(latitudes) + 0.25
        region_id = f"SYN-REG-{region_name.upper()}"
        region_ring = [[min_lon, min_lat], [max_lon, min_lat], [max_lon, max_lat], [min_lon, max_lat], [min_lon, min_lat]]
        layers["operating_regions.geojson"].append(feature(
            "region-" + region_id.lower(), synthetic_properties(
                region_id=region_id, region_name=region_name, feature_type="IllustrativeOperatingRegionView",
                is_administrative_boundary=False, fictional_portfolio_relationship=True),
            "Polygon", [region_ring]))

    return {name: {"type": "FeatureCollection", "name": name.removesuffix(".geojson"), "features": features} for name, features in layers.items()}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for existing in OUTPUT.glob("*.geojson"):
        existing.unlink()
    manifest: dict[str, Any] = {"schema_version": "2.0", "files": {}}
    for file_name, collection in build_layers().items():
        path = OUTPUT / file_name
        path.write_text(json.dumps(collection, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        manifest["files"][file_name] = {
            "feature_count": len(collection["features"]),
            "geometry_types": sorted({item["geometry"]["type"] for item in collection["features"]}),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    (OUTPUT / "geojson-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Generated", len(manifest["files"]), "GeoJSON layers for", len(AIRPORTS), "airports")


if __name__ == "__main__":
    main()
