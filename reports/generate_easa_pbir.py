from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "reports" / "EASAComplianceReports.Report"
PAGE_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json"
VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.1.0/schema.json"


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def field(entity: str, property_name: str, *, measure: bool = False) -> dict[str, Any]:
    kind = "Measure" if measure else "Column"
    return {
        kind: {
            "Expression": {"SourceRef": {"Entity": entity}},
            "Property": property_name,
        }
    }


def projection(entity: str, property_name: str, *, measure: bool = False) -> dict[str, Any]:
    return {
        "field": field(entity, property_name, measure=measure),
        "queryRef": f"{entity}.{property_name}",
        "nativeQueryRef": property_name,
    }


def title_objects(title: str, alt_text: str) -> dict[str, Any]:
    return {
        "title": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": repr(title)}}},
                }
            }
        ],
        "general": [
            {
                "properties": {
                    "altText": {"expr": {"Literal": {"Value": repr(alt_text)}}}
                }
            }
        ],
    }


def card(name: str, title: str, entity: str, measure_name: str, x: int, y: int) -> dict[str, Any]:
    return {
        "$schema": VISUAL_SCHEMA,
        "name": name,
        "position": {"x": x, "y": y, "z": 0, "height": 130, "width": 270, "tabOrder": 0},
        "visual": {
            "visualType": "card",
            "query": {"queryState": {"Values": {"projections": [projection(entity, measure_name, measure=True)]}}},
            "visualContainerObjects": title_objects(title, title),
        },
        "filterConfig": {"filters": []},
    }


def table(name: str, title: str, fields: list[tuple[str, str]], x: int, y: int, width: int, height: int) -> dict[str, Any]:
    return {
        "$schema": VISUAL_SCHEMA,
        "name": name,
        "position": {"x": x, "y": y, "z": 0, "height": height, "width": width, "tabOrder": 0},
        "visual": {
            "visualType": "tableEx",
            "query": {"queryState": {"Values": {"projections": [projection(entity, column) for entity, column in fields]}}},
            "visualContainerObjects": title_objects(title, title),
        },
        "filterConfig": {"filters": []},
    }


def page(name: str, display_name: str, description: str, *, drillthrough: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "$schema": PAGE_SCHEMA,
        "name": name,
        "displayName": display_name,
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "filterConfig": {"filters": []},
        "annotations": [
            {"name": "owner", "value": "Regulatory Compliance"},
            {"name": "description", "value": description},
            {"name": "releaseBoundary", "value": "Human approval is required before export; no authority submission is performed."},
        ],
    }
    if drillthrough:
        result.update(
            {
                "type": "Drillthrough",
                "visibility": "HiddenInViewMode",
                "pageBinding": {
                    "name": "EASAAirportDrillthrough",
                    "type": "Drillthrough",
                    "referenceScope": "Default",
                    "acceptsFilterContext": "Default",
                    "parameters": [
                        {
                            "name": "AirportId",
                            "fieldExpr": field("easa_submission_status", "airport_id"),
                        }
                    ],
                },
            }
        )
    return result


def build() -> None:
    if TARGET.exists():
        try:
            shutil.rmtree(TARGET)
        except PermissionError:
            pass

    write_json(
        TARGET / ".platform",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {
                "type": "Report",
                "displayName": "EASAComplianceReports",
                "description": "Human-approved regulatory preparation, status, quality, and exception reporting.",
            },
            "config": {"version": "2.0", "logicalId": "ef1e507f-72a5-4450-8f0f-91d93dd21e9c"},
        },
    )
    write_json(
        TARGET / "definition.pbir",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": "../../semantic-model/EASARegulatoryModel.SemanticModel"}},
        },
    )
    write_json(
        TARGET / "definition" / "report.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/2.0.0/schema.json",
            "themeCollection": {
                "baseTheme": {
                    "name": "CY24SU10",
                    "reportVersionAtImport": "5.59",
                    "type": "SharedResources",
                }
            },
            "annotations": [
                {"name": "EASAGovernanceBoundary", "value": "Only approved inventory contributes to automation coverage."},
                {"name": "EASAReleaseBoundary", "value": "No export without exact-version human approval; no automatic authority submission."},
            ],
        },
    )
    write_json(
        TARGET / "definition" / "version.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
            "version": "2.0.0",
        },
    )

    pages = {
        "ReportSectionEASAExecutive": (
            page("ReportSectionEASAExecutive", "Executive Compliance", "Group compliance posture and approved-inventory automation coverage."),
            [
                card("AutomationCoverage", "Automation coverage", "easa_automation_coverage", "Automation Coverage %", 30, 30),
                card("SubmissionCount", "Submission inventory", "easa_submission_status", "Submission Count", 320, 30),
                card("Overdue", "Overdue submissions", "easa_submission_status", "Overdue Submissions", 610, 30),
                card("ReleaseReady", "Ready for export", "easa_submission_status", "Ready for Export", 900, 30),
                table("ManualInventory", "Manual and unapproved annual inventory", [
                    ("easa_manual_inventory", "submission_name"),
                    ("easa_manual_inventory", "authority_name"),
                    ("easa_manual_inventory", "airport_scope"),
                    ("easa_manual_inventory", "annual_submission_count"),
                    ("easa_manual_inventory", "approval_status"),
                    ("easa_manual_inventory", "manual_reason"),
                ], 30, 190, 1170, 480),
            ],
        ),
        "ReportSectionEASACalendar": (
            page("ReportSectionEASACalendar", "Submission Calendar and Status", "Due dates, approval state, and release blockers."),
            [
                card("DueSoon", "Due in 30 days", "easa_submission_status", "Due in 30 Days", 30, 30),
                card("AwaitingApproval", "Awaiting human approval", "easa_submission_status", "Awaiting Human Approval", 320, 30),
                card("Blockers", "Release blockers", "easa_submission_status", "Release Blocker Count", 610, 30),
                table("Calendar", "Submission calendar", [
                    ("easa_submission_status", "airport_id"),
                    ("easa_submission_status", "submission_name"),
                    ("easa_submission_status", "authority_name"),
                    ("easa_submission_status", "due_at_utc"),
                    ("easa_submission_status", "days_until_due"),
                    ("easa_submission_status", "submission_status"),
                    ("easa_submission_status", "approval_status"),
                    ("easa_submission_status", "release_status"),
                ], 30, 190, 1170, 480),
            ],
        ),
        "ReportSectionEASAQuality": (
            page("ReportSectionEASAQuality", "Data Quality and Exceptions", "Six-dimensional quality results and blocking exceptions."),
            [
                card("QualityPass", "Data quality pass", "easa_data_quality", "Data Quality Pass %", 30, 30),
                card("FailedRecords", "Failed quality records", "easa_data_quality", "Failed Quality Records", 320, 30),
                card("OpenExceptions", "Open exceptions", "easa_exceptions", "Open Exceptions", 610, 30),
                card("BlockingExceptions", "Blocking exceptions", "easa_exceptions", "Blocking Exceptions", 900, 30),
                table("QualityDetail", "Quality rule results", [
                    ("easa_data_quality", "airport_id"),
                    ("easa_data_quality", "quality_dimension"),
                    ("easa_data_quality", "rule_id"),
                    ("easa_data_quality", "severity"),
                    ("easa_data_quality", "result_status"),
                    ("easa_data_quality", "failed_record_count"),
                    ("easa_data_quality", "evaluated_at_utc"),
                ], 30, 190, 730, 480),
                table("ExceptionDetail", "Open exceptions", [
                    ("easa_exceptions", "airport_id"),
                    ("easa_exceptions", "exception_type"),
                    ("easa_exceptions", "severity"),
                    ("easa_exceptions", "exception_status"),
                    ("easa_exceptions", "exception_detail"),
                ], 780, 190, 420, 480),
            ],
        ),
        "ReportSectionEASAAirport": (
            page("ReportSectionEASAAirport", "Airport Submission Detail", "Airport-level drill-through for submissions, quality, and exceptions.", drillthrough=True),
            [
                table("AirportSubmission", "Airport submissions", [
                    ("easa_submission_status", "airport_id"),
                    ("easa_submission_status", "submission_name"),
                    ("easa_submission_status", "reporting_period_start"),
                    ("easa_submission_status", "reporting_period_end"),
                    ("easa_submission_status", "due_at_utc"),
                    ("easa_submission_status", "approval_status"),
                    ("easa_submission_status", "release_status"),
                ], 30, 30, 1170, 300),
                table("AirportQuality", "Airport quality detail", [
                    ("easa_data_quality", "quality_dimension"),
                    ("easa_data_quality", "rule_id"),
                    ("easa_data_quality", "result_status"),
                    ("easa_data_quality", "failed_record_count"),
                ], 30, 360, 570, 310),
                table("AirportExceptions", "Airport exceptions", [
                    ("easa_exceptions", "exception_type"),
                    ("easa_exceptions", "severity"),
                    ("easa_exceptions", "exception_status"),
                    ("easa_exceptions", "exception_detail"),
                ], 630, 360, 570, 310),
            ],
        ),
    }

    page_order = list(pages)
    write_json(
        TARGET / "definition" / "pages" / "pages.json",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
            "pageOrder": page_order,
            "activePageName": page_order[0],
        },
    )
    for page_name, (page_definition, visuals) in pages.items():
        page_root = TARGET / "definition" / "pages" / page_name
        write_json(page_root / "page.json", page_definition)
        for visual in visuals:
            write_json(page_root / "visuals" / visual["name"] / "visual.json", visual)


if __name__ == "__main__":
    build()
    print(f"Generated {TARGET}")