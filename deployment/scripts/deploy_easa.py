"""Deploy the fail-closed EASA regulatory reporting control plane to Fabric.

The driver deploys content only. It never mutates workspace infrastructure,
enables a source, schedules a pipeline, exports a report, or calls an authority.
Authentication and target identifiers are obtained at runtime.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
FABRIC_API = "https://api.fabric.microsoft.com/v1"
ONELAKE_DFS = "https://onelake.dfs.fabric.microsoft.com"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
EASA_SQL = (
    "warehouse/10_easa_schema.sql",
    "warehouse/11_easa_views.sql",
    "warehouse/12_easa_security.sql",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def az_token(resource: str) -> str:
    az_executable = shutil.which("az.cmd") or shutil.which("az")
    if not az_executable:
        raise RuntimeError("Azure CLI executable was not found")
    completed = subprocess.run(
        [az_executable, "account", "get-access-token", "--resource", resource, "--query", "accessToken", "--output", "tsv"],
        check=True,
        capture_output=True,
        text=True,
    )
    token = completed.stdout.strip()
    if not token:
        raise RuntimeError(f"Azure CLI returned no token for {resource}")
    return token


class RestClient:
    def __init__(self, token: str, timeout_seconds: int = 120) -> None:
        self.token = token
        self.timeout_seconds = timeout_seconds

    def request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any] | bytes | None = None,
        accepted: Iterable[int] = (200, 201, 202),
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], Any]:
        accepted_status = set(accepted)
        request_headers = {"Authorization": f"Bearer {self.token}"}
        request_headers.update(headers or {})
        data: bytes | None
        if isinstance(payload, dict):
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        else:
            data = payload
        last_error = ""
        for attempt in range(6):
            request = urllib.request.Request(url, data=data, method=method, headers=request_headers)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body_bytes = response.read()
                    response_headers = {key.lower(): value for key, value in response.headers.items()}
                    body = json.loads(body_bytes) if body_bytes else {}
                    if response.status not in accepted_status:
                        raise RuntimeError(f"Unexpected HTTP {response.status}")
                    if response.status == 202 and response_headers.get("location"):
                        return self.poll(response_headers["location"])
                    return response.status, response_headers, body
            except urllib.error.HTTPError as exc:
                last_error = exc.read().decode("utf-8", errors="replace")[:4000]
                if exc.code not in RETRYABLE_STATUS or attempt == 5:
                    raise RuntimeError(f"HTTP {exc.code} {url}: {last_error}") from exc
                time.sleep(min(2**attempt, 30))
            except urllib.error.URLError as exc:
                last_error = str(exc.reason)
                if attempt == 5:
                    raise RuntimeError(f"Request failed for {url}: {last_error}") from exc
                time.sleep(min(2**attempt, 30))
        raise RuntimeError(last_error or f"Request failed for {url}")

    def poll(self, operation_url: str) -> tuple[int, dict[str, str], Any]:
        started = time.monotonic()
        while time.monotonic() - started < 1800:
            request = urllib.request.Request(operation_url, method="GET", headers={"Authorization": f"Bearer {self.token}"})
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body_bytes = response.read()
                body = json.loads(body_bytes) if body_bytes else {}
                headers = {key.lower(): value for key, value in response.headers.items()}
                status = str(body.get("status", "")).lower()
                if status in {"succeeded", "completed"}:
                    return response.status, headers, body
                if status in {"failed", "cancelled", "deduped"}:
                    raise RuntimeError(f"Fabric operation ended with {status}: {json.dumps(body)[:4000]}")
                time.sleep(min(int(headers.get("retry-after", "5")), 30))
        raise TimeoutError(f"Fabric operation timed out: {operation_url}")


class FabricDeployer:
    def __init__(self, workspace_id: str, environment_name: str) -> None:
        self.workspace_id = workspace_id
        self.environment_name = environment_name
        self.client = RestClient(az_token("https://api.fabric.microsoft.com"))
        self.storage_client = RestClient(az_token("https://storage.azure.com/"))
        self.results: list[dict[str, Any]] = []
        self.run_id = "EASA-DEPLOY-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def record(self, name: str, item_type: str, status: str, detail: str, item_id: str = "") -> None:
        entry = {
            "deployment_run_id": self.run_id,
            "environment": self.environment_name,
            "artifact_name": name,
            "artifact_type": item_type,
            "status": status,
            "detail": detail[:4000],
            "item_id": item_id,
            "observed_at_utc": utc_now(),
        }
        self.results.append(entry)
        print(f"{status:36} {item_type:18} {name}: {detail}")

    def list_items(self, item_type: str | None = None) -> list[dict[str, Any]]:
        query = "?" + urllib.parse.urlencode({"type": item_type}) if item_type else ""
        _, _, body = self.client.request("GET", f"{FABRIC_API}/workspaces/{self.workspace_id}/items{query}", accepted=(200,))
        return body.get("value", [])

    def find_item(self, display_name: str, item_type: str) -> dict[str, Any] | None:
        matches = [
            item for item in self.list_items(item_type)
            if item.get("displayName") == display_name and item.get("type") == item_type
        ]
        if len(matches) > 1:
            raise RuntimeError(f"Multiple {item_type} items named {display_name}")
        return matches[0] if matches else None

    @staticmethod
    def definition_parts(
        root: Path,
        replacements: dict[str, str] | None = None,
        include_platform: bool = False,
    ) -> list[dict[str, str]]:
        replacements = replacements or {}
        parts: list[dict[str, str]] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix == ".py" or (path.name == ".platform" and not include_platform):
                continue
            data = path.read_bytes()
            if path.suffix.lower() in {".json", ".tmdl", ".pbir", ".rdl", ".md", ".yaml", ".sql"} or path.name == ".platform":
                text = data.decode("utf-8")
                for token, value in replacements.items():
                    text = text.replace(token, value)
                if "${WAREHOUSE_" in text or "${FABRIC_WORKSPACE_NAME}" in text or "${EASA_SEMANTIC_MODEL_NAME}" in text:
                    raise ValueError(f"Unresolved runtime placeholder in {path}")
                data = text.encode("utf-8")
            parts.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "payload": base64.b64encode(data).decode("ascii"),
                    "payloadType": "InlineBase64",
                }
            )
        if not parts:
            raise ValueError(f"No definition parts under {root}")
        return parts

    def deploy_generic_definition(
        self,
        display_name: str,
        item_type: str,
        parts: list[dict[str, str]],
        description: str,
    ) -> dict[str, Any]:
        item = self.find_item(display_name, item_type)
        if item:
            self.client.request(
                "POST",
                f"{FABRIC_API}/workspaces/{self.workspace_id}/items/{item['id']}/updateDefinition",
                {"definition": {"parts": parts}},
            )
            self.record(display_name, item_type, "DEPLOYED", "Definition updated and long-running operation completed", item["id"])
            return item
        self.client.request(
            "POST",
            f"{FABRIC_API}/workspaces/{self.workspace_id}/items",
            {"displayName": display_name, "type": item_type, "description": description, "definition": {"parts": parts}},
        )
        item = self.find_item(display_name, item_type)
        if not item:
            raise RuntimeError(f"Created {item_type} could not be retrieved: {display_name}")
        self.record(display_name, item_type, "DEPLOYED", "Item created with definition", item["id"])
        return item

    def deploy_specialized_definition(
        self,
        display_name: str,
        item_type: str,
        collection: str,
        parts: list[dict[str, str]],
        description: str,
        definition_format: str | None = None,
    ) -> dict[str, Any]:
        for part in parts:
            if item_type == "PaginatedReport" and part["path"].lower().endswith(".rdl"):
                part["path"] = display_name + ".rdl"
            if part["path"] == ".platform":
                platform = json.loads(base64.b64decode(part["payload"]).decode("utf-8"))
                platform.setdefault("metadata", {})["displayName"] = display_name
                part["payload"] = base64.b64encode(json.dumps(platform, separators=(",", ":")).encode("utf-8")).decode("ascii")
        item = self.find_item(display_name, item_type)
        if not item:
            create_payload: dict[str, Any] = {"displayName": display_name, "description": description}
            if definition_format:
                create_payload["definition"] = {"format": definition_format, "parts": parts}
            self.client.request(
                "POST",
                f"{FABRIC_API}/workspaces/{self.workspace_id}/{collection}",
                create_payload,
            )
            item = self.find_item(display_name, item_type)
        if not item:
            raise RuntimeError(f"Created {item_type} could not be retrieved: {display_name}")
        definition: dict[str, Any] = {"parts": parts}
        if definition_format:
            definition["format"] = definition_format
        if not definition_format or self.find_item(display_name, item_type):
            self.client.request(
                "POST",
                f"{FABRIC_API}/workspaces/{self.workspace_id}/{collection}/{item['id']}/updateDefinition",
                {"definition": definition},
            )
        self.record(display_name, item_type, "DEPLOYED", "Governed shell created or updated; execution remains disabled", item["id"])
        return item

    def deploy_notebook(self, path: Path, lakehouse: dict[str, Any]) -> dict[str, Any]:
        notebook = read_json(path)
        notebook.setdefault("metadata", {}).setdefault("dependencies", {})["lakehouse"] = {
            "default_lakehouse": lakehouse["id"],
            "default_lakehouse_name": lakehouse["displayName"],
            "default_lakehouse_workspace_id": self.workspace_id,
            "known_lakehouses": [
                {"id": lakehouse["id"], "name": lakehouse["displayName"], "workspace_id": self.workspace_id}
            ],
        }
        data = json.dumps(notebook, separators=(",", ":")).encode("utf-8")
        platform = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
            "metadata": {"type": "Notebook", "displayName": path.stem, "description": "Governed EASA regulatory processing"},
            "config": {"version": "2.0", "logicalId": str(uuid.uuid5(uuid.NAMESPACE_URL, "repo://notebooks/" + path.stem))},
        }
        parts = [
            {"path": "artifact.content.ipynb", "payload": base64.b64encode(data).decode("ascii"), "payloadType": "InlineBase64"},
            {"path": ".platform", "payload": base64.b64encode(json.dumps(platform, separators=(",", ":")).encode("utf-8")).decode("ascii"), "payloadType": "InlineBase64"},
        ]
        return self.deploy_specialized_definition(
            path.stem,
            "Notebook",
            "notebooks",
            parts,
            "Governed EASA regulatory processing; human approval and fail-closed release controls",
            definition_format="ipynb",
        )

    def onelake_url(self, lakehouse_id: str, path: str, query: dict[str, str]) -> str:
        encoded_path = "/".join(urllib.parse.quote(part, safe="") for part in path.strip("/").split("/"))
        return f"{ONELAKE_DFS}/{self.workspace_id}/{lakehouse_id}/{encoded_path}?{urllib.parse.urlencode(query)}"

    def ensure_onelake_directory(self, lakehouse_id: str, path: str) -> None:
        url = self.onelake_url(lakehouse_id, path, {"resource": "directory"})
        try:
            self.storage_client.request("PUT", url, b"", accepted=(201,), headers={"Content-Length": "0", "x-ms-version": "2023-11-03"})
        except RuntimeError as exc:
            if "HTTP 409" not in str(exc):
                raise

    def upload_onelake_file(self, lakehouse_id: str, relative_path: str, data: bytes) -> None:
        parts = relative_path.strip("/").split("/")
        for index in range(1, len(parts)):
            self.ensure_onelake_directory(lakehouse_id, "/".join(parts[:index]))
        create_url = self.onelake_url(lakehouse_id, relative_path, {"resource": "file"})
        self.storage_client.request("PUT", create_url, b"", accepted=(201,), headers={"Content-Length": "0", "x-ms-version": "2023-11-03"})
        if data:
            append_url = self.onelake_url(lakehouse_id, relative_path, {"action": "append", "position": "0"})
            self.storage_client.request(
                "PATCH", append_url, data, accepted=(202,),
                headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(data)), "x-ms-version": "2023-11-03"},
            )
        flush_url = self.onelake_url(lakehouse_id, relative_path, {"action": "flush", "position": str(len(data))})
        self.storage_client.request("PATCH", flush_url, b"", accepted=(200,), headers={"Content-Length": "0", "x-ms-version": "2023-11-03"})

    def upload_governance_bundle(self, lakehouse: dict[str, Any]) -> None:
        files = {
            "Files/easa/config/easa_requirements_matrix.json": ROOT / "config/easa_requirements_matrix.json",
            "Files/easa/config/easa_approved_sources.json": ROOT / "config/easa_approved_sources.json",
            "Files/easa/config/easa_deployment.json": ROOT / "config/easa_deployment.json",
            "Files/easa/config/easa_monitoring.json": ROOT / "config/easa_monitoring.json",
            "Files/easa/sql/easa_medallion.sql": ROOT / "lakehouse/schemas/easa_medallion.sql",
        }
        for target, source in files.items():
            self.upload_onelake_file(lakehouse["id"], target, source.read_bytes())
            self.record(target, "OneLakeFile", "DEPLOYED", f"Uploaded sha256={sha256_bytes(source.read_bytes())}")

    @staticmethod
    def split_sql_batches(text: str) -> list[str]:
        return [batch.strip() for batch in re.split(r"^\s*GO\s*$", text, flags=re.MULTILINE | re.IGNORECASE) if batch.strip()]

    def deploy_warehouse(self, server: str, database: str) -> None:
        try:
            import pyodbc
        except ImportError as exc:
            raise RuntimeError("pyodbc is required; install requirements.txt") from exc
        drivers = set(pyodbc.drivers())
        driver = "ODBC Driver 18 for SQL Server" if "ODBC Driver 18 for SQL Server" in drivers else "ODBC Driver 17 for SQL Server"
        if driver not in drivers:
            raise RuntimeError("Microsoft ODBC Driver 17 or 18 for SQL Server is required")
        token = az_token("https://database.windows.net/").encode("utf-16-le")
        token_struct = struct.pack("<I", len(token)) + token
        connection = pyodbc.connect(
            f"Driver={{{driver}}};Server={server};Database={database};Encrypt=yes;TrustServerCertificate=no;",
            attrs_before={1256: token_struct},
            autocommit=False,
            timeout=60,
        )
        try:
            for relative_path in EASA_SQL:
                path = ROOT / relative_path
                cursor = connection.cursor()
                try:
                    for batch in self.split_sql_batches(path.read_text(encoding="utf-8")):
                        cursor.execute(batch)
                        while cursor.nextset():
                            pass
                    connection.commit()
                    self.record(relative_path, "WarehouseSQL", "DEPLOYED", "All idempotent SQL batches committed")
                except Exception:
                    connection.rollback()
                    raise
            self.seed_governance(connection)
        finally:
            connection.close()

    def seed_governance(self, connection: Any) -> None:
        matrix = read_json(ROOT / "config/easa_requirements_matrix.json")
        cursor = connection.cursor()
        for requirement in matrix["requirements"]:
            version_hash = sha256_bytes(json.dumps(requirement, sort_keys=True).encode("utf-8"))
            cursor.execute(
                """
                IF NOT EXISTS (SELECT 1 FROM easa.requirement_inventory WHERE requirement_id = ? AND requirement_version_hash = ?)
                INSERT INTO easa.requirement_inventory (
                    requirement_id, regulation, submission_name, airport_scope, authority_name,
                    frequency_rule, annual_submission_count, deadline_rule, deadline_timezone,
                    source_fields_json, validation_rules_json, output_format_reference,
                    automation_eligibility, approval_status, inventory_approved, manual_reason,
                    effective_from, effective_to, signoff_evidence_reference,
                    requirement_version_hash, recorded_at_utc, is_placeholder
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), ?)
                """,
                requirement["requirement_id"], version_hash,
                requirement["requirement_id"], requirement["regulation"], requirement["submission"], requirement["airport"], requirement["authority"],
                requirement["frequency"], requirement["annual_submission_count"], requirement["deadline"]["rule"], requirement["deadline"]["timezone"],
                json.dumps(requirement["source_fields"]), json.dumps(requirement["validation_rules"]), requirement["output_format"],
                requirement["automation_eligibility"], requirement["approval_status"], int(requirement["inventory_approved"]), requirement["manual_reason"],
                requirement.get("effective_from"), requirement.get("effective_to"), requirement["compliance_owner_signoff"].get("evidence_reference"),
                version_hash, int("TODO" in json.dumps(requirement).upper()),
            )
        source_policy = read_json(ROOT / "config/easa_approved_sources.json")
        for source in source_policy["sources"]:
            version_hash = sha256_bytes(json.dumps(source, sort_keys=True).encode("utf-8"))
            cursor.execute(
                """
                IF NOT EXISTS (SELECT 1 FROM easa.source_registry WHERE source_id = ? AND source_version_hash = ?)
                INSERT INTO easa.source_registry (
                    source_id, source_domain, source_system, connector_type, connection_reference,
                    data_contract_reference, data_classification, approved, ingestion_enabled,
                    approved_by_object_id, approved_at_utc, source_version_hash, recorded_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
                """,
                source["source_id"], version_hash,
                source["source_id"], source["domain"], source["source_system"], source["connector_type"], source["connection_reference"],
                source["data_contract_reference"], source["data_classification"], int(source["approved"]), int(source["ingestion_enabled"]),
                source.get("approved_by"), source.get("approved_at_utc"), version_hash,
            )
        connection.commit()
        self.record("EASA governance configuration", "WarehouseSeed", "DEPLOYED", "Versioned requirement and source rows appended idempotently")

    def report_parts(self, root: Path, workspace_name: str, semantic_model_name: str, semantic_model_id: str) -> list[dict[str, str]]:
        parts = self.definition_parts(root)
        connection_string = (
            f"Data Source=powerbi://api.powerbi.com/v1.0/myorg/{workspace_name};"
            f"Initial Catalog={semantic_model_name};semanticModelId={semantic_model_id};Integrated Security=ClaimsToken"
        )
        for part in parts:
            if part["path"] == "definition.pbir":
                definition = json.loads(base64.b64decode(part["payload"]).decode("utf-8"))
                definition["datasetReference"] = {"byConnection": {"connectionString": connection_string}}
                part["payload"] = base64.b64encode(json.dumps(definition, separators=(",", ":")).encode("utf-8")).decode("ascii")
                return parts
        raise RuntimeError("PBIR definition.pbir was not found")

    def validate_warehouse(self, server: str, database: str) -> dict[str, Any]:
        import pyodbc
        drivers = set(pyodbc.drivers())
        driver = "ODBC Driver 18 for SQL Server" if "ODBC Driver 18 for SQL Server" in drivers else "ODBC Driver 17 for SQL Server"
        token = az_token("https://database.windows.net/").encode("utf-16-le")
        token_struct = struct.pack("<I", len(token)) + token
        connection = pyodbc.connect(
            f"Driver={{{driver}}};Server={server};Database={database};Encrypt=yes;TrustServerCertificate=no;",
            attrs_before={1256: token_struct}, autocommit=True, timeout=60,
        )
        try:
            cursor = connection.cursor()
            checks = {
                "serving_view_count": "SELECT COUNT(*) FROM sys.views WHERE schema_id = SCHEMA_ID('ops') AND name LIKE 'vw_easa_%'",
                "approved_todo_count": "SELECT COUNT(*) FROM ops.vw_easa_requirement_inventory WHERE inventory_approved = 1 AND (regulation LIKE '%TODO%' OR authority_name LIKE '%TODO%' OR output_format_reference LIKE '%TODO%')",
                "eligible_unapproved_count": "SELECT COUNT(*) FROM ops.vw_easa_requirement_inventory WHERE automation_eligibility = 'ELIGIBLE' AND inventory_approved = 0",
                "enabled_unapproved_source_count": "SELECT COUNT(*) FROM easa.source_registry WHERE ingestion_enabled = 1 AND approved = 0",
            }
            result = {name: int(cursor.execute(sql).fetchone()[0]) for name, sql in checks.items()}
            coverage = cursor.execute("SELECT approved_annual_submission_count, eligible_annual_submission_count, automation_coverage_percent, coverage_status FROM ops.vw_easa_automation_coverage").fetchone()
            result["coverage"] = {
                "approved_annual_submission_count": coverage[0],
                "eligible_annual_submission_count": coverage[1],
                "automation_coverage_percent": float(coverage[2]) if coverage[2] is not None else None,
                "coverage_status": coverage[3],
            }
            if result["serving_view_count"] < 12 or result["approved_todo_count"] or result["eligible_unapproved_count"] or result["enabled_unapproved_source_count"]:
                raise RuntimeError(f"Warehouse validation failed: {json.dumps(result)}")
            return result
        finally:
            connection.close()

    def write_evidence(self, lakehouse: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
        evidence = {
            "deployment_run_id": self.run_id,
            "workspace_id": self.workspace_id,
            "environment": self.environment_name,
            "observed_at_utc": utc_now(),
            "artifacts": self.results,
            "validation": validation,
            "automatic_authority_call_performed": False,
        }
        canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
        evidence["evidence_sha256"] = sha256_bytes(canonical)
        data = json.dumps(evidence, indent=2).encode("utf-8")
        self.upload_onelake_file(lakehouse["id"], f"Files/easa/evidence/deployments/{self.run_id}.json", data)
        state_path = Path(os.environ.get("EASA_DEPLOYMENT_STATE_PATH", Path(tempfile.gettempdir()) / "easa-deployment-state.json"))
        state_path.write_bytes(data + b"\n")
        return evidence

    def apply(self) -> dict[str, Any]:
        config = read_json(ROOT / "config/easa_deployment.json")
        environment = config["environments"][self.environment_name]
        matrix = read_json(ROOT / "config/easa_requirements_matrix.json")
        if environment["transmission_enabled"]:
            raise RuntimeError("This driver refuses environments with transmission enabled")

        _, _, workspace = self.client.request("GET", f"{FABRIC_API}/workspaces/{self.workspace_id}", accepted=(200,))
        lakehouse = self.find_item(environment["lakehouse_name"], "Lakehouse")
        warehouse = self.find_item(environment["warehouse_name"], "Warehouse")
        if not lakehouse or not warehouse:
            raise RuntimeError("Configured Lakehouse and Warehouse must already exist")
        _, _, warehouse_detail = self.client.request(
            "GET", f"{FABRIC_API}/workspaces/{self.workspace_id}/warehouses/{warehouse['id']}", accepted=(200,)
        )
        warehouse_server = warehouse_detail["properties"]["connectionString"]

        self.upload_governance_bundle(lakehouse)
        self.deploy_warehouse(warehouse_server, warehouse["displayName"])
        for notebook_name in ("17_EASA_Validate_Transform.ipynb", "18_EASA_Release_Gate.ipynb"):
            self.deploy_notebook(ROOT / "notebooks" / notebook_name, lakehouse)

        suffix = "-" + self.environment_name.capitalize()
        pipeline_specs = (
            ("EASA Scheduled Ingestion" + suffix, ROOT / "data-factory/EASA_Scheduled_Ingestion.DataPipeline"),
            ("EASA Event Ingestion" + suffix, ROOT / "data-factory/EASA_Event_Ingestion.DataPipeline"),
        )
        for name, root in pipeline_specs:
            self.deploy_specialized_definition(
                name, "DataPipeline", "dataPipelines", self.definition_parts(root, include_platform=True),
                "Governed disabled shell; binding requires approved source and compliance-owner sign-off",
            )

        replacements = {"${WAREHOUSE_SERVER}": warehouse_server, "${WAREHOUSE_DATABASE}": warehouse["displayName"]}
        semantic_model = self.deploy_generic_definition(
            environment["semantic_model_name"], "SemanticModel",
            self.definition_parts(ROOT / "semantic-model/EASARegulatoryModel.SemanticModel", replacements),
            "Certified EASA regulatory reporting model; fail-closed inventory and release status",
        )
        report = self.deploy_generic_definition(
            environment["interactive_report_name"], "Report",
            self.report_parts(
                ROOT / "reports/EASAComplianceReports.Report", workspace["displayName"],
                environment["semantic_model_name"], semantic_model["id"],
            ),
            "Executive, calendar, quality, exception, and airport drill-through regulatory reporting",
        )
        paginated_replacements = {
            "${FABRIC_WORKSPACE_NAME}": workspace["displayName"],
            "${EASA_SEMANTIC_MODEL_NAME}": environment["semantic_model_name"],
        }
        paginated = None
        try:
            paginated = self.deploy_specialized_definition(
                environment["paginated_report_name"], "PaginatedReport", "paginatedReports",
                self.definition_parts(ROOT / "paginated-reports/EASASubmissionReview.PaginatedReport", paginated_replacements, include_platform=True),
                "Human review shell; not an authority template and blocked from release",
                definition_format="PaginatedReportDefinition",
            )
        except RuntimeError as exc:
            if "InvalidDefinitionFormat" not in str(exc):
                raise
            self.record(
                environment["paginated_report_name"], "PaginatedReport", "BLOCKED_TENANT_CAPABILITY",
                "Tenant rejected the documented PaginatedReportDefinition format; validated RDL source remains blocked and undeployed",
            )

        warehouse_validation = self.validate_warehouse(warehouse_server, warehouse["displayName"])
        expected = {
            environment["semantic_model_name"]: "SemanticModel",
            environment["interactive_report_name"]: "Report",
            "17_EASA_Validate_Transform": "Notebook",
            "18_EASA_Release_Gate": "Notebook",
            pipeline_specs[0][0]: "DataPipeline",
            pipeline_specs[1][0]: "DataPipeline",
        }
        if paginated:
            expected[environment["paginated_report_name"]] = "PaginatedReport"
        live_items = self.list_items()
        missing = [name for name, item_type in expected.items() if not any(item.get("displayName") == name and item.get("type") == item_type for item in live_items)]
        if missing:
            raise RuntimeError(f"Post-deployment retrieval failed: {missing}")
        coverage_status = warehouse_validation["coverage"]["coverage_status"]
        overall_status = "DEPLOYED" if coverage_status == "TARGET_MET" else "DEPLOYED_BLOCKED_PENDING_SIGNOFF"
        validation = {
            "status": overall_status,
            "workspace_retrieved": True,
            "items_retrieved": sorted(expected),
            "warehouse": warehouse_validation,
            "pipelines_scheduled": False,
            "real_source_ingestion_enabled": False,
            "export_enabled": False,
            "transmission_enabled": False,
            "paginated_authority_template_verified": not any("TODO" in item["output_format"].upper() for item in matrix["requirements"]),
            "paginated_deployment_status": "DEPLOYED" if paginated else "BLOCKED_TENANT_CAPABILITY",
            "semantic_model_certification_status": "PENDING_TENANT_ENDORSEMENT",
            "report_item_id": report["id"],
            "paginated_report_item_id": paginated["id"] if paginated else "",
        }
        evidence = self.write_evidence(lakehouse, validation)
        print(json.dumps({"status": overall_status, "deployment_run_id": self.run_id, "evidence_sha256": evidence["evidence_sha256"]}, indent=2))
        return evidence


def plan(environment_name: str) -> dict[str, Any]:
    matrix = read_json(ROOT / "config/easa_requirements_matrix.json")
    source_policy = read_json(ROOT / "config/easa_approved_sources.json")
    config = read_json(ROOT / "config/easa_deployment.json")
    approved_count = sum(int(item.get("annual_submission_count") or 0) for item in matrix["requirements"] if item["inventory_approved"])
    eligible_count = sum(int(item.get("annual_submission_count") or 0) for item in matrix["requirements"] if item["inventory_approved"] and item["automation_eligibility"] == "ELIGIBLE")
    result = {
        "status": "VALIDATED_BLOCKED_PENDING_SIGNOFF" if approved_count == 0 else "VALIDATED",
        "environment": environment_name,
        "artifacts": ["Warehouse control plane", "OneLake governance bundle", "2 notebooks", "2 disabled DataPipeline shells", "SemanticModel", "PBIR report", "PaginatedReport review shell"],
        "approved_annual_submission_count": approved_count,
        "eligible_annual_submission_count": eligible_count,
        "coverage_percent": round(eligible_count * 100 / approved_count, 2) if approved_count else None,
        "real_source_count_enabled": sum(1 for item in source_policy["sources"] if item["domain"] != "synthetic_test" and item["ingestion_enabled"]),
        "export_enabled": config["environments"][environment_name]["export_enabled"],
        "transmission_enabled": config["environments"][environment_name]["transmission_enabled"],
        "terraform_mutation": False,
    }
    print(json.dumps(result, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deploy the fail-closed EASA Fabric solution")
    parser.add_argument("command", choices=("plan", "apply"))
    parser.add_argument("--environment", choices=("dev", "test", "prod"), default="dev")
    parser.add_argument("--workspace-id", default=os.environ.get("FABRIC_WORKSPACE_ID", ""))
    args = parser.parse_args(argv)
    if args.command == "plan":
        plan(args.environment)
        return 0
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", args.workspace_id):
        raise ValueError("apply requires --workspace-id or FABRIC_WORKSPACE_ID")
    FabricDeployer(args.workspace_id, args.environment).apply()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, TimeoutError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)