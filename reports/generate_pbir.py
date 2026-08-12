from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "AirportOpsPersonaReports.Report"
DEFINITION = REPORT / "definition"
PAGES = DEFINITION / "pages"
GEOJSON_TARGET = REPORT / "StaticResources" / "SharedResources" / "GeoJSON"
DISCLAIMER = "Real airport identities are used only as public geographic reference anchors. All ownership, infrastructure, flights, passengers, employees, operations, performance, incidents, commercial activity, recommendations, and outcomes are synthetic."
ADVISORY_NOTICE = "AI recommendations are advisory, include provenance and confidence, and require human review before any decision."

PERSONAS = {
    "Executive": ("Operational risk and network outcomes", "Executive"),
    "Regional": ("Regional comparison and portfolio outcomes", "Regional"),
    "Airport": ("Airport flow, baggage, and customer experience", "Airport"),
    "Airline": ("Route, load factor, punctuality, and baggage", "Airline"),
    "Operations": ("Turnaround phases, queues, gates, and staffing", "Operations"),
    "Maintenance": ("Asset availability, anomalies, and work coverage", "Maintenance"),
    "Commercial": ("Synthetic retail revenue and customer experience", "Commercial"),
    "Sustainability": ("Synthetic energy, water, and emissions proxies", "Sustainability"),
    "Compliance": ("Synthetic incidents and regulatory preparation", "Compliance"),
    "CustomerExperience": ("Synthetic satisfaction, complaints, disruption, and service recovery", "CustomerExperience"),
    "IT": ("Data quality, freshness, lineage, and capacity proxies", "IT"),
}
PAGE_NAMES = {persona: "ReportSection" + persona for persona in PERSONAS}
DETAIL_PAGES = {
    "GroupOverview": ("Group overview", "gold_persona_scorecard", ["persona", "primary_kpi_name", "primary_kpi_value", "scorecard_status"]),
    "AirportComparison": ("Airport comparison", "dim_airport", ["airport_name", "region", "latitude", "longitude"]),
    "FlightPerformance": ("Flight performance", "gold_flight_operations_kpi", ["on_time_arrival_pct", "on_time_departure_pct", "avg_arrival_delay_min", "avg_departure_delay_min"]),
    "TurnaroundControl": ("Turnaround control", "gold_flight_operations_kpi", ["avg_turnaround_min", "turnaround_target_attainment_pct", "milestone_adherence_pct", "gate_conflict_count"]),
    "PassengerFlow": ("Passenger flow", "gold_passenger_flow_kpi", ["avg_queue_length", "peak_wait_min", "throughput_pax", "predicted_congestion_risk_pct"]),
    "Baggage": ("Baggage", "gold_baggage_kpi", ["bags_processed", "bags_per_flight", "mishandled_bags_per_1000", "scan_completeness_pct"]),
    "GatesAndStands": ("Gates and stands", "gold_flight_operations_kpi", ["gate_utilization_pct", "stand_utilization_pct", "gate_conflict_count"]),
    "Workforce": ("Workforce", "gold_workforce_kpi", ["planned_hours", "actual_hours", "overtime_hours", "roster_coverage_pct", "skill_coverage_pct"]),
    "MaintenanceAssets": ("Maintenance and assets", "gold_maintenance_kpi", ["asset_availability_pct", "failure_count", "mean_time_to_repair_hours", "open_work_order_backlog", "predicted_failure_risk_pct", "avg_inspection_score", "inspection_compliance_pct", "inspection_follow_up_count"]),
    "Energy": ("Energy", "gold_energy_sustainability_kpi", ["total_kwh", "kwh_per_passenger", "kwh_per_flight", "energy_benchmark_variance_pct"]),
    "RetailRevenue": ("Retail and revenue", "gold_commercial_kpi", ["revenue_proxy", "revenue_per_passenger_proxy", "conversion_rate_pct", "average_transaction_value_proxy"]),
    "Incidents": ("Incidents", "gold_incident_customer_kpi", ["incident_count", "incidents_per_100_flights", "high_severity_incidents", "time_to_resolution_proxy_min"]),
    "CustomerExperienceDetail": ("Customer experience", "gold_incident_customer_kpi", ["customer_satisfaction", "synthetic_nps", "complaints_per_1000_responses", "recommendation_acceptance_pct"]),
    "DataQualityPlatform": ("Data quality and platform operations", "gold_it_service_health", ["data_product", "data_quality_pass_pct", "pipeline_run_status", "refresh_status", "security_control_status"]),
}
DETAIL_PAGE_NAMES = {key: "ReportSection" + key for key in DETAIL_PAGES}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def column(entity: str, property_name: str) -> dict[str, object]:
    return {
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": property_name,
            }
        },
        "queryRef": f"{entity}.{property_name}",
        "nativeQueryRef": property_name,
    }


def measure(entity: str, measure_name: str) -> dict[str, object]:
    return {
        "field": {
            "Measure": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": measure_name,
            }
        },
        "queryRef": f"{entity}.{measure_name}",
        "nativeQueryRef": measure_name,
    }


def visual(name: str, visual_type: str, x: int, y: int, width: int, height: int, projections: dict[str, list[dict[str, object]]], title: str) -> dict[str, object]:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.1.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": 0, "height": height, "width": width, "tabOrder": 0},
        "visual": {
            "visualType": visual_type,
            "query": {"queryState": {role: {"projections": values} for role, values in projections.items()}},
            "visualContainerObjects": {
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}}, "text": {"expr": {"Literal": {"Value": "'" + title + "'"}}}}}],
                "general": [{"properties": {"altText": {"expr": {"Literal": {"Value": "'" + title + ". Synthetic demonstration data.'"}}}}}],
            },
        },
        "filterConfig": {"filters": []},
    }


def azure_map(name: str, title: str, geojson_resource: str) -> dict[str, object]:
    value = visual(
        name,
        "azureMap",
        36,
        250,
        760,
        430,
        {"Latitude": [column("dim_airport", "latitude")], "Longitude": [column("dim_airport", "longitude")], "Legend": [column("dim_airport", "region")]},
        title,
    )
    value["visual"]["objects"] = {
        "referenceLayer": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "geoJsonResource": {"expr": {"Literal": {"Value": "'" + geojson_resource + "'"}}},
                    "coordinateSystem": {"expr": {"Literal": {"Value": "'EPSG:4326'"}}},
                }
            }
        ]
    }
    return value


write_json(
    REPORT / ".platform",
    {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": "AirportOpsPersonaReports", "description": "Seven-persona synthetic airport operations report"},
        "config": {"version": "2.0", "logicalId": "d761836d-b46e-43f4-b028-ef7590f5123e"},
    },
)
write_json(
    REPORT / "definition.pbir",
    {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json", "version": "4.0", "datasetReference": {"byPath": {"path": "../../semantic-model/AirportOpsSharedModel.SemanticModel"}}},
)
write_json(
    DEFINITION / "version.json",
    {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"},
)
write_json(
    DEFINITION / "report.json",
    {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/2.0.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.59", "type": "SharedResources"}},
        "resourcePackages": [{"name": "SharedResources", "type": "RegisteredResources", "items": [{"name": path.name, "path": "GeoJSON/" + path.name, "type": "ShapeMap"} for path in sorted((ROOT / "geospatial" / "azure-maps").glob("*.geojson"))]}],
        "annotations": [
            {"name": "AirportOpsDisclaimer", "value": DISCLAIMER},
            {"name": "AirportOpsSafetyBoundary", "value": ADVISORY_NOTICE},
            {"name": "AirportOpsDataAsOf", "value": "2026-01-31T23:59:00Z"},
        ],
    },
)
write_json(
    PAGES / "pages.json",
    {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json", "pageOrder": list(PAGE_NAMES.values()) + list(DETAIL_PAGE_NAMES.values()), "activePageName": PAGE_NAMES["Executive"]},
)

for order, (persona, (description, perspective)) in enumerate(PERSONAS.items()):
    page_name = PAGE_NAMES[persona]
    page_root = PAGES / page_name
    write_json(
        page_root / "page.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
            "name": page_name,
            "displayName": persona,
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
            "filterConfig": {"filters": []},
            "annotations": [
                {"name": "persona", "value": persona},
                {"name": "perspective", "value": perspective},
                {"name": "description", "value": description},
                {"name": "disclaimer", "value": DISCLAIMER},
                {"name": "safety", "value": ADVISORY_NOTICE},
                {"name": "dataAsOf", "value": "2026-01-31T23:59:00Z"},
            ],
        },
    )
    scorecard_values = (
        [column("gold_incident_customer_kpi", property_name) for property_name in ["customer_satisfaction", "synthetic_nps", "complaints_per_1000_responses", "recommendation_acceptance_pct"]]
        if persona == "CustomerExperience"
        else [column("gold_persona_scorecard", "primary_kpi_name"), column("gold_persona_scorecard", "primary_kpi_value"), column("gold_persona_scorecard", "secondary_kpi_name"), column("gold_persona_scorecard", "secondary_kpi_value"), column("gold_persona_scorecard", "scorecard_status")]
    )
    write_json(
        page_root / "visuals" / "PersonaScorecard" / "visual.json",
        visual(
            "PersonaScorecard",
            "tableEx",
            36,
            36,
            1208,
            190,
            {"Values": scorecard_values},
            persona + " scorecard - synthetic demonstration, advisory only",
        ),
    )

    if persona in {"Airport", "Operations"}:
        resource = "StaticResources/SharedResources/GeoJSON/terminals.geojson" if persona == "Airport" else "StaticResources/SharedResources/GeoJSON/zones.geojson"
        write_json(page_root / "visuals" / "AirportMap" / "visual.json", azure_map("AirportMap", persona + " Azure Maps spatial context", resource))
    else:
        bindings = {
            "Executive": ("gold_persona_scorecard", "Airports Requiring Attention"),
            "Regional": ("gold_persona_scorecard", "Airports Requiring Attention"),
            "Airline": ("gold_airline_route_performance", "On-Time Departure %"),
            "Maintenance": ("gold_asset_reliability", "Asset Availability %"),
            "Commercial": ("gold_retail_performance", "Synthetic Net Retail Revenue"),
            "Sustainability": ("gold_energy_efficiency", "Energy Benchmark Variance %"),
            "Compliance": ("gold_incident_details", "Incident Count"),
            "CustomerExperience": ("gold_incident_customer_kpi", "Recommendation Acceptance %"),
            "IT": ("gold_it_service_health", "Data Quality Pass %"),
        }
        entity, measure_name = bindings[persona]
        write_json(
            page_root / "visuals" / "PrimaryKpi" / "visual.json",
            visual("PrimaryKpi", "card", 36, 250, 420, 200, {"Values": [measure(entity, measure_name)]}, persona + " primary KPI"),
        )

for detail_order, (detail_key, (display_name, entity, property_names)) in enumerate(DETAIL_PAGES.items(), start=len(PERSONAS)):
    page_name = DETAIL_PAGE_NAMES[detail_key]
    page_root = PAGES / page_name
    write_json(
        page_root / "page.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
            "name": page_name,
            "displayName": display_name,
            "displayOption": "FitToPage",
            "height": 720,
            "width": 1280,
            "filterConfig": {"filters": []},
            "annotations": [
                {"name": "pagePurpose", "value": display_name},
                {"name": "disclaimer", "value": DISCLAIMER},
                {"name": "safety", "value": ADVISORY_NOTICE},
                {"name": "dataAsOf", "value": "2026-01-31T23:59:00Z"},
            ],
        },
    )
    has_secondary_visual = detail_key in {"PassengerFlow", "Baggage", "GatesAndStands", "RetailRevenue"}
    write_json(
        page_root / "visuals" / "DetailTable" / "visual.json",
        visual(
            "DetailTable", "tableEx", 36, 36, 1208, 190 if has_secondary_visual else 610,
            {"Values": [column(entity, property_name) for property_name in property_names]},
            display_name + " - synthetic demonstration, advisory only",
        ),
    )

    if detail_key in {"PassengerFlow", "Baggage"}:
        resource_name = "passenger_flows.geojson" if detail_key == "PassengerFlow" else "baggage_flows.geojson"
        write_json(
            page_root / "visuals" / "SpatialContext" / "visual.json",
            azure_map("SpatialContext", display_name + " illustrative spatial context", "StaticResources/SharedResources/GeoJSON/" + resource_name),
        )
    elif detail_key == "GatesAndStands":
        write_json(
            page_root / "visuals" / "RotationStatus" / "visual.json",
            visual("RotationStatus", "tableEx", 36, 250, 1208, 430,
                   {"Values": [column("gold_aircraft_rotation_kpi", property_name) for property_name in ["rotation_legs", "aircraft_instances", "avg_ground_interval_min", "overlap_count", "legs_per_aircraft"]]},
                   "Aircraft rotation status - synthetic demonstration"),
        )
    elif detail_key == "RetailRevenue":
        write_json(
            page_root / "visuals" / "InventoryStatus" / "visual.json",
            visual("InventoryStatus", "tableEx", 36, 250, 1208, 430,
                   {"Values": [column("gold_retail_inventory_kpi", property_name) for property_name in ["inventory_snapshots", "total_on_hand_units", "reorder_items", "reorder_rate_pct", "avg_on_hand_units"]]},
                   "Retail inventory status - synthetic demonstration"),
        )

if GEOJSON_TARGET.exists():
    for existing_resource in GEOJSON_TARGET.glob("*.geojson"):
        existing_resource.unlink()
GEOJSON_TARGET.mkdir(parents=True, exist_ok=True)
for source in sorted((ROOT / "geospatial" / "azure-maps").glob("*.geojson")):
    shutil.copyfile(source, GEOJSON_TARGET / source.name)

print(f"Generated PBIR report at {REPORT} with {len(PERSONAS)} persona pages and {len(DETAIL_PAGES)} detail pages")
