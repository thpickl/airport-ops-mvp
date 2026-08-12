"""Rerunnable Bronze, Silver, and Gold transformations for local validation."""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

from .configuration import SimulationConfig
from .determinism import canonical_json, logical_checksum, stable_uuid
from .simulator import SimulationResult

REQUIRED_EVENT_FIELDS = {
    "event_id",
    "event_type",
    "event_schema_version",
    "event_timestamp_utc",
    "source_system",
    "correlation_id",
    "record_version",
    "is_synthetic",
    "data_classification",
}


@dataclass(frozen=True)
class SilverResult:
    tables: dict[str, list[dict[str, Any]]]
    quarantine: list[dict[str, Any]]
    quality_results: list[dict[str, Any]]
    lineage: list[dict[str, Any]]


@dataclass(frozen=True)
class GoldResult:
    tables: dict[str, list[dict[str, Any]]]
    kpis: dict[str, dict[str, float]]


@dataclass(frozen=True)
class PipelineResult:
    simulation: SimulationResult
    bronze: dict[str, list[dict[str, Any]]]
    silver: SilverResult
    gold: GoldResult

    def logical_checksum(self) -> str:
        payload = {
            "simulation": self.simulation.logical_checksum(),
            "bronze": _table_checksums(self.bronze, "ingestion_record_id"),
            "silver": _table_checksums(self.silver.tables, "event_id"),
            "gold": _table_checksums(self.gold.tables, None),
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _table_checksums(tables: dict[str, list[dict[str, Any]]], preferred_key: str | None) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for table_name, rows in sorted(tables.items()):
        if not rows:
            checksums[table_name] = hashlib.sha256(b"").hexdigest()
            continue
        key = preferred_key if preferred_key and preferred_key in rows[0] else next(
            (candidate for candidate in ("kpi_id", "node_id", "edge_id", "event_id") if candidate in rows[0]),
            None,
        )
        if key:
            checksums[table_name] = logical_checksum(rows, [key])
        else:
            ordered = sorted(canonical_json(row) for row in rows)
            checksums[table_name] = hashlib.sha256("\n".join(ordered).encode("utf-8")).hexdigest()
    return checksums


def build_bronze(simulation: SimulationResult) -> dict[str, list[dict[str, Any]]]:
    config = simulation.config
    replay_batch_id = f"SYN-RPL-{stable_uuid('replay', config.canonical_values())}"
    fault_stride = max(25, round(1 / max(config.event_fault_rate, 0.000001)))
    bronze: dict[str, list[dict[str, Any]]] = {}
    global_sequence = 0
    for source_table, source_rows in sorted(simulation.tables.items()):
        target = f"bronze_{source_table}"
        envelopes: list[dict[str, Any]] = []
        for source_sequence, source_row in enumerate(source_rows):
            global_sequence += 1
            event_time = _parse_utc(source_row["event_timestamp_utc"])
            is_late = global_sequence % (fault_stride * 2) == 0
            ingestion_time = event_time + (timedelta(hours=12) if is_late else timedelta(minutes=5))
            payload = canonical_json(source_row)
            payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            envelope = {
                "ingestion_record_id": f"SYN-ING-{stable_uuid('ingestion', replay_batch_id, source_table, source_sequence, 0)}",
                "event_id": source_row["event_id"],
                "event_type": source_row["event_type"],
                "event_schema_version": source_row["event_schema_version"],
                "event_timestamp_utc": source_row["event_timestamp_utc"],
                "ingestion_timestamp_utc": _utc_text(ingestion_time),
                "replay_batch_id": replay_batch_id,
                "correlation_id": source_row["correlation_id"],
                "causation_id": source_row.get("causation_id"),
                "source_system": source_row["source_system"],
                "source_table": source_table,
                "source_sequence": source_sequence,
                "source_file": f"Files/landing/{replay_batch_id}/{source_table}.jsonl",
                "canonical_payload_hash": payload_hash,
                "raw_payload": payload,
                "parsing_status": "PARSED",
                "quarantine_reason": None,
                "duplicate_candidate": False,
                "is_late_arrival": is_late,
                "is_out_of_order": global_sequence % (fault_stride * 3) == 0,
                "is_correction": False,
                "corrects_event_id": None,
                "record_version": int(source_row.get("record_version", 1)),
                "data_classification": source_row["data_classification"],
            }
            envelopes.append(envelope)
            if global_sequence % fault_stride == 0:
                duplicate = dict(envelope)
                duplicate["ingestion_record_id"] = f"SYN-ING-{stable_uuid('ingestion', replay_batch_id, source_table, source_sequence, 1)}"
                duplicate["duplicate_candidate"] = True
                duplicate["ingestion_timestamp_utc"] = _utc_text(ingestion_time + timedelta(seconds=1))
                envelopes.append(duplicate)
            if global_sequence % (fault_stride * 4) == 2:
                corrected_payload = dict(source_row)
                corrected_payload["record_version"] = int(source_row.get("record_version", 1)) + 1
                corrected_payload["correction_reason"] = "Deterministic source correction scenario"
                correction_raw = canonical_json(corrected_payload)
                correction = dict(envelope)
                correction["ingestion_record_id"] = f"SYN-ING-{stable_uuid('ingestion', replay_batch_id, source_table, source_sequence, 'correction')}"
                correction["raw_payload"] = correction_raw
                correction["canonical_payload_hash"] = hashlib.sha256(correction_raw.encode("utf-8")).hexdigest()
                correction["record_version"] = corrected_payload["record_version"]
                correction["is_correction"] = True
                correction["corrects_event_id"] = source_row["event_id"]
                correction["ingestion_timestamp_utc"] = _utc_text(ingestion_time + timedelta(minutes=1))
                envelopes.append(correction)
            if global_sequence % (fault_stride * 5) == 3:
                malformed = dict(envelope)
                malformed["ingestion_record_id"] = f"SYN-ING-{stable_uuid('ingestion', replay_batch_id, source_table, source_sequence, 'malformed')}"
                malformed["event_id"] = f"SYN-EVT-{stable_uuid('malformed', source_table, source_sequence)}"
                malformed["raw_payload"] = "{malformed-json"
                malformed["canonical_payload_hash"] = hashlib.sha256(malformed["raw_payload"].encode("utf-8")).hexdigest()
                malformed["parsing_status"] = "QUARANTINED"
                malformed["quarantine_reason"] = "MALFORMED_JSON"
                envelopes.append(malformed)
        envelopes.sort(key=lambda row: row["ingestion_record_id"])
        bronze[target] = envelopes
    bronze["bronze_ingestion_ledger"] = [{
        "ingestion_record_id": f"SYN-LEDGER-{stable_uuid('ledger', replay_batch_id)}",
        "replay_batch_id": replay_batch_id,
        "generator_version": config.generator_version,
        "configuration_hash": hashlib.sha256(canonical_json(config.canonical_values()).encode("utf-8")).hexdigest(),
        "source_record_count": sum(len(rows) for rows in simulation.tables.values()),
        "bronze_record_count": sum(len(rows) for rows in bronze.values()),
        "committed": True,
    }]
    return bronze


def merge_bronze(
    existing: dict[str, list[dict[str, Any]]],
    incoming: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, list[dict[str, Any]]] = {}
    for table_name in sorted(set(existing) | set(incoming)):
        records = {
            row["ingestion_record_id"]: row
            for row in [*existing.get(table_name, []), *incoming.get(table_name, [])]
        }
        merged[table_name] = sorted(records.values(), key=lambda row: row["ingestion_record_id"])
    return merged


def conform_silver(bronze: dict[str, list[dict[str, Any]]]) -> SilverResult:
    tables: dict[str, list[dict[str, Any]]] = {}
    quarantine: list[dict[str, Any]] = []
    quality_results: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    for bronze_name, envelopes in sorted(bronze.items()):
        if bronze_name == "bronze_ingestion_ledger":
            continue
        silver_name = bronze_name.replace("bronze_", "silver_", 1)
        candidates: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
        for envelope in envelopes:
            if envelope["parsing_status"] != "PARSED":
                quarantine.append({**envelope, "silver_table": silver_name})
                continue
            try:
                payload = json.loads(envelope["raw_payload"])
            except json.JSONDecodeError:
                quarantine.append({**envelope, "quarantine_reason": "MALFORMED_JSON", "silver_table": silver_name})
                continue
            missing = sorted(REQUIRED_EVENT_FIELDS - payload.keys())
            if missing:
                quarantine.append({**envelope, "quarantine_reason": f"MISSING_REQUIRED_FIELDS:{','.join(missing)}", "silver_table": silver_name})
                continue
            if payload["is_synthetic"] is not True:
                quarantine.append({**envelope, "quarantine_reason": "NON_SYNTHETIC_RECORD", "silver_table": silver_name})
                continue
            candidates[payload["event_id"]].append((envelope, payload))
        conformed: list[dict[str, Any]] = []
        duplicate_count = 0
        correction_count = 0
        late_count = 0
        for event_id, versions in candidates.items():
            selected_envelope, selected_payload = max(
                versions,
                key=lambda pair: (int(pair[1].get("record_version", 1)), pair[0]["ingestion_timestamp_utc"], pair[0]["ingestion_record_id"]),
            )
            duplicate_count += max(0, len(versions) - 1)
            correction_count += int(selected_envelope["is_correction"])
            late_count += int(selected_envelope["is_late_arrival"])
            conformed.append({
                **selected_payload,
                "silver_record_hash": selected_envelope["canonical_payload_hash"],
                "source_ingestion_record_id": selected_envelope["ingestion_record_id"],
                "source_replay_batch_id": selected_envelope["replay_batch_id"],
                "is_late_arrival": selected_envelope["is_late_arrival"],
                "is_correction": selected_envelope["is_correction"],
                "quality_rule_version": "1.0",
                "classification": selected_payload["data_classification"],
            })
        conformed.sort(key=lambda row: row["event_id"])
        tables[silver_name] = conformed
        quality_results.append({
            "quality_result_id": f"SYN-DQ-{stable_uuid('quality', silver_name)}",
            "table_name": silver_name,
            "input_count": len(envelopes),
            "output_count": len(conformed),
            "quarantine_count": sum(1 for row in quarantine if row["silver_table"] == silver_name),
            "duplicate_or_superseded_count": duplicate_count,
            "correction_count": correction_count,
            "late_arrival_count": late_count,
            "rule_version": "1.0",
            "status": "PASS",
        })
        lineage.append({
            "lineage_id": f"SYN-LIN-{stable_uuid('lineage', bronze_name, silver_name)}",
            "source_object": bronze_name,
            "target_object": silver_name,
            "transformation": "schema validation, parse, synthetic-policy enforcement, version-aware deduplication",
            "rule_version": "1.0",
        })
    quarantine.sort(key=lambda row: row["ingestion_record_id"])
    return SilverResult(tables=tables, quarantine=quarantine, quality_results=quality_results, lineage=lineage)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = percentile * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def calculate_kpis(silver: SilverResult, config: SimulationConfig) -> dict[str, dict[str, float]]:
    flights = silver.tables["silver_flight_operation"]
    queues = silver.tables["silver_queue_observation"]
    retail = silver.tables["silver_retail_transaction"]
    energy = silver.tables["silver_energy_observation"]
    regulatory = silver.tables["silver_regulatory_workflow"]
    baggage = silver.tables["silver_baggage_journey"]
    workforce = silver.tables["silver_workforce_shift"]
    maintenance = silver.tables["silver_maintenance_work_order"]
    telemetry = silver.tables["silver_asset_telemetry"]
    incidents = silver.tables["silver_incident"]
    feedback = silver.tables["silver_customer_feedback"]
    results: dict[str, dict[str, float]] = {}
    for phase in ("baseline", "improvement"):
        phase_flights = [row for row in flights if row["phase"] == phase]
        completed_flights = [row for row in phase_flights if not row["cancelled"] and not row["diverted"]]
        flight_ids = {row["flight_id"] for row in phase_flights}
        phase_queues = [row for row in queues if row["phase"] == phase]
        phase_retail = [row for row in retail if row["phase"] == phase]
        phase_energy = [row for row in energy if row["phase"] == phase]
        phase_regulatory = [row for row in regulatory if row["phase"] == phase]
        phase_baggage = [row for row in baggage if row["phase"] == phase]
        phase_workforce = [row for row in workforce if row["phase"] == phase]
        phase_maintenance = [row for row in maintenance if row["phase"] == phase]
        phase_telemetry = [row for row in telemetry if row["phase"] == phase]
        phase_incidents = [row for row in incidents if row["phase"] == phase]
        phase_feedback = [row for row in feedback if row["phase"] == phase]
        passengers = sum(row["passenger_count"] for row in phase_flights)
        gross_revenue = sum(row["gross_revenue_eur"] for row in phase_retail)
        net_revenue = gross_revenue - sum(row["refund_eur"] for row in phase_retail)
        wait_values = [float(row["wait_minutes"]) for row in phase_queues]
        arrival_delays = [float(row["arrival_delay_minutes"]) for row in completed_flights]
        departure_delays = [float(row["departure_delay_minutes"]) for row in completed_flights]
        baseline_days = max(1, config.history_days // 2)
        phase_days = baseline_days if phase == "baseline" else config.history_days - baseline_days
        results[phase] = {
            "flight_count": float(len(phase_flights)),
            "on_time_arrival_0_rate": sum(value <= 0 for value in arrival_delays) / max(1, len(arrival_delays)),
            "on_time_arrival_15_rate": sum(value <= 15 for value in arrival_delays) / max(1, len(arrival_delays)),
            "on_time_arrival_30_rate": sum(value <= 30 for value in arrival_delays) / max(1, len(arrival_delays)),
            "on_time_departure_0_rate": sum(value <= 0 for value in departure_delays) / max(1, len(departure_delays)),
            "on_time_departure_15_rate": sum(value <= 15 for value in departure_delays) / max(1, len(departure_delays)),
            "on_time_departure_30_rate": sum(value <= 30 for value in departure_delays) / max(1, len(departure_delays)),
            "average_arrival_delay_minutes": mean(arrival_delays) if arrival_delays else 0.0,
            "average_departure_delay_minutes": mean(departure_delays) if departure_delays else 0.0,
            "delay_p50_minutes": _percentile(departure_delays, 0.50),
            "delay_p90_minutes": _percentile(departure_delays, 0.90),
            "delay_p95_minutes": _percentile(departure_delays, 0.95),
            "cancellation_rate": sum(row["cancelled"] for row in phase_flights) / max(1, len(phase_flights)),
            "diversion_rate": sum(row["diverted"] for row in phase_flights) / max(1, len(phase_flights)),
            "average_turnaround_minutes": mean(float(row["turnaround_minutes"]) for row in completed_flights),
            "turnaround_p50_minutes": _percentile([float(row["turnaround_minutes"]) for row in completed_flights], 0.50),
            "turnaround_p90_minutes": _percentile([float(row["turnaround_minutes"]) for row in completed_flights], 0.90),
            "turnaround_p95_minutes": _percentile([float(row["turnaround_minutes"]) for row in completed_flights], 0.95),
            "turnaround_target_attainment_rate": sum(float(row["turnaround_minutes"]) <= 38 for row in completed_flights) / max(1, len(completed_flights)),
            "queue_wait_p50_minutes": _percentile(wait_values, 0.50),
            "queue_wait_p90_minutes": _percentile(wait_values, 0.90),
            "queue_wait_p95_minutes": _percentile(wait_values, 0.95),
            "missed_preferred_boarding_rate": sum(row["missed_preferred_boarding_count"] for row in phase_queues) / max(1, sum(row["demand_passengers"] for row in phase_queues)),
            "queue_forecast_accuracy_rate": 1 - sum(abs(row["forecast_wait_minutes"] - row["wait_minutes"]) for row in phase_queues) / max(1.0, sum(row["wait_minutes"] for row in phase_queues)),
            "gross_revenue_per_passenger_eur": gross_revenue / max(1, passengers),
            "net_revenue_per_passenger_eur": net_revenue / max(1, passengers),
            "peer_benchmark_variance_rate": gross_revenue / max(1, passengers) / 8.5 - 1,
            "refund_rate": sum(row["refund_eur"] for row in phase_retail) / max(1.0, gross_revenue),
            "regulatory_activity_annualized": len(phase_regulatory) / max(1, phase_days) * 365,
            "regulatory_automation_coverage_rate": sum(row["automated_preparation"] for row in phase_regulatory) / max(1, len(phase_regulatory)),
            "energy_per_passenger_kwh": sum(row["electricity_kwh"] for row in phase_energy) / max(1, sum(row["passenger_count"] for row in phase_energy)),
            "energy_benchmark_variance_rate": sum(row["electricity_kwh"] for row in phase_energy) / max(1.0, sum(row["benchmark_kwh"] for row in phase_energy)) - 1,
            "emissions_proxy_kgco2e": sum(row["emissions_proxy_kgco2e"] for row in phase_energy),
            "baggage_transfer_success_rate": sum(row["transfer_success"] for row in phase_baggage) / max(1, len(phase_baggage)),
            "baggage_scan_completeness_rate": sum(row["scan_count"] for row in phase_baggage) / max(1, sum(row["expected_scan_count"] for row in phase_baggage)),
            "mishandled_bags_per_1000": sum(row["mishandled"] for row in phase_baggage) / max(1, len(phase_baggage)) * 1000,
            "staffing_coverage_rate": sum(row["scheduled_staff"] for row in phase_workforce) / max(1, sum(row["required_staff"] for row in phase_workforce)),
            "overtime_hours": sum(row["overtime_hours"] for row in phase_workforce),
            "maintenance_backlog": float(sum(row["status"] == "Open" for row in phase_maintenance)),
            "mean_time_to_repair_minutes": mean(float(row["repair_minutes"]) for row in phase_maintenance),
            "first_time_fix_rate": sum(row["first_time_fix"] for row in phase_maintenance) / max(1, len(phase_maintenance)),
            "asset_availability_rate": sum(row["available"] for row in phase_telemetry) / max(1, len(phase_telemetry)),
            "incident_frequency_per_1000_flights": len(phase_incidents) / max(1, len(flight_ids)) * 1000,
            "average_incident_response_minutes": mean(float(row["response_minutes"]) for row in phase_incidents) if phase_incidents else 0.0,
            "average_incident_resolution_minutes": mean(float(row["resolution_minutes"]) for row in phase_incidents) if phase_incidents else 0.0,
            "synthetic_csat": mean(float(row["synthetic_csat"]) for row in phase_feedback),
            "synthetic_nps": mean(float(row["synthetic_nps"]) for row in phase_feedback),
        }
    results["comparison"] = {
        "turnaround_improvement_rate": 1 - results["improvement"]["average_turnaround_minutes"] / results["baseline"]["average_turnaround_minutes"],
        "peak_queue_wait_reduction_rate": 1 - results["improvement"]["queue_wait_p95_minutes"] / results["baseline"]["queue_wait_p95_minutes"],
        "revenue_per_passenger_increase_rate": results["improvement"]["gross_revenue_per_passenger_eur"] / results["baseline"]["gross_revenue_per_passenger_eur"] - 1,
        "energy_efficiency_improvement_rate": 1 - results["improvement"]["energy_per_passenger_kwh"] / results["baseline"]["energy_per_passenger_kwh"],
    }
    return results


def build_gold(silver: SilverResult, config: SimulationConfig) -> GoldResult:
    source_to_gold = {
        "silver_airport": "dim_airport",
        "silver_airline": "dim_airline",
        "silver_aircraft_type": "dim_aircraft_type",
        "silver_aircraft": "dim_aircraft",
        "silver_terminal": "dim_terminal",
        "silver_zone": "dim_zone",
        "silver_gate": "dim_gate",
        "silver_stand": "dim_stand",
        "silver_employee": "dim_employee_pseudonymous",
        "silver_asset": "dim_asset",
        "silver_flight_operation": "fact_flight_operation",
        "silver_turnaround_milestone": "fact_turnaround_milestone",
        "silver_passenger_journey": "fact_passenger_journey_pseudonymous",
        "silver_queue_observation": "fact_queue_observation",
        "silver_baggage_journey": "fact_baggage_journey",
        "silver_retail_transaction": "fact_retail_transaction",
        "silver_workforce_shift": "fact_workforce_shift",
        "silver_weather_observation": "fact_weather_observation",
        "silver_energy_observation": "fact_energy_observation",
        "silver_asset_telemetry": "fact_asset_telemetry",
        "silver_maintenance_work_order": "fact_maintenance_work_order",
        "silver_incident": "fact_incident",
        "silver_customer_feedback": "fact_customer_feedback",
        "silver_regulatory_workflow": "fact_regulatory_workflow",
    }
    tables = {gold_name: [dict(row) for row in silver.tables[source_name]] for source_name, gold_name in source_to_gold.items()}
    kpis = calculate_kpis(silver, config)
    tables["gold_phase_kpi"] = [
        {
            "kpi_id": f"SYN-KPI-{phase.upper()}-{name.upper()}",
            "phase": phase,
            "kpi_name": name,
            "kpi_value": round(value, 8),
            "is_simulated": True,
            "advisory_only": True,
            "data_classification": "DerivedAnalytical",
        }
        for phase in ("baseline", "improvement", "comparison")
        for name, value in sorted(kpis[phase].items())
    ]
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for row in silver.tables["silver_airport"]:
        nodes.append({"node_id": row["airport_id"], "node_type": "Airport", "business_key": row["iata_code"], "approved_source": "dim_airport", "data_classification": "DerivedAnalytical"})
    for row in silver.tables["silver_terminal"]:
        nodes.append({"node_id": row["terminal_id"], "node_type": "Terminal", "business_key": row["terminal_id"], "approved_source": "dim_terminal", "data_classification": "DerivedAnalytical"})
        edges.append({"edge_id": f"SYN-EDGE-{stable_uuid('contains', row['airport_id'], row['terminal_id'])}", "from_node_id": row["airport_id"], "to_node_id": row["terminal_id"], "relationship_type": "CONTAINS", "data_classification": "DerivedAnalytical"})
    for row in silver.tables["silver_flight_operation"]:
        nodes.append({"node_id": row["flight_id"], "node_type": "Flight", "business_key": row["flight_id"], "approved_source": "fact_flight_operation", "data_classification": "DerivedAnalytical"})
        edges.append({"edge_id": f"SYN-EDGE-{stable_uuid('origin', row['origin_airport_id'], row['flight_id'])}", "from_node_id": row["origin_airport_id"], "to_node_id": row["flight_id"], "relationship_type": "ORIGIN_FOR", "data_classification": "DerivedAnalytical"})
    tables["gold_ontology_node"] = sorted(nodes, key=lambda row: row["node_id"])
    tables["gold_ontology_edge"] = sorted(edges, key=lambda row: row["edge_id"])
    return GoldResult(tables=tables, kpis=kpis)


def run_pipeline(simulation: SimulationResult) -> PipelineResult:
    bronze = build_bronze(simulation)
    silver = conform_silver(bronze)
    gold = build_gold(silver, simulation.config)
    return PipelineResult(simulation=simulation, bronze=bronze, silver=silver, gold=gold)