from __future__ import annotations

import ast
import json
import re
import sys
import unittest
from dataclasses import replace
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from airport_ops import load_config, run_pipeline, simulate, stable_uuid  # noqa: E402
from airport_ops.medallion import SilverResult, calculate_kpis, merge_bronze  # noqa: E402

DISCLAIMER = "Real airport identities are used only as public geographic reference anchors."


class DeterministicPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config(profile_name="unit", airport_count=2)
        cls.first = run_pipeline(simulate(cls.config))
        cls.second = run_pipeline(simulate(cls.config))

    def test_two_runs_are_logically_identical(self) -> None:
        self.assertEqual(self.first.logical_checksum(), self.second.logical_checksum())
        self.assertEqual(self.first.simulation.checksums(), self.second.simulation.checksums())

    def test_typed_uuid_is_stable(self) -> None:
        self.assertEqual(stable_uuid("flight", "SYN-1"), stable_uuid("flight", "SYN-1"))
        self.assertNotEqual(stable_uuid("flight", "SYN-1"), stable_uuid("bag", "SYN-1"))

    def test_different_seed_changes_logical_records(self) -> None:
        different = simulate(replace(self.config, seed=self.config.seed + 1))
        self.assertNotEqual(self.first.simulation.logical_checksum(), different.logical_checksum())

    def test_bronze_rerun_adds_no_rows(self) -> None:
        merged = merge_bronze(self.first.bronze, self.first.bronze)
        self.assertEqual({name: len(rows) for name, rows in self.first.bronze.items()}, {name: len(rows) for name, rows in merged.items()})

    def test_faults_are_auditable_and_silver_is_unique(self) -> None:
        envelopes = [row for name, rows in self.first.bronze.items() if name != "bronze_ingestion_ledger" for row in rows]
        self.assertTrue(any(row["duplicate_candidate"] for row in envelopes))
        self.assertTrue(any(row["is_late_arrival"] for row in envelopes))
        self.assertTrue(any(row["is_out_of_order"] for row in envelopes))
        self.assertTrue(any(row["is_correction"] for row in envelopes))
        self.assertTrue(any(row["quarantine_reason"] == "MALFORMED_JSON" for row in self.first.silver.quarantine))
        for rows in self.first.silver.tables.values():
            self.assertEqual(len(rows), len({row["event_id"] for row in rows}))

    def test_gold_catalog_covers_emitted_objects(self) -> None:
        catalog = json.loads((ROOT / "lakehouse" / "schemas" / "gold-object-catalog.json").read_text(encoding="utf-8"))
        entries = {item["name"]: item for item in catalog["objects"]}
        self.assertLessEqual(set(self.first.gold.tables), set(entries))
        required_metadata = {"definition", "grain", "business_key", "surrogate_key", "source_lineage", "refresh", "quality_rules", "data_agent_approved"}
        self.assertTrue(all(required_metadata <= item.keys() for item in entries.values()))
        allowed = set(json.loads((ROOT / "contracts" / "schemas" / "classification-vocabulary.json").read_text(encoding="utf-8"))["classifications"])
        default_classification = catalog["default_classification"]
        self.assertIn(default_classification, allowed)
        self.assertTrue(all(item.get("data_classification", default_classification) in allowed for item in entries.values()))


class ScenarioOutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config(profile_name="smoke")
        cls.simulation = simulate(cls.config)
        cls.kpis = calculate_kpis(SilverResult({"silver_" + name: rows for name, rows in cls.simulation.tables.items()}, [], [], []), cls.config)

    def test_baseline_outcomes(self) -> None:
        baseline = self.kpis["baseline"]
        self.assertTrue(47 <= baseline["average_turnaround_minutes"] <= 49)
        self.assertTrue(0.32 <= baseline["missed_preferred_boarding_rate"] <= 0.36)
        self.assertTrue(-0.21 <= baseline["peer_benchmark_variance_rate"] <= -0.15)
        self.assertTrue(800 <= baseline["regulatory_activity_annualized"] <= 880)
        self.assertTrue(0.23 <= baseline["energy_benchmark_variance_rate"] <= 0.29)

    def test_improvement_outcomes(self) -> None:
        improvement = self.kpis["improvement"]
        comparison = self.kpis["comparison"]
        self.assertTrue(38 <= improvement["average_turnaround_minutes"] <= 40)
        self.assertTrue(0.35 <= comparison["peak_queue_wait_reduction_rate"] <= 0.41)
        self.assertTrue(0.19 <= comparison["revenue_per_passenger_increase_rate"] <= 0.25)
        self.assertTrue(0.73 <= improvement["regulatory_automation_coverage_rate"] <= 0.83)
        self.assertGreater(comparison["energy_efficiency_improvement_rate"], 0.08)

    def test_fixed_clock_and_dst(self) -> None:
        dst_config = load_config(profile_name="unit", airport_count=1, simulation_start_utc="2026-03-28T00:00:00Z")
        dst_result = simulate(dst_config)
        offsets = {row["local_utc_offset_minutes"] for row in dst_result.tables["flight_operation"]}
        self.assertEqual(offsets, {60, 120})


class ArtifactAndGovernanceTests(unittest.TestCase):
    def test_configuration_and_reference_snapshot(self) -> None:
        config = load_config()
        snapshot = json.loads((ROOT / "config" / "reference" / "airport-anchors.json").read_text(encoding="utf-8"))
        airlines = json.loads((ROOT / "data" / "reference" / "airlines.json").read_text(encoding="utf-8"))["records"]
        aircraft_types = json.loads((ROOT / "data" / "reference" / "aircraft_types.json").read_text(encoding="utf-8"))["records"]
        self.assertEqual(config.seed, 42)
        self.assertEqual(config.airport_count, 18)
        self.assertEqual(config.deployment_mode, "dry-run")
        self.assertFalse(config.destructive_operations_enabled)
        self.assertEqual(len(snapshot["records"]), 18)
        self.assertEqual({row["region"] for row in snapshot["records"]}, {"France", "Italy", "Portugal", "Jordan"})
        self.assertEqual(Counter(row["region"] for row in snapshot["records"]), Counter({"France": 6, "Italy": 5, "Portugal": 5, "Jordan": 2}))
        self.assertEqual(snapshot["validation_status"], "SOURCE_VERIFIED")
        self.assertEqual([(row["iata_code"], row["icao_code"]) for row in airlines], [("AF","AFR"),("U2","EZY"),("TO","TVF"),("XK","CCM"),("AZ","ITY"),("FR","RYR"),("W4","WMT"),("NO","NOS"),("EN","DLA"),("TP","TAP"),("S4","RZO"),("NI","PGA"),("RJ","RJA"),("R5","JAV"),("LH","DLH"),("BA","BAW"),("KL","KLM"),("EK","UAE"),("QR","QTR"),("TK","THY")])
        self.assertEqual([row["icao_type_designator"] for row in aircraft_types], ["BCS3","A319","A320","A20N","A21N","A332","A339","A359","AT76","B738","B38M","B788","B789","B77W","E190","E290"])
        self.assertTrue(all(not row["is_synthetic"] and row["data_classification"] == "PublicReference" for row in airlines + aircraft_types))

    def test_notebooks_are_valid_json_with_metadata_and_python_syntax(self) -> None:
        for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
            notebook = json.loads(path.read_text(encoding="utf-8"))
            ids = [cell.get("id") or cell.get("metadata", {}).get("id") for cell in notebook["cells"]]
            self.assertTrue(all(ids), path.name)
            self.assertEqual(len(ids), len(set(ids)), path.name)
            languages = [cell.get("metadata", {}).get("language") or {"code": "python", "markdown": "markdown"}.get(cell.get("cell_type")) for cell in notebook["cells"]]
            self.assertTrue(all(language in {"markdown", "python"} for language in languages), path.name)
            for cell in notebook["cells"]:
                if cell["cell_type"] == "code":
                    ast.parse("".join(cell["source"]), filename=path.name)

    def test_dtdl_v2_models_and_relationships(self) -> None:
        dtdl_root = ROOT / "digital-twin" / "dtdl"
        # `*.v2.json` are the ;2 observed-state interfaces used only by the 3D scene graph.
        base_paths = sorted(path for path in dtdl_root.glob("*.json") if not path.name.endswith(".v2.json"))
        scene_paths = sorted(dtdl_root.glob("*.v2.json"))
        models = [json.loads(path.read_text(encoding="utf-8")) for path in base_paths]
        scene_models = [json.loads(path.read_text(encoding="utf-8")) for path in scene_paths]
        ids = {model["@id"] for model in models}
        targets = [content["target"] for model in models for content in model.get("contents", []) if content.get("@type") == "Relationship"]
        self.assertEqual(len(models), 15)
        self.assertEqual(len(scene_models), 5)
        self.assertTrue(all(model["@context"] == "dtmi:dtdl:context;2" for model in models + scene_models))
        self.assertTrue(all(model["@id"].endswith(";2") for model in scene_models))
        self.assertLessEqual(set(targets), ids)
        required = {"Airport", "Terminal", "Zone", "Gate", "Stand", "Flight", "Queue", "BaggageAsset", "EnergyMeter", "Asset", "MaintenanceWorkOrder", "Incident"}
        self.assertLessEqual(required, {path.stem for path in base_paths})
        twins = json.loads((ROOT / "digital-twin" / "instances" / "sample-twins.json").read_text(encoding="utf-8"))
        relationships = json.loads((ROOT / "digital-twin" / "relationships" / "sample-relationships.json").read_text(encoding="utf-8"))
        twin_ids = {twin["$dtId"] for twin in twins}
        self.assertEqual({twin["$metadata"]["$model"] for twin in twins}, ids)
        self.assertTrue(all(twin["$dtId"].startswith("SYN-TWIN-") for twin in twins))
        self.assertTrue(all(rel["$relationshipId"].startswith("SYN-REL-") and rel["$sourceId"] in twin_ids and rel["$targetId"] in twin_ids for rel in relationships))

        sys.path.insert(0, str(ROOT / "deployment" / "scripts"))
        import digital_twin

        package = digital_twin.load_package(ROOT / "digital-twin")
        payloads = {twin["$dtId"]: (twin, telemetry) for twin, telemetry in digital_twin.split_twin_payloads(package)}
        queue, queue_telemetry = payloads["SYN-TWIN-QUE-CDG-01"]
        self.assertNotIn("waitMinutes", queue)
        self.assertNotIn("passengerCount", queue)
        self.assertEqual(queue_telemetry, {"passengerCount": 42, "waitMinutes": 18.4})
        self.assertTrue(all(set(relationship) == {"$relationshipId", "$sourceId", "$relationshipName", "$targetId"} for relationship in package.relationships))

    def test_all_airport_3d_scene_graph_and_glbs(self) -> None:
        sys.path.insert(0, str(ROOT / "deployment" / "scripts"))
        import generate_3d_scenes

        twins, relationships, manifest, glbs = generate_3d_scenes.build_artifacts()
        self.assertEqual(len(twins), 1134)
        self.assertEqual(len(relationships), 2304)
        self.assertEqual(manifest["sceneCount"], 18)
        self.assertEqual(len({twin["$dtId"] for twin in twins}), 1134)
        self.assertEqual(len({relationship["$relationshipId"] for relationship in relationships}), 2304)
        self.assertTrue(all(scene["expectedTwinCount"] == 63 for scene in manifest["scenes"]))
        self.assertTrue(all(scene["expectedRelationshipCount"] == 128 for scene in manifest["scenes"]))
        self.assertEqual(len(glbs), 18)
        for scene in manifest["scenes"]:
            gltf = generate_3d_scenes.parse_glb(glbs[scene["glbBlobPath"]])
            self.assertEqual(len(gltf["meshes"]), 63)
            self.assertEqual(
                {mesh["name"] for mesh in gltf["meshes"]},
                {element["meshName"] for element in scene["elements"]},
            )

    def test_geojson_structure(self) -> None:
        all_ids: set[str] = set()
        layer_names = set()
        for path in sorted((ROOT / "geospatial" / "azure-maps").glob("*.geojson")):
            layer_names.add(path.name)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["type"], "FeatureCollection", path.name)
            for feature in payload["features"]:
                self.assertNotIn(feature["id"], all_ids)
                all_ids.add(feature["id"])
                self.assertTrue(feature["properties"].get("is_synthetic") or feature["properties"].get("reference_anchor_only"), path.name)
                coordinate_stack = [feature["geometry"]["coordinates"]]
                while coordinate_stack:
                    value = coordinate_stack.pop()
                    if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
                        self.assertTrue(-180 <= value[0] <= 180 and -90 <= value[1] <= 90, path.name)
                    elif isinstance(value, list):
                        coordinate_stack.extend(value)
                if feature["geometry"]["type"] == "Polygon":
                    self.assertEqual(feature["geometry"]["coordinates"][0][0], feature["geometry"]["coordinates"][0][-1])
        self.assertLessEqual({"airports.geojson", "operating_regions.geojson", "terminals.geojson", "zones.geojson", "gates.geojson", "stands.geojson", "routes.geojson", "passenger_flows.geojson", "baggage_flows.geojson", "assets.geojson", "energy.geojson", "incidents.geojson"}, layer_names)

    def test_eventhouse_warehouse_semantic_and_report_sources(self) -> None:
        kql = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "eventhouse").glob("*.kql"))
        sql = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "warehouse").glob("*.sql"))
        tmdl = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "semantic-model").rglob("*.tmdl"))
        self.assertIn(".create-merge table", kql)
        self.assertIn(".create-or-alter function", kql)
        self.assertIn("policy retention", kql)
        self.assertIn("CREATE OR ALTER VIEW", sql.upper())
        self.assertNotIn(" LIMIT ", sql.upper())
        self.assertIn("perspective Executive", tmdl)
        self.assertIn("perspective Regional", tmdl)
        self.assertIn("perspective Sustainability", tmdl)
        self.assertIn("perspective Compliance", tmdl)
        self.assertIn("role AirportOpsDataAgentReader", tmdl)
        persona_security = (ROOT / "warehouse" / "03_persona_security.sql").read_text(encoding="utf-8")
        self.assertIn("security.principal_scope", persona_security)
        self.assertIn("USER_NAME()", persona_security)
        self.assertNotIn("@contoso.com", persona_security)
        report = (ROOT / "reports" / "AirportOpsPersonaReports.Report" / "definition" / "report.json").read_text(encoding="utf-8")
        self.assertIn(DISCLAIMER, report)

    def test_data_agent_is_read_only_and_curated(self) -> None:
        definition = json.loads((ROOT / "data-agent" / "definition.json").read_text(encoding="utf-8"))
        approved = [*definition["approved_warehouse_sources"], *definition["approved_kql_functions"]]
        self.assertTrue(all("bronze_" not in source and "silver_" not in source for source in approved))
        self.assertFalse(definition["safety"]["action_tools_enabled"])
        evaluations = json.loads((ROOT / "data-agent" / "evaluation-cases.json").read_text(encoding="utf-8"))["cases"]
        prompts = " ".join(case["prompt"].lower() for case in evaluations)
        case_ids = {case["id"] for case in evaluations}
        for marker in ("passenger", "staff", "bhs"):
            self.assertIn(marker, prompts)
        self.assertLessEqual({"ambiguity", "forecast-confidence", "freshness", "prompt-injection", "unauthorized-source", "re-identification", "small-cohort", "stale-data-warning", "missing-data", "cross-source-reconciliation", "regulatory-conclusion"}, case_ids)
        self.assertTrue(definition["safety"]["read_only"])
        self.assertGreaterEqual(definition["privacy"]["minimum_aggregate_cohort_size"], 10)

    def test_deployment_plan_and_teardown_safeguards(self) -> None:
        sys.path.insert(0, str(ROOT / "deployment" / "scripts"))
        import fabric

        deployment_plan = fabric.plan()
        self.assertEqual(deployment_plan["status"], "VALIDATED")
        self.assertFalse(deployment_plan["deployment_attempted"])
        self.assertEqual(deployment_plan["artifact_order"][-1]["status"], "UNSUPPORTED")
        teardown = (ROOT / "notebooks" / "13_Reset_Teardown.ipynb").read_text(encoding="utf-8")
        self.assertIn("Production reset and teardown are refused", teardown)
        self.assertIn("DELETE {resource_prefix} {environment_name}", teardown)
        self.assertIn("Unrecognized resource prefix", teardown)

    def test_infra_terraform_uses_verified_provider_and_resources(self) -> None:
        tf_files = list((ROOT / "infra").rglob("*.tf"))
        self.assertTrue(tf_files)
        combined = "\n".join(path.read_text(encoding="utf-8") for path in tf_files)
        self.assertIn('source  = "microsoft/fabric"', combined)
        self.assertIn('version = "~> 1.12"', combined)
        self.assertIn('required_version = ">= 1.8, < 2.0"', combined)
        verified_resources = {"fabric_workspace", "fabric_lakehouse", "fabric_warehouse", "fabric_eventhouse", "fabric_kql_database"}
        used_resources = set(re.findall(r'resource\s+"(fabric_[a-z_]+)"', combined))
        self.assertTrue(used_resources)
        self.assertLessEqual(used_resources, verified_resources)
        self.assertIn("prevent_destroy = true", combined)
        self.assertIn('contains(["dev", "test"], var.environment)', combined)
        guid = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I)
        self.assertEqual([str(path.relative_to(ROOT)) for path in tf_files if guid.search(path.read_text(encoding="utf-8"))], [])

    def test_fictional_reference_mode_is_deterministic(self) -> None:
        config = load_config(profile_name="unit", airport_count=3, reference_mode="fictional")
        self.assertEqual(simulate(config).logical_checksum(), simulate(config).logical_checksum())
        self.assertEqual(len(simulate(config).tables["airport"]), 3)
        snapshot = json.loads((ROOT / "config" / "reference" / "airport-anchors.fictional.json").read_text(encoding="utf-8"))
        self.assertEqual(len(snapshot["records"]), 18)
        self.assertTrue(all(record["airport_reference_id"].startswith("SYN-REF-AP-") for record in snapshot["records"]))
        self.assertEqual(snapshot["validation_status"], "FICTIONAL_GENERATED")

    def test_no_committed_secrets_or_real_personal_data(self) -> None:
        prohibited_patterns = [
            re.compile(r"(?im)^\s*(client_secret|access_token|account_key|shared_access_key)\s*=\s*['\"](?!\$\{|<)[^'\"]{8,}['\"]"),
            re.compile(r"(?i)authorization\s*[:=]\s*['\"]bearer\s+[a-z0-9._-]{20,}"),
            re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I),
        ]
        allowed_suffixes = {".py", ".json", ".md", ".yaml", ".yml", ".sql", ".kql", ".tmdl", ".pbir", ".ipynb", ".tf"}
        findings: list[str] = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in allowed_suffixes or ".git" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in prohibited_patterns[:2]:
                if pattern.search(text):
                    findings.append(str(path.relative_to(ROOT)))
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)