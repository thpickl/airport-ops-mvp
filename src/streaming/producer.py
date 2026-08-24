"""Synthetic airport telemetry producer for the provisioned Event Hubs.

Publishes privacy-safe synthetic events whose JSON field names match the existing
Eventhouse ingestion mappings exactly. Each source in config/streaming_sources.json
names its own hub, raw KQL table, and ingestion mapping; there are eight.

Authentication is Microsoft Entra only: the namespace sets disableLocalAuth=true, so the
caller must hold Azure Event Hubs Data Sender. No connection string or key is used.

Reference identifiers are read from the Lakehouse SQL endpoint so that streamed events
reference the same airports, gates and terminals as the batch model. Nothing is invented.

    python -m src.streaming.producer --duration-seconds 120
    python -m src.streaming.producer --source flight --rate-multiplier 2 --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import struct
import subprocess
import sys
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = Path("config/streaming_sources.json")
CONFIG_TEMPLATE_PATH = Path("config/streaming_sources.example.json")
REFERENCE_CACHE = Path("config/streaming_reference_cache.json")
LAKEHOUSE_DATABASE = "AirportOpsLakehouse"

PLACEHOLDER = re.compile(r"\$\{([A-Z0-9_]+)\}")

LOGGER = logging.getLogger("fao.producer")


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'))
    LOGGER.setLevel(level.upper())
    LOGGER.handlers = [handler]


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} must be set; runtime endpoints are never committed to source.")
    return value


def warehouse_server() -> str:
    return require_env("FABRIC_WAREHOUSE_SERVER")


def _expand(value):
    """Resolve ${ENV_VAR} placeholders so no runtime identifier is stored in source."""
    if isinstance(value, dict):
        return {key: _expand(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand(item) for item in value]
    if isinstance(value, str):
        return PLACEHOLDER.sub(lambda match: require_env(match.group(1)), value)
    return value


def load_config() -> dict:
    path = CONFIG_PATH if CONFIG_PATH.exists() else CONFIG_TEMPLATE_PATH
    if not path.exists():
        raise SystemExit(f"Neither {CONFIG_PATH} nor {CONFIG_TEMPLATE_PATH} is present.")
    return _expand(json.loads(path.read_text(encoding="utf-8")))


def build_credential():
    """Entra credential for keyless Event Hubs access.

    The broad DefaultAzureCredential chain probes several unavailable sources and retries
    the CLI concurrently, which intermittently fails. Only the sources that work in this
    environment (env vars, managed identity, az CLI) are kept.
    """
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential(
        exclude_workload_identity_credential=True,
        exclude_shared_token_cache_credential=True,
        exclude_visual_studio_code_credential=True,
        exclude_powershell_credential=True,
        exclude_developer_cli_credential=True,
        exclude_interactive_browser_credential=True,
        exclude_broker_credential=True,
        process_timeout=60,
    )


# ---------------------------------------------------------------- reference data

def _sql_connection():
    import pyodbc

    token = subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://database.windows.net",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True, shell=os.name == "nt",
    ).stdout.strip()
    raw = token.encode("utf-16-le")
    return pyodbc.connect(
        f"Driver={{ODBC Driver 17 for SQL Server}};Server={warehouse_server()};"
        f"Database={LAKEHOUSE_DATABASE};Encrypt=yes;TrustServerCertificate=no",
        attrs_before={1256: struct.pack(f"<I{len(raw)}s", len(raw), raw)},
        timeout=120,
    )


REFERENCE_QUERIES = {
    "airports": "SELECT airport_id FROM dim_airport ORDER BY airport_id",
    "gates": "SELECT TOP 400 gate_id, airport_id FROM dim_gate ORDER BY gate_id",
    "terminals": "SELECT terminal_id, airport_id FROM dim_terminal ORDER BY terminal_id",
    "airlines": "SELECT airline_id FROM dim_airline ORDER BY airline_id",
    "routes": "SELECT TOP 200 route_id, airline_id, origin_airport_id FROM dim_route ORDER BY route_id",
    "flights": ("SELECT TOP 400 flight_event_id, airport_id, gate_id, airline_id "
                "FROM fact_flight_turnaround_events ORDER BY flight_event_id"),
    "assets": "SELECT TOP 400 asset_id, airport_id, asset_type FROM dim_asset ORDER BY asset_id",
    "outlets": ("SELECT TOP 200 outlet_id, airport_id, terminal_id "
                "FROM dim_retail_outlet ORDER BY outlet_id"),
    "products": "SELECT TOP 100 product_id FROM dim_retail_product ORDER BY product_id",
}


def refresh_reference() -> dict:
    """Pull real identifiers from the batch model so streamed events keep referential integrity."""
    LOGGER.info("refreshing reference identifiers from the Lakehouse SQL endpoint")
    reference: dict[str, list] = {}
    connection = _sql_connection()
    try:
        cursor = connection.cursor()
        for name, sql in REFERENCE_QUERIES.items():
            cursor.execute(sql)
            columns = [c[0] for c in cursor.description]
            reference[name] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            LOGGER.info(f"{name}: {len(reference[name])} rows")
    finally:
        connection.close()
    REFERENCE_CACHE.write_text(json.dumps(reference, indent=1), encoding="utf-8")
    return reference


def load_reference(refresh: bool) -> dict:
    if refresh or not REFERENCE_CACHE.exists():
        return refresh_reference()
    reference = json.loads(REFERENCE_CACHE.read_text(encoding="utf-8"))
    LOGGER.info(f"reference cache loaded ({ {k: len(v) for k, v in reference.items()} })")
    return reference


# ---------------------------------------------------------------- event builders

def _envelope(batch_id: str, sequence: int, payload: dict) -> dict:
    """Attach the identity/lineage fields every raw table mapping expects."""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["event_id"] = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{batch_id}:{sequence}"))
    payload["payload_hash"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    payload["batch_id"] = batch_id
    payload["is_synthetic"] = True
    return payload


def build_flight(rng: random.Random, reference: dict, now: datetime,
                 batch_id: str, sequence: int) -> dict:
    flight = rng.choice(reference["flights"])
    return _envelope(batch_id, sequence, {
        "event_timestamp": now.isoformat(),
        "airport_id": flight["airport_id"],
        "gate_id": flight["gate_id"],
        "airline_id": flight["airline_id"],
        "route_id": rng.choice(reference["routes"])["route_id"],
        "flight_event_id": flight["flight_event_id"],
        "event_type": rng.choice(["ArrivalActual", "DepartureActual", "GateAssigned", "Boarding"]),
        "delay_minutes": round(max(0.0, rng.gauss(8.0, 9.0)), 1),
        "turnaround_minutes": round(max(18.0, rng.gauss(48.0, 7.5)), 1),
        "passenger_count": int(max(40, rng.gauss(150, 38))),
    })


def build_turnaround(rng: random.Random, reference: dict, now: datetime,
                     batch_id: str, sequence: int) -> dict:
    flight = rng.choice(reference["flights"])
    tasks = ["Deboarding", "Cleaning", "Refuelling", "Catering", "Boarding"]
    index = sequence % len(tasks)
    return _envelope(batch_id, sequence, {
        "event_timestamp": now.isoformat(),
        "airport_id": flight["airport_id"],
        "gate_id": flight["gate_id"],
        "flight_event_id": flight["flight_event_id"],
        "task_name": tasks[index],
        "task_sequence": index + 1,
        "task_duration_minutes": round(max(2.0, rng.gauss(9.0, 3.0)), 1),
        "task_status": rng.choices(["OnPlan", "Delayed"], weights=[0.82, 0.18])[0],
    })


def build_queue(rng: random.Random, reference: dict, now: datetime,
                batch_id: str, sequence: int) -> dict:
    terminal = rng.choice(reference["terminals"])
    queue_length = int(max(0, rng.gauss(22, 9)))
    return _envelope(batch_id, sequence, {
        "event_timestamp": now.isoformat(),
        "airport_id": terminal["airport_id"],
        "terminal_id": terminal["terminal_id"],
        "checkpoint_id": f"{terminal['terminal_id']}-CP{(sequence % 4) + 1}",
        "queue_type": rng.choice(["Security", "BorderControl", "CheckIn"]),
        "queue_length": queue_length,
        "wait_time_minutes": round(max(0.5, queue_length * rng.uniform(0.5, 1.1)), 1),
        "throughput_passengers": int(max(10, rng.gauss(180, 45))),
    })


def build_energy(rng: random.Random, reference: dict, now: datetime,
                 batch_id: str, sequence: int) -> dict:
    gate = rng.choice(reference["gates"])
    energy = round(max(1.0, rng.gauss(62.0, 14.0)), 2)
    return _envelope(batch_id, sequence, {
        "event_timestamp": now.isoformat(),
        "airport_id": gate["airport_id"],
        "gate_id": gate["gate_id"],
        "meter_id": f"MTR-{gate['gate_id']}",
        "source": rng.choice(["Grid", "Solar", "GroundPower"]),
        "energy_kwh": energy,
        "demand_kw": round(energy * rng.uniform(0.8, 1.4), 2),
    })


def build_baggage(rng: random.Random, reference: dict, now: datetime,
                  batch_id: str, sequence: int) -> dict:
    flight = rng.choice(reference["flights"])
    mishandled = rng.random() < 0.03
    token = uuid.uuid5(uuid.NAMESPACE_OID, f"{batch_id}:{sequence}").hex[:12].upper()
    return _envelope(batch_id, sequence, {
        "event_timestamp": now.isoformat(),
        "airport_id": flight["airport_id"],
        "destination_airport_id": rng.choice(reference["airports"])["airport_id"],
        "flight_event_id": flight["flight_event_id"],
        "bag_token": f"BAG-{token}",
        "event_type": rng.choice(["CheckIn", "Sortation", "Loaded", "Delivered"]),
        "journey_status": "Mishandled" if mishandled
                          else rng.choice(["InTransit", "Delivered", "Loaded"]),
        "journey_minutes": round(max(5.0, rng.gauss(64.0, 22.0)), 1),
        "mishandled_flag": mishandled,
    })


def build_asset(rng: random.Random, reference: dict, now: datetime,
                batch_id: str, sequence: int) -> dict:
    asset = rng.choice(reference["assets"])
    availability = round(min(100.0, max(40.0, rng.gauss(96.0, 5.0))), 1)
    anomaly = availability < 85.0
    return _envelope(batch_id, sequence, {
        "event_timestamp": now.isoformat(),
        "airport_id": asset["airport_id"],
        "asset_id": asset["asset_id"],
        "asset_type": asset["asset_type"],
        "availability_pct": availability,
        "health_status": "Degraded" if anomaly else ("Watch" if availability < 93 else "Healthy"),
        "anomaly_flag": anomaly,
        "energy_kwh": round(max(0.5, rng.gauss(14.0, 5.0)), 2),
    })


def build_pos(rng: random.Random, reference: dict, now: datetime,
              batch_id: str, sequence: int) -> dict:
    outlet = rng.choice(reference["outlets"])
    transactions = int(max(1, rng.gauss(9, 4)))
    gross = round(transactions * rng.uniform(6.5, 38.0), 2)
    return _envelope(batch_id, sequence, {
        "event_timestamp": now.isoformat(),
        "airport_id": outlet["airport_id"],
        "terminal_id": outlet["terminal_id"],
        "outlet_id": outlet["outlet_id"],
        "product_id": rng.choice(reference["products"])["product_id"],
        "transaction_count": transactions,
        "gross_sales_proxy": gross,
        "refund_proxy": round(gross * rng.uniform(0.0, 0.05), 2),
    })


def build_incident(rng: random.Random, reference: dict, now: datetime,
                   batch_id: str, sequence: int) -> dict:
    gate = rng.choice(reference["gates"])
    severity = rng.choices(["Low", "Medium", "High"], weights=[0.6, 0.3, 0.1])[0]
    resolved = rng.random() < 0.7
    baseline = {"Low": 6.0, "Medium": 18.0, "High": 42.0}[severity]
    return _envelope(batch_id, sequence, {
        "event_timestamp": now.isoformat(),
        "airport_id": gate["airport_id"],
        "gate_id": gate["gate_id"],
        "category": rng.choice(["GroundHandling", "Weather", "Technical", "Security"]),
        "severity": severity,
        "status": "Resolved" if resolved else rng.choice(["Open", "Investigating"]),
        "delay_minutes": round(max(0.0, rng.gauss(baseline, 8.0)), 1),
        "resolution_minutes": round(max(1.0, rng.gauss(35.0, 15.0)), 1) if resolved else 0.0,
    })


BUILDERS = {
    "flight": build_flight,
    "turnaround": build_turnaround,
    "queue": build_queue,
    "energy": build_energy,
    "baggage": build_baggage,
    "asset": build_asset,
    "pos": build_pos,
    "incident": build_incident,
}


# ---------------------------------------------------------------- publishing

def publish(config: dict, reference: dict, args: argparse.Namespace) -> dict:
    from azure.core.exceptions import AzureError
    from azure.eventhub import EventData, EventHubProducerClient

    selected = [s for s in config["sources"]
                if args.source in (None, "all", s["key"])]
    if not selected:
        raise SystemExit(f"no source matches --source {args.source}")

    credential = None if args.dry_run else build_credential()
    producers = {}
    if not args.dry_run:
        for source in selected:
            producers[source["key"]] = EventHubProducerClient(
                fully_qualified_namespace=config["namespace_fqdn"],
                eventhub_name=source["event_hub"],
                credential=credential,
                retry_total=5,
                retry_backoff_factor=0.8,
            )
        LOGGER.info(f"producers ready for {[s['event_hub'] for s in selected]}")

    rng = random.Random(args.seed)
    counts = {s["key"]: 0 for s in selected}
    batch_id = f"STREAM-{uuid.uuid4().hex[:12].upper()}"
    deadline = time.monotonic() + args.duration_seconds
    sequence = 0

    try:
        while time.monotonic() < deadline:
            cycle_started = time.monotonic()
            for source in selected:
                key = source["key"]
                size = max(1, int(source["events_per_batch"] * args.rate_multiplier))
                now = datetime.now(timezone.utc)
                events = [BUILDERS[key](rng, reference, now, batch_id, sequence + i)
                          for i in range(size)]
                sequence += size

                if args.dry_run:
                    counts[key] += len(events)
                    if counts[key] == len(events):
                        LOGGER.info(f"{key} sample: {json.dumps(events[0])[:400]}")
                    continue

                try:
                    producer = producers[key]
                    batch = producer.create_batch(
                        partition_key=str(events[0][source["partition_key_field"]]))
                    for event in events:
                        batch.add(EventData(json.dumps(event, separators=(",", ":"))))
                    producer.send_batch(batch)
                    counts[key] += len(batch)
                    LOGGER.info(f"published hub={source['event_hub']} events={len(batch)} "
                                f"total={counts[key]}")
                except AzureError as exc:
                    LOGGER.error(f"publish failed hub={source['event_hub']} error={exc}")

            elapsed = time.monotonic() - cycle_started
            interval = max(s["publish_interval_seconds"] for s in selected)
            if elapsed < interval and time.monotonic() < deadline:
                time.sleep(interval - elapsed)
    finally:
        for producer in producers.values():
            producer.close()
        if credential is not None:
            credential.close()

    return {"batch_id": batch_id, "counts": counts}


def health_check(config: dict) -> int:
    """Verify Entra auth and hub reachability without publishing."""
    from azure.eventhub import EventHubProducerClient

    credential = build_credential()
    failures = 0
    try:
        for source in config["sources"]:
            client = EventHubProducerClient(
                fully_qualified_namespace=config["namespace_fqdn"],
                eventhub_name=source["event_hub"], credential=credential, retry_total=2)
            try:
                properties = client.get_eventhub_properties()
                LOGGER.info(f"health ok hub={source['event_hub']} "
                            f"partitions={len(properties['partition_ids'])}")
            except Exception as exc:
                failures += 1
                LOGGER.error(f"health FAILED hub={source['event_hub']} error={str(exc)[:200]}")
            finally:
                client.close()
    finally:
        credential.close()
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="all",
                        choices=["all", "flight", "turnaround", "queue", "energy",
                                 "baggage", "asset", "pos", "incident"])
    parser.add_argument("--duration-seconds", type=int, default=60)
    parser.add_argument("--rate-multiplier", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=39039)
    parser.add_argument("--refresh-reference", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="build and log events without publishing")
    parser.add_argument("--health-check", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    configure_logging(args.log_level)
    config = load_config()

    if args.health_check:
        failures = health_check(config)
        LOGGER.info(f"health check complete failures={failures}")
        return 1 if failures else 0

    reference = load_reference(args.refresh_reference)
    result = publish(config, reference, args)
    LOGGER.info(f"run complete batch_id={result['batch_id']} counts={result['counts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
