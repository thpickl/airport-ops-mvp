"""Deterministic generator for the fictional airport reference snapshot.

Used when public reference data cannot be redistributed (reference_mode=fictional).
Produces 18 fully synthetic airports with the same region distribution and valid
IANA time zones as the public snapshot, but non-real names, codes, and coordinates.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "config" / "reference" / "airport-anchors.fictional.json"

# Fictional country-level centroids only; not real airport coordinates.
REGIONS = [
    ("France", "FR", "Europe/Paris", 46.6, 2.2, 6),
    ("Italy", "IT", "Europe/Rome", 42.5, 12.5, 5),
    ("Portugal", "PT", "Europe/Lisbon", 39.5, -8.0, 5),
    ("Jordan", "JO", "Asia/Amman", 31.2, 36.3, 2),
]


def build_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    index = 0
    for region, code, time_zone, center_lat, center_lon, count in REGIONS:
        for local_index in range(count):
            index += 1
            latitude = round(center_lat + (local_index - (count - 1) / 2) * 0.85, 4)
            longitude = round(center_lon + (local_index - (count - 1) / 2) * 1.15, 4)
            records.append({
                "airport_reference_id": f"SYN-REF-AP-{index:02d}",
                "name": f"Synthetic {region} Airport {local_index + 1:02d}",
                "city": f"Synthetic {region} City {local_index + 1:02d}",
                "country": region,
                "country_code": code,
                "region": region,
                "iata_code": f"Q{index:02d}",
                "icao_code": f"ZZ{index:02d}",
                "latitude": latitude,
                "longitude": longitude,
                "elevation_ft": 100 + index * 5,
                "time_zone": time_zone,
                "is_synthetic": True,
                "reference_anchor_only": False,
            })
    return records


def main() -> None:
    records = build_records()
    payload = {
        "schema_version": "1.0",
        "snapshot_date": "2026-08-08",
        "validation_status": "FICTIONAL_GENERATED",
        "ownership_assertion": "None. Fully fictional demonstration portfolio; no real airports are referenced.",
        "operational_data_policy": "No real operational data is included or implied.",
        "sources": [
            {
                "source_id": "FICTIONAL-GENERATOR-2026-08-08",
                "name": "Deterministic Fictional Airport Anchor Generator",
                "url": "repo://config/reference/generate_fictional_anchors.py",
                "retrieved_utc": "2026-08-08T00:00:00Z",
                "usage_notes": "All names, codes, and coordinates are synthetic and safe for redistribution.",
                "fields": ["name", "city", "country_code", "iata_code", "icao_code", "latitude", "longitude", "elevation_ft", "time_zone"],
            }
        ],
        "records": records,
        "field_provenance": {field: "FICTIONAL-GENERATOR-2026-08-08" for field in ["name", "city", "country_code", "iata_code", "icao_code", "latitude", "longitude", "elevation_ft", "time_zone"]},
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(records)} fictional airport anchors at {OUTPUT}")


if __name__ == "__main__":
    main()
