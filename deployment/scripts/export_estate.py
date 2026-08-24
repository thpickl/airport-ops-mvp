"""Export the Lakehouse reference estate to a committed, deterministic JSON document.

The 3D scene generator must stay offline and reproducible, so it cannot query Fabric
directly. This script snapshots the estate that the streaming producer also emits from,
which is what makes scene twin identifiers join to Eventhouse business keys.

    python -u deployment/scripts/export_estate.py [--server HOST] [--database NAME]
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import struct
import subprocess

import pyodbc

ROOT = pathlib.Path(__file__).resolve().parents[2]
ESTATE_PATH = ROOT / "digital-twin" / "estate.json"

DEFAULT_DATABASE = "AirportOpsLakehouse"

QUERIES = {
    "airports": """
        SELECT airport_id, iata_code, airport_name, latitude, longitude
        FROM dim_airport ORDER BY airport_id""",
    "terminals": """
        SELECT terminal_id, airport_id, terminal_code, terminal_name, floor_count
        FROM dim_terminal ORDER BY terminal_id""",
    "zones": """
        SELECT DISTINCT zone_id, terminal_id, airport_id, zone_code, zone_name,
               zone_type, floor_level
        FROM bronze_terminal_zones ORDER BY zone_id""",
    "gates": """
        SELECT gate_id, airport_id, gate_code, terminal AS terminal_code, gate_type
        FROM dim_gate ORDER BY gate_id""",
    "stands": """
        SELECT stand_id, airport_id, terminal_id, gate_id, stand_name
        FROM dim_stand ORDER BY stand_id""",
    "assets": """
        SELECT asset_id, airport_id, terminal_id, zone_id, gate_id, asset_type,
               asset_class, criticality
        FROM dim_asset ORDER BY asset_id""",
}


def connect(server: str, database: str) -> pyodbc.Connection:
    token = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://database.windows.net",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True, shell=os.name == "nt",
    ).stdout.strip()
    raw = token.encode("utf-16-le")
    return pyodbc.connect(
        f"Driver={{ODBC Driver 17 for SQL Server}};Server={server};Database={database};"
        "Encrypt=yes;TrustServerCertificate=no",
        attrs_before={1256: struct.pack(f"<I{len(raw)}s", len(raw), raw)},
        autocommit=True, timeout=300,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the Lakehouse reference estate")
    parser.add_argument("--server", default=os.environ.get("FABRIC_WAREHOUSE_SERVER", ""))
    parser.add_argument("--database", default=DEFAULT_DATABASE)
    args = parser.parse_args()
    if not args.server:
        parser.error("--server or FABRIC_WAREHOUSE_SERVER is required; "
                     "runtime endpoints are never committed to source.")

    estate: dict[str, object] = {
        "schemaVersion": "1.0",
        "source": f"{args.database} reference dimensions",
        "isSynthetic": True,
        "spatialDisclaimer": (
            "Airport anchors are public geographic reference points. All terminal, zone, "
            "gate, stand, checkpoint and asset records are synthetic."
        ),
    }

    with connect(args.server, args.database) as connection:
        cursor = connection.cursor()
        for name, statement in QUERIES.items():
            cursor.execute(statement)
            columns = [column[0] for column in cursor.description]
            rows = [
                {
                    column: (float(value) if isinstance(value, (int, float)) and
                             column in {"latitude", "longitude"} else value)
                    for column, value in zip(columns, row)
                }
                for row in cursor.fetchall()
            ]
            estate[name] = rows
            print(f"   {name:<12} {len(rows)}")

    ESTATE_PATH.write_text(
        json.dumps(estate, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8")
    print(f"wrote {ESTATE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
