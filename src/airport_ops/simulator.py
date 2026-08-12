"""Deterministic synthetic airport master-data and event simulation."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .configuration import PROJECT_ROOT, SimulationConfig, load_airport_references
from .determinism import canonical_json, logical_checksum, stable_uuid

EVENT_SCHEMA_VERSION = "1.0"
PUBLIC_REFERENCE_EVENTS = {"airport", "airline", "aircraft_type"}
SYNTHETIC_MASTER_EVENTS = {"organization", "region", "terminal", "zone", "gate", "stand", "asset", "employee", "aircraft"}
TURNAROUND_COMPONENT_MEANS = {
    "baseline": {"deboarding": 6.2, "cleaning": 8.2, "catering": 6.3, "baggage": 9.0, "boarding": 13.0, "coordination": 5.3},
    "improvement": {"deboarding": 5.5, "cleaning": 6.6, "catering": 5.2, "baggage": 7.2, "boarding": 10.5, "coordination": 4.0},
}
AIRCRAFT_FAMILIES = ("A220", "A320-family", "A330", "B737-family", "B787", "E-Jet")
QUEUE_TYPES = ("Security", "BorderControl", "CheckIn", "Boarding")
ASSET_CLASSES = ("PassengerBoardingBridge", "BaggageBelt", "HVAC", "Escalator", "EnergyMeter", "GroundPower")


@dataclass(frozen=True)
class SimulationResult:
    config: SimulationConfig
    tables: dict[str, list[dict[str, Any]]]

    def checksums(self) -> dict[str, str]:
        return {
            table_name: logical_checksum(rows, ["event_id"])
            for table_name, rows in sorted(self.tables.items())
            if rows
        }

    def logical_checksum(self) -> str:
        return hashlib.sha256(canonical_json(self.checksums()).encode("utf-8")).hexdigest()


def _rng(config: SimulationConfig, *parts: object) -> random.Random:
    material = canonical_json([config.seed, config.generator_version, *parts]).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
    return random.Random(seed)


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Synthetic event timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _event(
    config: SimulationConfig,
    event_type: str,
    timestamp: datetime,
    natural_key: tuple[object, ...],
    payload: dict[str, Any],
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> dict[str, Any]:
    event_id = f"SYN-EVT-{stable_uuid(event_type, *natural_key)}"
    is_public_reference = event_type in PUBLIC_REFERENCE_EVENTS
    classification = (
        "PublicReference"
        if is_public_reference
        else "SyntheticMaster"
        if event_type in SYNTHETIC_MASTER_EVENTS
        else "SyntheticOperational"
    )
    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_schema_version": EVENT_SCHEMA_VERSION,
        "event_timestamp_utc": _utc_text(timestamp),
        "source_system": "PUBLIC-REFERENCE-CATALOG" if is_public_reference else f"SYN-{event_type.upper()}-SIM",
        "correlation_id": correlation_id or f"SYN-COR-{stable_uuid('correlation', *natural_key)}",
        "causation_id": causation_id,
        "record_version": 1,
        "is_synthetic": not is_public_reference,
        "data_classification": classification,
        "generator_version": config.generator_version,
        **payload,
    }


def _phase(config: SimulationConfig, day_index: int) -> str:
    return "baseline" if day_index < max(1, config.history_days // 2) else "improvement"


def _bounded(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def _local_context(timestamp: datetime, time_zone: str) -> dict[str, Any]:
    local = timestamp.astimezone(ZoneInfo(time_zone))
    return {
        "airport_time_zone": time_zone,
        "event_timestamp_local": local.isoformat(),
        "local_utc_offset_minutes": int(local.utcoffset().total_seconds() // 60),
        "local_fold": local.fold,
    }


def _master_data(config: SimulationConfig, airports: list[dict[str, object]]) -> dict[str, list[dict[str, Any]]]:
    tables: dict[str, list[dict[str, Any]]] = defaultdict(list)
    start = config.simulation_start_utc
    airline_references = json.loads((PROJECT_ROOT / "data" / "reference" / "airlines.json").read_text(encoding="utf-8"))["records"]
    aircraft_type_references = json.loads((PROJECT_ROOT / "data" / "reference" / "aircraft_types.json").read_text(encoding="utf-8"))["records"]
    tables["organization"].append(_event(config, "organization", start, ("group",), {
        "organization_id": "SYN-ORG-FAO-001",
        "organization_name": "AeroSphere Operations Intelligence Demonstration",
        "headquarters_id": "SYN-HQ-FR-001",
        "headquarters_country": "France",
        "portfolio_relationship": "Fictional demonstration relationship only; no ownership or operating claim",
    }))
    for region in ("France", "Italy", "Portugal", "Jordan"):
        tables["region"].append(_event(config, "region", start, (region,), {
            "region_id": f"SYN-REG-{region.upper()}", "region_name": region,
        }))
    for airport_index, reference in enumerate(airports, start=1):
        code = str(reference["iata_code"])
        airport_id = f"SYN-AP-{code}"
        tables["airport"].append(_event(config, "airport", start, (airport_id,), {
            **reference,
            "airport_id": airport_id,
            "reference_anchor_only": True,
            "fictional_portfolio_relationship": True,
        }))
        for terminal_number in range(1, 3):
            terminal_id = f"SYN-TER-{code}-{terminal_number:02d}"
            tables["terminal"].append(_event(config, "terminal", start, (terminal_id,), {
                "terminal_id": terminal_id, "airport_id": airport_id, "terminal_name": f"Synthetic Terminal {terminal_number}",
                "geometry_is_synthetic": True, "floor_count": 3,
            }))
            for zone_number in range(1, 5):
                zone_id = f"SYN-ZON-{code}-{terminal_number:02d}-{zone_number:02d}"
                tables["zone"].append(_event(config, "zone", start, (zone_id,), {
                    "zone_id": zone_id, "terminal_id": terminal_id, "airport_id": airport_id,
                    "zone_type": ("CheckIn", "Security", "Retail", "Boarding")[zone_number - 1], "geometry_is_synthetic": True,
                }))
        for position in range(1, 7):
            tables["gate"].append(_event(config, "gate", start, (code, position), {
                "gate_id": f"SYN-GAT-{code}-{position:02d}", "airport_id": airport_id,
                "terminal_id": f"SYN-TER-{code}-{1 + (position % 2):02d}", "contact_gate": position % 4 != 0,
            }))
            tables["stand"].append(_event(config, "stand", start, (code, position), {
                "stand_id": f"SYN-STD-{code}-{position:02d}", "airport_id": airport_id,
                "stand_category": "C" if position < 5 else "E", "geometry_is_synthetic": True,
            }))
        for asset_number, asset_class in enumerate(ASSET_CLASSES, start=1):
            tables["asset"].append(_event(config, "asset", start, (code, asset_number), {
                "asset_id": f"SYN-AST-{code}-{asset_number:03d}", "airport_id": airport_id,
                "asset_class": asset_class, "zone_id": f"SYN-ZON-{code}-01-{1 + (asset_number % 4):02d}",
            }))
        for employee_number in range(1, 13):
            tables["employee"].append(_event(config, "employee", start, (code, employee_number), {
                "employee_id": f"SYN-EMP-{code}-{employee_number:05d}", "airport_id": airport_id,
                "team_id": f"SYN-TEAM-{code}-{1 + employee_number % 4:02d}",
                "role": ("Operations", "Maintenance", "PassengerService", "Compliance")[employee_number % 4],
                "skill_code": f"SYN-SKILL-{1 + employee_number % 6:02d}", "certification_current": employee_number % 11 != 0,
            }))
    for airline in airline_references:
        tables["airline"].append(_event(config, "airline", start, (airline["airline_id"],), dict(airline)))
    for aircraft_type in aircraft_type_references:
        tables["aircraft_type"].append(_event(config, "aircraft_type", start, (aircraft_type["aircraft_type_id"],), dict(aircraft_type)))
    for aircraft_number in range(1, 25):
        aircraft_type = aircraft_type_references[(aircraft_number - 1) % len(aircraft_type_references)]
        tables["aircraft"].append(_event(config, "aircraft", start, (aircraft_number,), {
            "aircraft_id": f"SYN-AC-{aircraft_number:05d}", "registration_id": f"SYN-REG-{aircraft_number:05d}",
            "aircraft_type_id": aircraft_type["aircraft_type_id"], "aircraft_family": aircraft_type["model"],
            "airline_id": airline_references[(aircraft_number - 1) % len(airline_references)]["airline_id"],
        }))
    return dict(tables)


def simulate(config: SimulationConfig) -> SimulationResult:
    airports = load_airport_references(reference_mode=config.reference_mode)[: config.airport_count]
    airline_references = json.loads((PROJECT_ROOT / "data" / "reference" / "airlines.json").read_text(encoding="utf-8"))["records"]
    aircraft_type_references = json.loads((PROJECT_ROOT / "data" / "reference" / "aircraft_types.json").read_text(encoding="utf-8"))["records"]
    tables = _master_data(config, airports)
    for name in (
        "flight_operation", "turnaround_milestone", "passenger_journey", "queue_observation", "baggage_journey",
        "retail_transaction", "workforce_shift", "weather_observation", "energy_observation", "asset_telemetry",
        "maintenance_work_order", "incident", "customer_feedback", "regulatory_workflow",
    ):
        tables.setdefault(name, [])

    for day_index in range(config.history_days):
        day_start = config.simulation_start_utc + timedelta(days=day_index)
        phase = _phase(config, day_index)
        weekend_factor = 1.08 if day_start.weekday() >= 5 else 1.0
        seasonal_factor = 1.0 + 0.08 * math.sin(2 * math.pi * day_start.timetuple().tm_yday / 365.25)
        for airport_index, airport in enumerate(airports):
            code = str(airport["iata_code"])
            airport_id = f"SYN-AP-{code}"
            time_zone = str(airport["time_zone"])
            day_rng = _rng(config, "airport-day", code, day_index)
            weather_severity = _bounded(day_rng.normalvariate(0.12, 0.08), 0.0, 0.65)
            weather_time = day_start + timedelta(hours=6)
            tables["weather_observation"].append(_event(config, "weather_observation", weather_time, (code, day_index), {
                "airport_id": airport_id, "phase": phase, "temperature_c": round(day_rng.normalvariate(17, 7), 1),
                "wind_speed_kph": round(day_rng.uniform(5, 42), 1), "weather_severity_index": round(weather_severity, 4),
                "observation_type": "SyntheticClimateAware", **_local_context(weather_time, time_zone),
            }))
            required_staff = 34 + (day_index + airport_index) % 9
            coverage_factor = 0.91 if phase == "baseline" else 0.98
            scheduled_staff = max(1, round(required_staff * coverage_factor + day_rng.normalvariate(0, 1.0)))
            tables["workforce_shift"].append(_event(config, "workforce_shift", day_start, (code, day_index), {
                "shift_id": f"SYN-SHIFT-{code}-{day_index:04d}", "airport_id": airport_id, "phase": phase,
                "required_staff": required_staff, "scheduled_staff": scheduled_staff,
                "overtime_hours": round(max(0, required_staff - scheduled_staff) * 1.7, 1),
                "absence_count": int(day_rng.random() < 0.16), "skill_coverage_rate": round(_bounded(coverage_factor + 0.01, 0, 1), 4),
            }))
            tables["maintenance_work_order"].append(_event(config, "maintenance_work_order", day_start + timedelta(hours=4), (code, day_index), {
                "work_order_id": f"SYN-WO-{code}-{day_index:05d}", "airport_id": airport_id,
                "asset_id": f"SYN-AST-{code}-{1 + day_index % len(ASSET_CLASSES):03d}", "phase": phase,
                "work_order_type": "Preventive" if day_index % 3 else "Corrective", "status": "Closed" if day_index % 5 else "Open",
                "repair_minutes": round(day_rng.uniform(25, 160) * (0.82 if phase == "improvement" else 1.0), 1),
                "first_time_fix": day_rng.random() < (0.87 if phase == "improvement" else 0.76),
            }))
            for observation_index in range(config.asset_observations_per_airport_day):
                observation_time = day_start + timedelta(minutes=observation_index * 1440 / config.asset_observations_per_airport_day)
                asset_number = 1 + observation_index % len(ASSET_CLASSES)
                health = _bounded(day_rng.normalvariate(0.88 if phase == "improvement" else 0.81, 0.08), 0.25, 1.0)
                tables["asset_telemetry"].append(_event(config, "asset_telemetry", observation_time, (code, day_index, observation_index), {
                    "airport_id": airport_id, "asset_id": f"SYN-AST-{code}-{asset_number:03d}", "phase": phase,
                    "health_score": round(health, 4), "available": health >= 0.55,
                    "anomaly_flag": health < 0.62, **_local_context(observation_time, time_zone),
                }))
            if day_rng.random() < 0.08:
                detected = day_start + timedelta(hours=day_rng.randint(0, 23), minutes=day_rng.randint(0, 59))
                response_factor = 0.76 if phase == "improvement" else 1.0
                acknowledgement = max(1, round(day_rng.uniform(4, 18) * response_factor))
                resolution = max(15, round(day_rng.uniform(45, 240) * response_factor))
                tables["incident"].append(_event(config, "incident", detected, (code, day_index), {
                    "incident_id": f"SYN-INC-{code}-{day_index:05d}", "airport_id": airport_id, "phase": phase,
                    "severity": 1 + day_rng.randrange(4), "acknowledgement_minutes": acknowledgement,
                    "response_minutes": acknowledgement + max(2, round(day_rng.uniform(3, 20))), "resolution_minutes": resolution,
                    "corrective_action_status": "Closed" if day_index % 4 else "InReview", "official_submission": False,
                }))

            for flight_index in range(config.flights_per_airport_day):
                flight_rng = _rng(config, "flight", code, day_index, flight_index)
                scheduled_arrival = day_start + timedelta(hours=(flight_index * 3 + airport_index) % 24, minutes=(flight_index * 7) % 60)
                demand_factor = weekend_factor * seasonal_factor * (1.18 if scheduled_arrival.hour in {7, 8, 16, 17, 18} else 0.94)
                passenger_count = max(8, round(config.passengers_per_flight * demand_factor * flight_rng.uniform(0.88, 1.12)))
                flight_id = f"SYN-FLT-{code}-{day_index:04d}-{flight_index:03d}"
                airline = airline_references[(airport_index + flight_index) % len(airline_references)]
                airline_id = airline["airline_id"]
                aircraft_number = 1 + (day_index * config.flights_per_airport_day + flight_index) % 24
                aircraft_id = f"SYN-AC-{aircraft_number:05d}"
                aircraft_type = aircraft_type_references[(aircraft_number - 1) % len(aircraft_type_references)]
                destination = airports[(airport_index + flight_index + 1) % len(airports)]
                correlation_id = f"SYN-COR-{stable_uuid('flight', flight_id)}"
                components: dict[str, float] = {}
                for component, component_mean in TURNAROUND_COMPONENT_MEANS[phase].items():
                    component_noise = flight_rng.normalvariate(0, 0.28 if component != "coordination" else 0.45)
                    congestion_effect = (demand_factor - 1) * (0.9 if phase == "baseline" else 0.35)
                    components[component] = round(max(1.0, component_mean + component_noise + congestion_effect), 2)
                turnaround_minutes = round(sum(components.values()), 2)
                arrival_delay = round(max(-8, flight_rng.normalvariate(8 + weather_severity * 15, 9)), 1)
                actual_arrival = scheduled_arrival + timedelta(minutes=arrival_delay)
                actual_departure = actual_arrival + timedelta(minutes=turnaround_minutes)
                cancelled = flight_rng.random() < (0.012 if phase == "baseline" else 0.008)
                diverted = not cancelled and flight_rng.random() < 0.004
                flight_event = _event(config, "flight_operation", actual_arrival, (flight_id,), {
                    "flight_id": flight_id, "route_id": f"SYN-ROUTE-{code}-{destination['iata_code']}",
                    "origin_airport_id": airport_id, "destination_airport_id": f"SYN-AP-{destination['iata_code']}",
                    "airline_id": airline_id, "aircraft_id": aircraft_id, "aircraft_type_id": aircraft_type["aircraft_type_id"],
                    "aircraft_family": aircraft_type["model"],
                    "gate_id": f"SYN-GAT-{code}-{1 + flight_index % 6:02d}", "stand_id": f"SYN-STD-{code}-{1 + flight_index % 6:02d}",
                    "phase": phase, "scheduled_arrival_utc": _utc_text(scheduled_arrival), "actual_arrival_utc": _utc_text(actual_arrival),
                    "actual_departure_utc": _utc_text(actual_departure), "arrival_delay_minutes": arrival_delay,
                    "departure_delay_minutes": round(max(0, arrival_delay) + max(0, turnaround_minutes - 38), 1),
                    "turnaround_minutes": turnaround_minutes, "turnaround_target_minutes": 38,
                    "passenger_count": passenger_count, "cancelled": cancelled, "diverted": diverted,
                    "delay_reason": "SyntheticWeather" if weather_severity > 0.35 else "SyntheticOperational",
                    **_local_context(actual_arrival, time_zone),
                }, correlation_id=correlation_id)
                tables["flight_operation"].append(flight_event)
                milestone_start = actual_arrival
                for sequence, (component, minutes) in enumerate(components.items(), start=1):
                    milestone_end = milestone_start + timedelta(minutes=minutes)
                    tables["turnaround_milestone"].append(_event(config, "turnaround_milestone", milestone_end, (flight_id, component), {
                        "milestone_id": f"SYN-MILE-{flight_id}-{sequence:02d}", "flight_id": flight_id, "airport_id": airport_id,
                        "phase": phase, "milestone_type": component, "duration_minutes": minutes,
                        "service_level_breach": minutes > TURNAROUND_COMPONENT_MEANS["baseline"][component] * 1.25,
                    }, correlation_id=correlation_id, causation_id=flight_event["event_id"]))
                    milestone_start = milestone_end

                queue_waits: list[float] = []
                for queue_index in range(config.queue_observations_per_flight):
                    queue_type = QUEUE_TYPES[queue_index % len(QUEUE_TYPES)]
                    capacity_factor = 1.0 if phase == "baseline" else 1.40
                    demand_smoothing = 0.0 if phase == "baseline" else 0.16
                    wait_minutes = max(1.0, 24.0 * demand_factor / capacity_factor * (1 - demand_smoothing) + flight_rng.normalvariate(0, 1.25))
                    affected = max(5, round(passenger_count / config.queue_observations_per_flight * demand_factor))
                    missed_probability = _bounded(0.12 + wait_minutes / 110, 0.04, 0.72)
                    missed_count = round(affected * missed_probability)
                    queue_time = actual_arrival + timedelta(minutes=queue_index * 15)
                    queue_waits.append(wait_minutes)
                    tables["queue_observation"].append(_event(config, "queue_observation", queue_time, (flight_id, queue_index), {
                        "queue_observation_id": f"SYN-QUE-{flight_id}-{queue_index:02d}", "flight_id": flight_id,
                        "airport_id": airport_id, "phase": phase, "queue_type": queue_type,
                        "demand_passengers": affected, "service_capacity_factor": capacity_factor,
                        "demand_smoothing_factor": demand_smoothing, "wait_minutes": round(wait_minutes, 2),
                        "missed_preferred_boarding_count": missed_count, "forecast_wait_minutes": round(wait_minutes * flight_rng.uniform(0.92, 1.08), 2),
                        **_local_context(queue_time, time_zone),
                    }, correlation_id=correlation_id, causation_id=flight_event["event_id"]))

                footfall_rate, conversion_rate, basket_value = ((0.58, 0.33, 36.4) if phase == "baseline" else (0.60, 0.37, 38.35))
                transaction_count = max(config.retail_transactions_per_flight, round(passenger_count * footfall_rate * conversion_rate))
                target_revenue = passenger_count * footfall_rate * conversion_rate * basket_value
                weights = [flight_rng.uniform(0.75, 1.25) for _ in range(transaction_count)]
                weight_total = sum(weights)
                amounts = [round(target_revenue * weight / weight_total, 2) for weight in weights]
                amounts[-1] = round(amounts[-1] + target_revenue - sum(amounts), 2)
                for transaction_index, amount in enumerate(amounts):
                    transaction_time = actual_arrival + timedelta(minutes=12 + transaction_index)
                    tables["retail_transaction"].append(_event(config, "retail_transaction", transaction_time, (flight_id, transaction_index), {
                        "transaction_id": f"SYN-POS-{flight_id}-{transaction_index:03d}", "airport_id": airport_id,
                        "flight_id": flight_id, "phase": phase, "outlet_id": f"SYN-RTL-{code}-{1 + transaction_index % 8:02d}",
                        "product_category": ("Food", "Beverage", "Travel", "DutyFree")[transaction_index % 4],
                        "gross_revenue_eur": amount, "refund_eur": round(amount * 0.04, 2) if transaction_index % 41 == 0 else 0.0,
                        "promotion_applied": phase == "improvement" and transaction_index % 3 == 0,
                        "recommendation_cohort": "SYN-OPTIN-GENERAL" if transaction_index % 5 == 0 else None,
                    }, correlation_id=correlation_id, causation_id=flight_event["event_id"]))

                for passenger_index in range(min(4, passenger_count)):
                    passenger_id = f"SYN-PAX-{stable_uuid('passenger', flight_id, passenger_index)}"
                    consent = passenger_index % 3 != 0
                    tables["passenger_journey"].append(_event(config, "passenger_journey", actual_arrival, (flight_id, passenger_index), {
                        "passenger_id": passenger_id, "flight_id": flight_id, "airport_id": airport_id, "phase": phase,
                        "booking_id": f"SYN-BKG-{stable_uuid('booking', flight_id, passenger_index)}",
                        "connection_flag": passenger_index % 4 == 0, "accessibility_category": "MobilityAssistance" if passenger_index % 11 == 0 else "None",
                        "recommendation_consent": consent, "preference_consent": consent, "identity_is_pseudonymous": True,
                    }, correlation_id=correlation_id, causation_id=flight_event["event_id"]))
                    bag_id = f"SYN-BAG-{stable_uuid('bag', passenger_id, flight_id)}"
                    transfer_success = flight_rng.random() > (0.018 if phase == "baseline" else 0.009)
                    tables["baggage_journey"].append(_event(config, "baggage_journey", actual_arrival + timedelta(minutes=18 + passenger_index), (bag_id,), {
                        "bag_id": bag_id, "passenger_id": passenger_id, "flight_id": flight_id, "airport_id": airport_id,
                        "phase": phase, "scan_count": 5 if transfer_success else 3, "expected_scan_count": 5,
                        "transfer_success": transfer_success, "delivery_minutes": round(flight_rng.uniform(14, 38), 1),
                        "mishandled": not transfer_success and passenger_index % 2 == 0,
                    }, correlation_id=correlation_id, causation_id=flight_event["event_id"]))
                energy_benchmark = passenger_count * 2.4
                energy_factor = 1.26 if phase == "baseline" else 1.08
                total_energy = energy_benchmark * energy_factor * flight_rng.uniform(0.985, 1.015)
                energy_time = actual_departure
                tables["energy_observation"].append(_event(config, "energy_observation", energy_time, (flight_id,), {
                    "energy_observation_id": f"SYN-ENR-{flight_id}", "airport_id": airport_id, "flight_id": flight_id,
                    "phase": phase, "passenger_count": passenger_count, "terminal_area_m2": 48000 + airport_index * 1200,
                    "electricity_kwh": round(total_energy, 3), "benchmark_kwh": round(energy_benchmark, 3),
                    "hvac_kwh": round(total_energy * 0.46, 3), "base_load_kwh": round(total_energy * 0.34, 3),
                    "process_load_kwh": round(total_energy * 0.20, 3), "water_liters": round(passenger_count * (8.4 if phase == "baseline" else 7.6), 2),
                    "emissions_proxy_kgco2e": round(total_energy * 0.23, 3), **_local_context(energy_time, time_zone),
                }, correlation_id=correlation_id, causation_id=flight_event["event_id"]))
                csat = _bounded(3.25 + (0.42 if phase == "improvement" else 0) - sum(queue_waits) / len(queue_waits) / 80 + flight_rng.normalvariate(0, 0.12), 1, 5)
                nps = _bounded((csat - 3.0) * 42 + flight_rng.normalvariate(0, 5), -100, 100)
                tables["customer_feedback"].append(_event(config, "customer_feedback", actual_departure, (flight_id,), {
                    "feedback_id": f"SYN-CX-{flight_id}", "airport_id": airport_id, "flight_id": flight_id, "phase": phase,
                    "synthetic_csat": round(csat, 2), "synthetic_nps": round(nps, 1),
                    "complaint_category": "Queue" if max(queue_waits) > 25 else "None", "recovery_offered": max(queue_waits) > 30,
                }, correlation_id=correlation_id, causation_id=flight_event["event_id"]))

    total_regulatory_activities = max(2, round(config.history_days * 840 / 365))
    improvement_activity_indexes = [
        activity_index
        for activity_index in range(total_regulatory_activities)
        if _phase(config, min(config.history_days - 1, activity_index * config.history_days // total_regulatory_activities)) == "improvement"
    ]
    automated_activity_indexes = set(sorted(
        improvement_activity_indexes,
        key=lambda activity_index: _rng(config, "regulatory-automation-rank", activity_index).random(),
    )[: round(len(improvement_activity_indexes) * 0.78)])
    for activity_index in range(total_regulatory_activities):
        day_index = min(config.history_days - 1, activity_index * config.history_days // total_regulatory_activities)
        phase = _phase(config, day_index)
        airport = airports[activity_index % len(airports)]
        code = str(airport["iata_code"])
        timestamp = config.simulation_start_utc + timedelta(days=day_index, hours=10 + activity_index % 6)
        activity_rng = _rng(config, "regulatory", activity_index)
        automated = activity_index in automated_activity_indexes
        tables["regulatory_workflow"].append(_event(config, "regulatory_workflow", timestamp, (activity_index,), {
            "regulatory_workflow_id": f"SYN-REGWF-{activity_index:06d}", "airport_id": f"SYN-AP-{code}", "phase": phase,
            "report_type": ("NationalAviation", "EASA-Demonstration", "Environmental", "IncidentSummary")[activity_index % 4],
            "preparation_mode": "AutomatedDraft" if automated else "Manual",
            "automated_preparation": automated, "human_approval_required": True,
            "approval_status": ("Approved", "Deferred", "Rejected")[activity_index % 3],
            "official_submission": False, "preparation_minutes": round(activity_rng.uniform(15, 45) if automated else activity_rng.uniform(120, 300), 1),
        }))
    for rows in tables.values():
        rows.sort(key=lambda row: (row["event_timestamp_utc"], row["event_id"]))
    return SimulationResult(config=config, tables=tables)