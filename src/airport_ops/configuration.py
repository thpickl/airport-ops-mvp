"""Versioned platform configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_NAMES = ("unit", "smoke", "demo", "enterprise")


@dataclass(frozen=True)
class SimulationConfig:
    schema_version: str
    environment: str
    resource_prefix: str
    seed: int
    airport_count: int
    simulation_start_utc: datetime
    scale_profile: str
    history_days: int
    flights_per_airport_day: int
    passengers_per_flight: int
    queue_observations_per_flight: int
    retail_transactions_per_flight: int
    asset_observations_per_airport_day: int
    event_fault_rate: float
    deployment_mode: str
    destructive_operations_enabled: bool
    external_integrations_enabled: bool
    data_classification: str
    recommendation_mode: str
    generator_version: str
    reference_mode: str
    disclaimer: str

    def canonical_values(self) -> dict[str, object]:
        values = asdict(self)
        values["simulation_start_utc"] = self.simulation_start_utc.isoformat().replace("+00:00", "Z")
        return values


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("simulation_start_utc must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def load_airport_references(root: Path = PROJECT_ROOT, reference_mode: str = "public_reference") -> list[dict[str, object]]:
    if reference_mode not in {"public_reference", "fictional"}:
        raise ValueError("reference_mode must be public_reference or fictional")
    snapshot = "config/reference/airport-anchors.fictional.json" if reference_mode == "fictional" else "config/reference/airport-anchors.json"
    payload = _load_json(root / snapshot)
    records = payload.get("records", [])
    if len(records) != 18:
        raise ValueError(f"The {reference_mode} reference snapshot must contain 18 airports, found {len(records)}")
    for record in records:
        try:
            ZoneInfo(str(record["time_zone"]))
        except (KeyError, ZoneInfoNotFoundError) as exc:
            raise ValueError(f"Invalid airport time zone for {record.get('iata_code', 'unknown')}") from exc
    return records


def load_config(
    root: Path = PROJECT_ROOT,
    profile_name: str | None = None,
    airport_count: int | None = None,
    simulation_start_utc: str | None = None,
    reference_mode: str | None = None,
) -> SimulationConfig:
    base = _load_json(root / "config" / "base" / "platform.json")
    selected_profile = profile_name or str(base["scale_profile"])
    if selected_profile not in PROFILE_NAMES:
        raise ValueError(f"scale_profile must be one of {PROFILE_NAMES}")
    profile = _load_json(root / "config" / "scale-profiles" / f"{selected_profile}.json")
    selected_reference_mode = reference_mode or str(base.get("reference_mode", "public_reference"))
    selected_airports = airport_count if airport_count is not None else int(base["airport_count"])
    if not 1 <= selected_airports <= len(load_airport_references(root, selected_reference_mode)):
        raise ValueError("airport_count must be between 1 and 18")
    if str(base["environment"]).lower() == "production":
        raise ValueError("The demonstration configuration refuses the production environment")
    config = SimulationConfig(
        schema_version=str(base["schema_version"]),
        environment=str(base["environment"]),
        resource_prefix=str(base["resource_prefix"]),
        seed=int(base["seed"]),
        airport_count=selected_airports,
        simulation_start_utc=_parse_utc(simulation_start_utc or str(base["simulation_start_utc"])),
        scale_profile=selected_profile,
        history_days=int(profile["history_days"]),
        flights_per_airport_day=int(profile["flights_per_airport_day"]),
        passengers_per_flight=int(profile["passengers_per_flight"]),
        queue_observations_per_flight=int(profile["queue_observations_per_flight"]),
        retail_transactions_per_flight=int(profile["retail_transactions_per_flight"]),
        asset_observations_per_airport_day=int(profile["asset_observations_per_airport_day"]),
        event_fault_rate=float(profile["event_fault_rate"]),
        deployment_mode=str(base["deployment_mode"]),
        destructive_operations_enabled=bool(base["destructive_operations_enabled"]),
        external_integrations_enabled=bool(base["external_integrations_enabled"]),
        data_classification=str(base["data_classification"]),
        recommendation_mode=str(base["recommendation_mode"]),
        generator_version=str(base["generator_version"]),
        reference_mode=selected_reference_mode,
        disclaimer=str(base["disclaimer"]),
    )
    numeric_values = (
        config.history_days,
        config.flights_per_airport_day,
        config.passengers_per_flight,
        config.queue_observations_per_flight,
        config.retail_transactions_per_flight,
        config.asset_observations_per_airport_day,
    )
    if any(value <= 0 for value in numeric_values):
        raise ValueError("All scale-profile volume settings must be positive")
    if not 0 <= config.event_fault_rate < 0.25:
        raise ValueError("event_fault_rate must be in [0, 0.25)")
    if config.deployment_mode not in {"dry-run", "plan", "apply"}:
        raise ValueError("deployment_mode must be dry-run, plan, or apply")
    return config