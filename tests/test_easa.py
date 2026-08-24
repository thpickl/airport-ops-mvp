from __future__ import annotations

import copy
import ast
import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from airport_ops.easa import calculate_automation_coverage, evaluate_release, validate_requirements_matrix  # noqa: E402


class EasaRequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = json.loads((ROOT / "config" / "easa_requirements_matrix.json").read_text(encoding="utf-8"))

    def test_unverified_inventory_is_valid_and_fail_closed(self) -> None:
        self.assertEqual(validate_requirements_matrix(self.matrix), ())
        result = calculate_automation_coverage(self.matrix)
        self.assertEqual(result.status, "BLOCKED_NO_APPROVED_INVENTORY")
        self.assertIsNone(result.coverage_percent)
        self.assertFalse(result.target_met)
        self.assertEqual(len(result.manual_submissions), 1)

    def test_coverage_uses_only_approved_annual_inventory(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        row = matrix["requirements"][0]
        row.update(
            {
                "requirement_id": "VERIFIED-001",
                "regulation": "Verified citation evidence://regulation/001",
                "submission": "Verified submission",
                "airport": "Verified airport scope",
                "authority": "Verified authority",
                "frequency": "Verified frequency",
                "annual_submission_count": 4,
                "source_fields": ["approved_source.field"],
                "validation_rules": [
                    {"rule_id": "VR-1", "rule_type": "RECONCILIATION", "definition": "Verified rule", "severity": "BLOCKING", "sql_expression": None},
                    {"rule_id": "VR-2", "rule_type": "COMPLETENESS", "definition": "Verified rule", "severity": "BLOCKING", "sql_expression": None},
                    {"rule_id": "VR-3", "rule_type": "VALIDITY", "definition": "Verified rule", "severity": "BLOCKING", "sql_expression": "source_record_id IS NOT NULL"},
                    {"rule_id": "VR-4", "rule_type": "DUPLICATE", "definition": "Verified rule", "severity": "BLOCKING", "sql_expression": None},
                    {"rule_id": "VR-5", "rule_type": "TIMELINESS", "definition": "Verified rule", "severity": "BLOCKING", "sql_expression": "source_event_at <= received_at_utc"},
                    {"rule_id": "VR-6", "rule_type": "CROSS_FIELD", "definition": "Verified rule", "severity": "BLOCKING", "sql_expression": "airport_id IS NOT NULL"}
                ],
                "output_format": "evidence://template/001",
                "automation_eligibility": "ELIGIBLE",
                "approval_status": "APPROVED",
                "inventory_approved": True,
                "manual_reason": "",
                "deadline": {"rule": "Verified rule", "timezone": "Europe/Paris", "calendar": "Verified calendar"},
                "compliance_owner_signoff": {"approved_by": "owner@example.invalid", "approved_at_utc": "2026-08-21T00:00:00Z", "evidence_reference": "evidence://signoff/001"},
            }
        )
        manual_row = copy.deepcopy(row)
        manual_row.update({"requirement_id": "VERIFIED-002", "annual_submission_count": 1, "automation_eligibility": "MANUAL", "manual_reason": "Authority template requires manual completion."})
        matrix["requirements"].append(manual_row)
        result = calculate_automation_coverage(matrix)
        self.assertEqual(result.coverage_percent, 80.0)
        self.assertTrue(result.target_met)
        self.assertEqual(result.status, "TARGET_MET")
        self.assertEqual(result.manual_submissions[0]["annual_submission_count"], 1)

    def test_approved_inventory_cannot_contain_todo(self) -> None:
        matrix = copy.deepcopy(self.matrix)
        row = matrix["requirements"][0]
        row.update(
            {
                "annual_submission_count": 1,
                "automation_eligibility": "ELIGIBLE",
                "approval_status": "APPROVED",
                "inventory_approved": True,
                "compliance_owner_signoff": {"approved_by": "owner@example.invalid", "approved_at_utc": "2026-08-21T00:00:00Z", "evidence_reference": "evidence://signoff/001"},
            }
        )
        self.assertIn("contains unresolved TODO", " ".join(validate_requirements_matrix(matrix)))

    def test_release_requires_quality_human_approval_and_authorized_interface(self) -> None:
        requirement = copy.deepcopy(self.matrix["requirements"][0])
        quality = {name: "FAIL" for name in ("reconciliation", "completeness", "validity", "duplicate", "timeliness", "cross_field")}
        quality.update({"quarantined_count": 2, "blocking_exception_count": 1})
        decision = evaluate_release(requirement, quality, {}, "TRANSMIT")
        self.assertFalse(decision.allowed)
        self.assertIn("HUMAN_APPROVAL_REQUIRED", decision.blockers)
        self.assertIn("OFFICIAL_INTERFACE_NOT_DOCUMENTED", decision.blockers)
        self.assertIn("TRANSMISSION_NOT_AUTHORIZED", decision.blockers)


class EasaArtifactTests(unittest.TestCase):
    def test_source_domains_and_environment_controls_fail_closed(self) -> None:
        sources = json.loads((ROOT / "config" / "easa_approved_sources.json").read_text(encoding="utf-8"))
        deployment = json.loads((ROOT / "config" / "easa_deployment.json").read_text(encoding="utf-8"))
        required_domains = {"operational", "safety", "flight", "passenger", "environmental", "incident"}
        self.assertLessEqual(required_domains, {source["domain"] for source in sources["sources"]})
        real_sources = [source for source in sources["sources"] if source["domain"] != "synthetic_test"]
        self.assertTrue(all(not source["approved"] and not source["ingestion_enabled"] for source in real_sources))
        for environment in deployment["environments"].values():
            self.assertFalse(environment["real_source_ingestion_enabled"])
            self.assertFalse(environment["scheduled_pipeline_enabled"])
            self.assertFalse(environment["event_pipeline_enabled"])
            self.assertFalse(environment["export_enabled"])
            self.assertFalse(environment["transmission_enabled"])

    def test_easa_notebooks_are_valid_and_have_release_boundaries(self) -> None:
        for name in ("17_EASA_Validate_Transform.ipynb", "18_EASA_Release_Gate.ipynb"):
            notebook = json.loads((ROOT / "notebooks" / name).read_text(encoding="utf-8"))
            ids = [cell["id"] for cell in notebook["cells"]]
            self.assertEqual(len(ids), len(set(ids)))
            for cell in notebook["cells"]:
                if cell["cell_type"] == "code":
                    ast.parse("".join(cell["source"]), filename=name)
        validation_text = (ROOT / "notebooks" / "17_EASA_Validate_Transform.ipynb").read_text(encoding="utf-8")
        release_text = (ROOT / "notebooks" / "18_EASA_Release_Gate.ipynb").read_text(encoding="utf-8")
        self.assertTrue(all(dimension in validation_text for dimension in ["RECONCILIATION", "COMPLETENESS", "VALIDITY", "DUPLICATE", "TIMELINESS", "CROSS_FIELD"]))
        self.assertIn("automatic_authority_call_performed", release_text)
        self.assertIn("HUMAN_APPROVAL_REQUIRED_FOR_EXACT_REPORT_VERSION", release_text)

    def test_data_factory_pipelines_are_deployable_but_disabled(self) -> None:
        for name in ("EASA_Scheduled_Ingestion.DataPipeline", "EASA_Event_Ingestion.DataPipeline"):
            definition = json.loads((ROOT / "data-factory" / name / "pipeline-content.json").read_text(encoding="utf-8"))
            self.assertEqual(definition["properties"]["activities"], [])
        bindings = json.loads((ROOT / "data-factory" / "pipeline-bindings.json").read_text(encoding="utf-8"))
        self.assertEqual(bindings["status"], "BLOCKED_PENDING_APPROVED_BINDINGS")
        self.assertTrue(all(not pipeline["binding_enabled"] for pipeline in bindings["pipelines"]))
        self.assertFalse(bindings["release_notebook"]["automatic_authority_call"])

    def test_warehouse_security_and_release_checks(self) -> None:
        schema = (ROOT / "warehouse" / "10_easa_schema.sql").read_text(encoding="utf-8")
        views = (ROOT / "warehouse" / "11_easa_views.sql").read_text(encoding="utf-8")
        security = (ROOT / "warehouse" / "12_easa_security.sql").read_text(encoding="utf-8")
        validation = (ROOT / "warehouse" / "13_easa_validation.sql").read_text(encoding="utf-8")
        self.assertGreaterEqual(views.upper().count("CREATE OR ALTER VIEW"), 14)
        self.assertIn("BLOCKED_NO_APPROVED_INVENTORY", views)
        self.assertIn("READY_FOR_EXPORT", views)
        self.assertIn("UNAUTHORIZED_ACTION", views)
        self.assertNotIn("GRANT DELETE", security.upper())
        self.assertNotIn("GRANT UPDATE", security.upper())
        self.assertNotIn("GRANT SELECT ON SCHEMA::EASA TO EASA_REPORT_READER", security.upper())
        self.assertIn("Deliberately no report-reader access to raw payload", security)
        self.assertTrue(all(table in schema for table in ["requirement_inventory", "source_registry", "quality_result", "quarantine_record", "approval_event", "export_event", "evidence_ledger", "principal_scope"]))
        self.assertIn("official_interface_reference IS NULL", validation)

    def test_semantic_model_contains_required_measures_and_dynamic_rls(self) -> None:
        model_root = ROOT / "semantic-model" / "EASARegulatoryModel.SemanticModel"
        tmdl = "\n".join(path.read_text(encoding="utf-8") for path in model_root.rglob("*.tmdl"))
        required_measures = [
            "Submission Count", "Ready for Export", "Awaiting Human Approval", "Overdue Submissions",
            "Due in 30 Days", "Release Blocker Count", "Data Quality Pass %", "Failed Quality Records",
            "Open Exceptions", "Blocking Exceptions", "Automation Coverage %", "Automation Target Met",
            "Manual Annual Submissions",
        ]
        self.assertTrue(all(f"measure '{name}'" in tmdl for name in required_measures))
        self.assertIn("USERPRINCIPALNAME()", tmdl)
        self.assertIn("easa_principal_scope[function_name]", tmdl)
        self.assertIn("${WAREHOUSE_SERVER}", tmdl)
        self.assertTrue((model_root / "definition.pbism").exists())

    def test_pbir_and_paginated_report_are_structurally_valid(self) -> None:
        report_root = ROOT / "reports" / "EASAComplianceReports.Report"
        pages = json.loads((report_root / "definition" / "pages" / "pages.json").read_text(encoding="utf-8"))
        self.assertEqual(len(pages["pageOrder"]), 4)
        drillthrough = json.loads((report_root / "definition" / "pages" / "ReportSectionEASAAirport" / "page.json").read_text(encoding="utf-8"))
        self.assertEqual(drillthrough["type"], "Drillthrough")
        self.assertEqual(drillthrough["pageBinding"]["parameters"][0]["fieldExpr"]["Column"]["Property"], "airport_id")
        visuals = [json.loads(path.read_text(encoding="utf-8")) for path in report_root.rglob("visual.json")]
        self.assertGreaterEqual(len(visuals), 18)
        self.assertTrue(all("altText" in json.dumps(visual) for visual in visuals))
        rdl_path = ROOT / "paginated-reports" / "EASASubmissionReview.PaginatedReport" / "EASASubmissionReview.rdl"
        ET.parse(rdl_path)
        rdl = rdl_path.read_text(encoding="utf-8")
        self.assertIn("AUTHORITY TEMPLATE UNVERIFIED", rdl)
        self.assertIn("No authority endpoint is called", rdl)

    def test_monitoring_destinations_require_owner_approval(self) -> None:
        monitoring = json.loads((ROOT / "config" / "easa_monitoring.json").read_text(encoding="utf-8"))
        self.assertEqual({rule["alert_type"] for rule in monitoring["alert_rules"]}, {"PIPELINE_FAILURE", "UNAPPROVED_SOURCE_ENABLED", "RELEASE_GATE_BLOCKED", "UNAUTHORIZED_ACTION"})
        self.assertTrue(all(not rule["enabled"] and rule["owner"].startswith("TODO") for rule in monitoring["alert_rules"]))


if __name__ == "__main__":
    unittest.main()