from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

if __name__ == "__main__":
    raise SystemExit(subprocess.run([sys.executable, str(Path(__file__).with_name("validate_platform.py"))], check=False).returncode)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "tests" / "validation-manifest.json").read_text(encoding="utf-8"))
failures: list[str] = []
passes = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passes
    status = "PASS" if condition else "FAIL"
    print(f"{status:4} {name}: {detail}")
    if condition:
        passes += 1
    else:
        failures.append(f"{name}: {detail}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def coordinate_pairs(value: Any) -> Iterable[tuple[float, float]]:
    if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
        yield float(value[0]), float(value[1])
        return
    if isinstance(value, list):
        for item in value:
            yield from coordinate_pairs(item)


config = load_json(ROOT / "config" / "demo_config.json")
check("config.synthetic", config.get("is_synthetic") is True, str(config.get("is_synthetic")))
check("config.seed", config.get("random_seed") == MANIFEST["random_seed"], str(config.get("random_seed")))
check("config.base_date", config.get("base_date") == MANIFEST["base_date"], str(config.get("base_date")))
required_fabric_items = {
    "workspace_name", "lakehouse_name", "warehouse_name", "eventhouse_name",
    "kql_database_name", "semantic_model_name", "report_name", "data_agent_name", "app_name",
}
check(
    "config.fabric_items",
    required_fabric_items == set(config.get("fabric_items", {})),
    f"items={len(config.get('fabric_items', {}))}",
)
check(
    "config.deployment_identity",
    config.get("deployment", {}).get("authentication") == "notebookutils.credentials.getToken"
    and config.get("deployment", {}).get("workspace_id_environment_variable") == "FABRIC_WORKSPACE_ID",
    "runtime identity only",
)
check("config.reference_counts", (config.get("airport_count"), config.get("airline_count"), config.get("aircraft_type_count"), config.get("operating_region_count")) == (15, 20, 16, 4), "15/20/16/4")
check("config.runtime_capacity", config.get("deployment", {}).get("capacity_reference_environment_variable") == "FABRIC_CAPACITY_REFERENCE" and config.get("deployment", {}).get("dry_run") is True, "runtime reference and dry-run default")
check(
    "config.safety_boundary",
    set(config.get("prohibited_control_targets", [])) == {"ATC", "AODB", "BHS", "BMS", "aircraft", "equipment", "staff"},
    "all control targets prohibited",
)

airports_reference = load_json(ROOT / "data" / "reference" / "airports.json")["records"]
airlines_reference = load_json(ROOT / "data" / "reference" / "airlines.json")["records"]
aircraft_reference = load_json(ROOT / "data" / "reference" / "aircraft_types.json")["records"]
source_manifest = load_json(ROOT / "data" / "reference" / "source_manifest.json")
check("reference.airports", len(airports_reference) == 15, str(len(airports_reference)))
check("reference.airlines", len(airlines_reference) == 20, str(len(airlines_reference)))
check("reference.aircraft_types", len(aircraft_reference) == 16, str(len(aircraft_reference)))
check("reference.region_distribution", Counter(item["country"] for item in airports_reference) == Counter({"Northstar": 4, "Meridian": 4, "Coastlight": 4, "Sunreach": 3}), str(Counter(item["country"] for item in airports_reference)))
check("reference.airport_codes", len({item["iata_code"] for item in airports_reference}) == 15 and len({item["icao_code"] for item in airports_reference}) == 15, "unique IATA/ICAO")
check("reference.airline_codes", len({item["iata_code"] for item in airlines_reference}) == 20 and len({item["icao_code"] for item in airlines_reference}) == 20, "unique IATA/ICAO")
valid_time_zones = {"Etc/UTC", "Etc/GMT-1", "Etc/GMT+1", "Etc/GMT-3"}
check("reference.wgs84_iana", all(-90 <= item["latitude"] <= 90 and -180 <= item["longitude"] <= 180 and item["iana_time_zone"] in valid_time_zones for item in airports_reference), "coordinate ranges and required IANA IDs")
check("reference.synthetic_classification", all(item["is_synthetic"] is True and item.get("data_classification") == "Synthetic master data" for item in airports_reference + airlines_reference + aircraft_reference), "all reference entities are fictional")
check("reference.provenance", all(item.get("source_name") == "DeterministicFictionalReferenceGenerator" and item.get("source_url") == "repo://data/reference/generate_fictional_reference.py" and item.get("source_as_of_date") == config["base_date"] for item in airports_reference + airlines_reference + aircraft_reference), "per-record generator provenance")
check("reference.fictional_scope", "every entity" in source_manifest["fictional_scope_statement"].lower() and "fictional" in source_manifest["fictional_scope_statement"].lower(), "all-fictional scope")

notebook_paths = sorted((ROOT / "notebooks").glob("*.ipynb"))
check("notebooks.count", len(notebook_paths) == MANIFEST["expected_notebooks"], str(len(notebook_paths)))
for path in notebook_paths:
    notebook = load_json(path)
    cells = notebook.get("cells", [])
    ids = [cell.get("id") or cell.get("metadata", {}).get("id") for cell in cells]
    check(f"notebook.{path.stem}.nbformat", notebook.get("nbformat") == 4, str(notebook.get("nbformat")))
    check(f"notebook.{path.stem}.cell_ids", all(ids) and len(ids) == len(set(ids)), f"cells={len(cells)}")
    languages = [cell.get("metadata", {}).get("language") or {"code": "python", "markdown": "markdown"}.get(cell.get("cell_type")) for cell in cells]
    check(f"notebook.{path.stem}.languages", all(language in {"markdown", "python"} for language in languages), "metadata.language or nbformat cell_type")
    try:
        for cell in cells:
            if cell.get("cell_type") == "code":
                ast.parse("".join(cell.get("source", [])))
        syntax_ok = True
        syntax_detail = "Python cells parse"
    except SyntaxError as exc:
        syntax_ok = False
        syntax_detail = f"{exc.msg} at line {exc.lineno}"
    check(f"notebook.{path.stem}.syntax", syntax_ok, syntax_detail)

model_paths = sorted((ROOT / "digital-twin" / "dtdl").glob("*.json"))
models = [load_json(path) for path in model_paths]
model_ids = {model.get("@id") for model in models}
check("dtdl.model_count", len(models) == MANIFEST["expected_dtdl_models"], str(len(models)))
check("dtdl.unique_ids", len(model_ids) == len(models) and None not in model_ids, str(len(model_ids)))
check("dtdl.context", all(model.get("@context") == "dtmi:dtdl:context;3" for model in models), "DTDL v3")
targets = [
    content["target"]
    for model in models
    for content in model.get("contents", [])
    if content.get("@type") == "Relationship"
]
targets.extend(model["extends"] for model in models if "extends" in model)
check("dtdl.relationship_targets", all(target in model_ids for target in targets), f"targets={len(targets)}")
check(
    "dtdl.unique_content_names",
    all(len([item["name"] for item in model.get("contents", [])]) == len({item["name"] for item in model.get("contents", [])}) for model in models),
    "no duplicate names per interface",
)

twins = load_json(ROOT / "digital-twin" / "instances" / "sample-twins.json")
relationships = load_json(ROOT / "digital-twin" / "relationships" / "sample-relationships.json")
twin_ids = {twin["$dtId"] for twin in twins}
check("twins.count", len(twins) == MANIFEST["expected_twin_instances"], str(len(twins)))
check("twins.models", all(twin["$metadata"]["$model"] in model_ids for twin in twins), "all models resolve")
check("twins.classification", all(twin.get("isSynthetic") is True for twin in twins), "all twins are synthetic")
check("relationships.count", len(relationships) == MANIFEST["expected_twin_relationships"], str(len(relationships)))
check(
    "relationships.endpoints",
    all(rel["$sourceId"] in twin_ids and rel["$targetId"] in twin_ids for rel in relationships),
    "all endpoints resolve",
)

known_airports = {f"AP{number}" for number in range(1, config["airport_count"] + 1)}
known_terminals = {f"{airport}-T{number}" for airport in known_airports for number in range(1, config["terminals_per_airport"] + 1)}
known_zones = {f"{terminal}-Z{number}" for terminal in known_terminals for number in range(1, config["zones_per_terminal"] + 1)}
known_gates = {f"{airport}-G{number}" for airport in known_airports for number in range(1, config["gates_per_airport"] + 1)}
known_stands = {f"{airport}-S{number}" for airport in known_airports for number in range(1, config["gates_per_airport"] + 1)}
checkpoint_codes = {"CHK", "SEC", "IMM", "BRD"}
known_checkpoints = {f"{airport}-CP-{code}" for airport in known_airports for code in checkpoint_codes}
known_assets = {f"{gate}-AST-JTB" for gate in known_gates}
known = {
    "airport_id": known_airports,
    "terminal_id": known_terminals,
    "zone_id": known_zones,
    "checkpoint_id": known_checkpoints,
    "from_checkpoint_id": known_checkpoints,
    "to_checkpoint_id": known_checkpoints,
    "gate_id": known_gates,
    "stand_id": known_stands,
    "asset_id": known_assets,
}

all_feature_ids: set[str] = set()
for file_name, expected in MANIFEST["geojson"].items():
    path = ROOT / "geospatial" / "azure-maps" / file_name
    data = load_json(path)
    features = data.get("features", [])
    check(f"geojson.{file_name}.collection", data.get("type") == "FeatureCollection", data.get("type", "missing"))
    check(f"geojson.{file_name}.count", len(features) == expected["feature_count"], str(len(features)))
    check(
        f"geojson.{file_name}.geometry",
        all(feature.get("geometry", {}).get("type") == expected["geometry_type"] for feature in features),
        expected["geometry_type"],
    )
    check(f"geojson.{file_name}.classification", all(feature.get("properties", {}).get("is_synthetic") is True for feature in features), "all coordinates and geometry are fictional")
    coordinates_ok = all(
        -180 <= longitude <= 180 and -90 <= latitude <= 90
        for feature in features
        for longitude, latitude in coordinate_pairs(feature["geometry"]["coordinates"])
    )
    check(f"geojson.{file_name}.coordinate_range", coordinates_ok, "EPSG:4326 ranges")
    polygons_closed = all(
        feature["geometry"]["coordinates"][0][0] == feature["geometry"]["coordinates"][0][-1]
        for feature in features if feature["geometry"]["type"] == "Polygon"
    )
    check(f"geojson.{file_name}.polygon_closure", polygons_closed, "closed rings")
    file_ids = [feature.get("id") for feature in features]
    check(f"geojson.{file_name}.feature_ids", None not in file_ids and len(file_ids) == len(set(file_ids)) and not all_feature_ids.intersection(file_ids), "globally unique IDs")
    all_feature_ids.update(file_ids)
    orphaned: list[str] = []
    for feature in features:
        for key, valid_values in known.items():
            value = feature.get("properties", {}).get(key)
            if value is not None and value not in valid_values:
                orphaned.append(f"{key}={value}")
    check(f"geojson.{file_name}.keys", not orphaned, ",".join(orphaned[:5]) or "no orphan keys")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    check(f"geojson.{file_name}.hash", digest == expected["sha256"], digest[:12])

ontology = load_json(ROOT / "ontology" / "airport-operations-ontology.yaml")
source_mappings = load_json(ROOT / "ontology" / "source-mappings.yaml")
entities = {entity["name"] for entity in ontology.get("entities", [])}
required_entities = {
    "Airport", "Terminal", "Zone", "Checkpoint", "Gate", "Stand", "Flight", "Turnaround",
    "Airline", "Aircraft", "PassengerFlowObservation", "Asset", "MaintenanceEvent",
    "EnergyObservation", "WeatherObservation", "OperationalIncident", "ServiceTeam", "KPI", "Recommendation",
}
check("ontology.entity_count", len(entities) == MANIFEST["expected_ontology_entities"], str(len(entities)))
check("ontology.required_entities", entities == required_entities, f"mapped={len(entities)}")
check("ontology.source_mapping", entities == set(source_mappings.get("entity_sources", {})), "one mapping per entity")
check("ontology.no_bronze", all(not entity["source"].startswith("bronze_") for entity in ontology["entities"]), "curated sources only")
required_metadata = {"description", "source", "primary_key", "important_properties", "relationships", "synonyms", "security_classification", "supported_measures", "questions"}
check("ontology.metadata", all(required_metadata.issubset(entity) and all(entity[key] for key in required_metadata) for entity in ontology["entities"]), "complete")

warehouse_sql = (ROOT / "warehouse" / "AirportOpsWarehouse_extended.sql").read_text(encoding="utf-8")
required_views = {
    "vw_executive_scorecard", "vw_operational_excellence_scorecard", "vw_airport_performance",
    "vw_terminal_performance", "vw_gate_turnaround_performance", "vw_checkpoint_performance",
    "vw_asset_reliability", "vw_energy_efficiency", "vw_incident_details", "vw_it_service_health",
    "vw_spatial_operational_context", "vw_data_agent_grounding",
}
check("warehouse.rerunnable", warehouse_sql.upper().count("CREATE OR ALTER VIEW") >= 28, f"views={warehouse_sql.upper().count('CREATE OR ALTER VIEW')}")
check("warehouse.required_views", all(view in warehouse_sql for view in required_views), f"required={len(required_views)}")
check("warehouse.no_limit", "LIMIT " not in warehouse_sql.upper(), "Fabric T-SQL compatible paging syntax")

model = (ROOT / "semantic-model" / "model.md").read_text(encoding="utf-8")
measures = (ROOT / "semantic-model" / "measures.dax").read_text(encoding="utf-8")
perspectives = (ROOT / "semantic-model" / "perspectives.md").read_text(encoding="utf-8")
report_paths = sorted((ROOT / "semantic-model" / "report-specifications").glob("*.md"))
check("semantic.relationships", "USERELATIONSHIP" in model and "single-direction" in model, "date roles and filter direction")
check("semantic.perspectives", all(persona in perspectives for persona in ["Airport", "Airline", "Executive", "Operations", "Maintenance", "Commercial", "CustomerExperience", "IT"]), "eight personas")
expected_report_specs = {"Airport", "Airline", "CEO", "CIO", "Commercial", "IT-Professional", "Maintenance", "OEE"}
check("semantic.reports", {path.stem for path in report_paths} == expected_report_specs and all("Drill-through" in path.read_text(encoding="utf-8") for path in report_paths), str(len(report_paths)))
required_measures = ["On-Time Departure %", "Operational Risk Score", "Turnaround Target Adherence %", "Data Quality Pass %", "Recommendations Requiring Approval"]
check("semantic.measures", all(f"{measure} =" in measures for measure in required_measures) and measures.count("(") == measures.count(")"), f"definitions={measures.count(' =')}")

notebook_05 = (ROOT / "notebooks" / "05_Build_Agent_Ontology_Context.ipynb").read_text(encoding="utf-8")
agent_fields = [
    "terminal_id", "zone_id", "stand_id", "asset_id", "observation_timestamp",
    "recommendation_rationale", "confidence_category", "source_table_references",
    "human_approval_required", "data_freshness_indicator", "advisory_only",
]
check("agent_context.extended_schema", all(field in notebook_05 for field in agent_fields), f"fields={len(agent_fields)}")
check("agent_context.backward_compatible", all(field in notebook_05 for field in ["airport_id", "gate_id", "operational_status", "delay_reason", "recommended_action"]), "legacy columns retained")

enterprise_ontology = load_json(ROOT / "ontology" / "enterprise-ontology-extension.yaml")
enterprise_mappings = load_json(ROOT / "ontology" / "enterprise-source-mappings.yaml")
enterprise_entities = {entity["name"] for entity in enterprise_ontology.get("entities", [])}
check(
    "enterprise_ontology.entity_count",
    len(enterprise_entities) == MANIFEST["expected_enterprise_ontology_entities"],
    str(len(enterprise_entities)),
)
check(
    "enterprise_ontology.source_mapping",
    enterprise_entities == set(enterprise_mappings.get("entity_sources", {})),
    "one aggregate mapping per entity",
)
check(
    "enterprise_ontology.curated_only",
    all(
        mapping["view"].startswith("ops.vw_")
        and "bronze_" not in mapping["view"]
        and "silver_" not in mapping["view"]
        for mapping in enterprise_mappings["entity_sources"].values()
    ),
    "Warehouse views only",
)
check(
    "enterprise_ontology.metadata",
    all(required_metadata.issubset(entity) and all(entity[key] for key in required_metadata) for entity in enterprise_ontology["entities"]),
    "complete",
)

eventhouse_paths = sorted((ROOT / "eventhouse").glob("*.kql"))
eventhouse_text = "\n".join(path.read_text(encoding="utf-8") for path in eventhouse_paths)
check("eventhouse.script_count", len(eventhouse_paths) == MANIFEST["expected_eventhouse_scripts"], str(len(eventhouse_paths)))
for marker in [".create-merge table", "ingestion json mapping", "ingestion csv mapping", ".create-or-alter function", "policy update", "materialized-view", "fn_realtime_agent_grounding", ".drop table"]:
    check(f"eventhouse.{marker.replace(' ', '_')}", marker in eventhouse_text, marker)
check("eventhouse.synthetic_filter", eventhouse_text.count("IsSynthetic == true") >= 12, "curated functions and transactional update policies")

enterprise_warehouse = (ROOT / "warehouse" / "01_enterprise_views.sql").read_text(encoding="utf-8")
warehouse_security = (ROOT / "warehouse" / "02_security.sql").read_text(encoding="utf-8")
check(
    "warehouse.enterprise_view_count",
    enterprise_warehouse.upper().count("CREATE OR ALTER VIEW") == MANIFEST["expected_enterprise_warehouse_views"],
    str(enterprise_warehouse.upper().count("CREATE OR ALTER VIEW")),
)
check(
    "warehouse.enterprise_agent_filter",
    "advisory_only = 1 AND is_synthetic = 1" in enterprise_warehouse,
    "agent serving view is filtered",
)
check(
    "warehouse.least_privilege",
    "airport_ops_data_agent_reader" in warehouse_security
    and "GRANT SELECT ON OBJECT::ops.vw_data_agent_grounding" in warehouse_security
    and "GRANT SELECT ON SCHEMA::ops TO airport_ops_data_agent_reader" not in warehouse_security,
    "Data Agent receives object grants only",
)

semantic_project = ROOT / "semantic-model" / "AirportOpsSharedModel.SemanticModel"
tmdl_tables = sorted((semantic_project / "definition" / "tables").glob("*.tmdl"))
tmdl_text = "\n".join(path.read_text(encoding="utf-8") for path in semantic_project.rglob("*.tmdl"))
check("tmdl.table_count", len(tmdl_tables) == MANIFEST["expected_tmdl_tables"], str(len(tmdl_tables)))
check("tmdl.parameterized", "${WAREHOUSE_SERVER}" in tmdl_text and "${WAREHOUSE_DATABASE}" in tmdl_text, "runtime connection parameters")
check("tmdl.personas", all(f"perspective {persona}" in tmdl_text for persona in ["Airport", "Airline", "Executive", "Operations", "Maintenance", "Commercial", "CustomerExperience", "IT"]), "eight perspectives")
check("tmdl.security_role", "role AirportOpsDataAgentReader" in tmdl_text and "[advisory_only] = TRUE()" in tmdl_text, "agent role filter")
for required_measure in ["On-Time Departure %", "On-Time Arrival %", "Turnaround Target Attainment %", "Predicted Congestion Risk %", "Mishandled Bags per 1,000", "Baggage Scan Completeness %", "Roster Coverage %", "Predicted Failure Risk %", "Energy Benchmark Variance %", "Commercial Conversion %", "Recommendation Acceptance %", "Staffing Coverage %", "Asset Availability %", "Synthetic Net Retail Revenue", "Customer Satisfaction", "Data Quality Pass %", "Recommendations Requiring Approval"]:
    check(f"tmdl.measure.{required_measure}", f"measure '{required_measure}'" in tmdl_text, required_measure)

report_project = ROOT / "reports" / "AirportOpsPersonaReports.Report"
pages_metadata = load_json(report_project / "definition" / "pages" / "pages.json")
page_names = pages_metadata.get("pageOrder", [])
visual_paths = sorted(report_project.rglob("visual.json"))
visuals = [load_json(path) for path in visual_paths]
check("pbir.page_count", len(page_names) == MANIFEST["expected_persona_pages"], str(len(page_names)))
required_pages = {f"ReportSection{persona}" for persona in ["Airport", "Airline", "Executive", "Operations", "Maintenance", "Commercial", "CustomerExperience", "IT"]} | {f"ReportSection{name}" for name in ["GroupOverview", "AirportComparison", "FlightPerformance", "TurnaroundControl", "PassengerFlow", "Baggage", "GatesAndStands", "Workforce", "MaintenanceAssets", "Energy", "RetailRevenue", "Incidents", "CustomerExperienceDetail", "DataQualityPlatform"]}
check("pbir.required_pages", set(page_names) == required_pages, f"pages={len(page_names)}")
check("pbir.azure_maps", sum(visual.get("visual", {}).get("visualType") == "azureMap" for visual in visuals) >= 4, "persona and flow/baggage maps")
check("pbir.accessibility", all("altText" in json.dumps(visual) for visual in visuals), f"visuals={len(visuals)}")
for source_path in sorted((ROOT / "geospatial" / "azure-maps").glob("*.geojson")):
    packaged_path = report_project / "definition" / "StaticResources" / "SharedResources" / "GeoJSON" / source_path.name
    check(f"pbir.geojson.{source_path.name}", packaged_path.exists() and packaged_path.read_bytes() == source_path.read_bytes(), "packaged WGS84 resource")

app_manifest = load_json(ROOT / "fabric-app" / "app-manifest.json")
rayfin_module = load_json(ROOT / "fabric-app" / "rayfin-module.json")
agent_definition = load_json(ROOT / "data-agent" / "definition.json")
agent_evaluations = load_json(ROOT / "data-agent" / "evaluation-cases.json")
check("app.personas", {item["audience"] for item in app_manifest["navigation"]} == {"Airport", "Airline", "Executive", "Operations", "Maintenance", "Commercial", "CustomerExperience", "IT"}, "eight audiences")
check("app.advisory_only", app_manifest["safety"]["human_approval_required_for_consequential_recommendations"] is True, "human approval")
check("rayfin.fallback", rayfin_module["native_experience_supported"] is False and rayfin_module["deployment_status_when_native_api_absent"] == "SKIPPED_UNSUPPORTED", "configurable module")
check(
    "data_agent.curated_allowlist",
    all(source.startswith("ops.vw_") and "bronze_" not in source and "silver_" not in source for source in agent_definition["approved_warehouse_sources"]),
    f"sources={len(agent_definition['approved_warehouse_sources'])}",
)
check("data_agent.no_actions", agent_definition["safety"]["action_tools_enabled"] is False, "no action tools")
check("data_agent.evaluations", len(agent_evaluations["cases"]) >= 15 and all(case.get("must_not_include") for case in agent_evaluations["cases"]), str(len(agent_evaluations["cases"])))
check("data_agent.value_semantics", set(agent_definition["answer_contract"]["value_semantics"]) == {"actual", "forecast", "target", "benchmark", "recommendation"}, "five value types")

deployment_manifest = load_json(ROOT / "deployment" / "manifest.json")
deployment_evidence_schema = load_json(ROOT / "deployment" / "evidence-schema.json")
deployment_items = {item["key"]: item for item in deployment_manifest["items"]}
check("deployment.core_items", {"lakehouse", "warehouse", "eventhouse", "kql_database", "semantic_model", "report", "data_agent", "fabric_app", "rayfin"} == set(deployment_items), f"items={len(deployment_items)}")
check("deployment.no_workspace_mutation", "never creates or deletes a workspace" in deployment_manifest["workspace_policy"], deployment_manifest["workspace_policy"])
check("deployment.conditional_honesty", all(deployment_items[key].get("on_unsupported") == "SKIPPED_UNSUPPORTED" for key in ["data_agent", "fabric_app", "rayfin"]), "conditional APIs")
check("deployment.references", all(reference.startswith("https://learn.microsoft.com/") for reference in deployment_manifest["official_references"]), f"references={len(deployment_manifest['official_references'])}")
evidence_fields = set(deployment_evidence_schema["properties"]["artifacts"]["items"]["properties"])
check("deployment.evidence_schema", {"artifact_name", "artifact_type", "deployment_method", "status", "item_id", "dependency_status", "validation_status", "unsupported_manual_status", "error_details", "deployment_timestamp", "request_id"}.issubset(evidence_fields), f"fields={len(evidence_fields)}")
check(
    "deployment.digital_twin_optional",
    len(deployment_manifest.get("optional_external_deployments", [])) == 1
    and deployment_manifest["optional_external_deployments"][0]["default_mode"] == "DRY_RUN"
    and deployment_manifest["optional_external_deployments"][0]["runtime_parameter"] == "digital_twins_endpoint",
    "parameterized external target",
)

notebook_text = {path.stem: path.read_text(encoding="utf-8") for path in notebook_paths}
scaling_keys = [
    "scale_factor", "operating_region_count", "corporate_headquarters_count",
    "airline_count", "routes_per_airport", "employees_per_airport",
    "passengers_per_flight_target", "retail_outlets_per_terminal",
]
check(
    "notebook.config_propagation",
    all(key in notebook_text["01_Generate_Sample_Data"] and key in config for key in scaling_keys),
    f"keys={len(scaling_keys)}",
)
enterprise_bronze_markers = ["bronze_route", "bronze_aircraft_fleet", "bronze_employee_roster", "bronze_passenger", "bronze_booking", "bronze_boarding_event", "bronze_baggage_journey", "bronze_baggage_scan", "bronze_ramp_service_task", "bronze_maintenance_work_order", "bronze_retail_pos", "bronze_turnaround_phase", "bronze_customer_experience", "bronze_recommendation_event"]
check("notebook.enterprise_bronze_domains", all(marker in notebook_text["07_Generate_Enterprise_Bronze"] for marker in enterprise_bronze_markers), f"domains={len(enterprise_bronze_markers)}")
check("notebook.bronze_incremental", all("DeltaTable.forName" in notebook_text[name] and "whenMatchedUpdateAll" in notebook_text[name] and "processing_mode" in notebook_text[name] for name in ["01_Generate_Sample_Data", "07_Generate_Enterprise_Bronze"]), "deterministic MERGE/upsert")
check("notebook.configurable_seed", all("random_seed'] == 42" not in notebook_text[name] for name in ["04_Generate_Physical_Spatial_Context", "05_Build_Agent_Ontology_Context", "06_Validate_Extended_MVP", "07_Generate_Enterprise_Bronze", "08_Enterprise_Bronze_to_Silver", "09_Enterprise_Silver_to_Gold", "12_Validate_Production_Demo"]), "42 is default, not restriction")
check("notebook.runtime_identity", "notebookutils.credentials.getToken" in notebook_text["00_Deploy_Fabric_Items"] and "dry_run = True" in notebook_text["00_Deploy_Fabric_Items"], "runtime token and dry-run default")
check("notebook.orchestration", "jobs/instances?jobType=RunNotebook" in notebook_text["11_Orchestrate_Deployment"] and "SECOND_PASS_DATA" in notebook_text["11_Orchestrate_Deployment"], "job API and second pass")
check("notebook.idempotency", "validation_idempotency_manifest_production" in notebook_text["12_Validate_Production_Demo"] and "xxhash64" in notebook_text["12_Validate_Production_Demo"], "stable fingerprints")
check("notebook.scoped_teardown", "status_detail == 'Created item'" in notebook_text["13_Reset_Teardown"] and "DELETE AIRPORT OPS DEMO" in notebook_text["13_Reset_Teardown"], "ledger ownership and confirmation")
check("notebook.reset_coverage", all(marker in notebook_text["13_Reset_Teardown"] for marker in ["gold_fact_recommendation", "bronze_baggage_scan", "fact_maintenance_work_order", "gold_commercial_kpi"]), "expanded table allowlist")
check("notebook.status", "NOT_AVAILABLE" in notebook_text["15_Deployment_Status"] and "success is not inferred" in notebook_text["15_Deployment_Status"], "evidence-based status")
check(
    "notebook.digital_twin_deployment",
    "digital_twins_endpoint = ''" in notebook_text["14_Deploy_Digital_Twin"]
    and "dry_run = True" in notebook_text["14_Deploy_Digital_Twin"]
    and "notebookutils.credentials.getToken('https://digitaltwins.azure.net/')" in notebook_text["14_Deploy_Digital_Twin"]
    and "Immutable model ID exists with a different definition" in notebook_text["14_Deploy_Digital_Twin"],
    "runtime identity, dry-run, immutable collision protection",
)

for forbidden in ["AccountKey=", "SharedAccessKey=", "Bearer eyJ", "password="]:
    leaked = [
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.resolve() != Path(__file__).resolve()
        and forbidden in path.read_text(encoding="utf-8", errors="ignore")
    ]
    check(f"security.no_{forbidden.rstrip('=')}", not leaked, ",".join(leaked) or "none")

feature_flags = load_json(ROOT / "config" / "feature_flags.json")
environment_example = load_json(ROOT / "config" / "environments.example.json")
approved_sources = load_json(ROOT / "config" / "approved_sources.json")
simulation_profiles = load_json(ROOT / "config" / "simulation_profiles.json")
check("feature_flags.rayfin", feature_flags["features"]["enable_rayfin_module"] is False and rayfin_module["enabled_by_default"] is False, "disabled by default")
check("environment.examples", set(environment_example["environments"]) == {"development", "test", "production"}, "development/test/production")
check("environment.placeholders", all(value["workspace_id"].startswith("${FABRIC_") and value["capacity_reference"].startswith("${FABRIC_") for value in environment_example["environments"].values()), "no committed IDs")
check("simulation.profiles", set(simulation_profiles["profiles"]) == {"small", "medium", "large"} and config["simulation_profile"] in simulation_profiles["profiles"], "small/medium/large")
check("approved_sources.denied", approved_sources["action_tools_enabled"] is False and {"bronze_*", "silver_*"}.issubset(set(approved_sources["deny_patterns"])), "raw layers denied")
required_docs = {"architecture.md", "deployment-runbook.md", "runbook.md", "data-dictionary.md", "kpi-dictionary.md", "security.md", "assumptions.md", "prerequisites.md", "limitations.md", "known-issues.md", "rollback.md", "lineage.md", "source-provenance.md", "persona-mapping.md", "data-agent-governance.md", "cost-and-scale.md", "troubleshooting.md"}
existing_docs = {path.name for path in (ROOT / "docs").glob("*.md")}
check("documentation.coverage", required_docs.issubset(existing_docs), ",".join(sorted(required_docs - existing_docs)) or "complete")
check("ci.portable_validation", (ROOT / ".github" / "workflows" / "validate.yml").exists() and "tests/validate_artifacts.py" in (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8"), "GitHub Actions workflow")
check("contributing.guidance", (ROOT / "CONTRIBUTING.md").exists() and "Safety rules" in (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"), "contribution and safety guidance")
check("notebook.preflight", "workspace_authorization" in notebook_text["00_Validate_Prerequisites"] and "dry_run = True" in notebook_text["00_Validate_Prerequisites"], "dry-run prerequisite checks")

print(f"\nValidation summary: {passes} passed, {len(failures)} failed")
if failures:
    for failure in failures:
        print(" -", failure)
    sys.exit(1)
