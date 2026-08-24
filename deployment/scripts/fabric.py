"""Plan, submit, and validate the Fabric notebook deployment graph.

Authentication and target identifiers are accepted only from environment variables.
The default state file is outside the repository and may contain runtime item IDs.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
API_BASE = "https://api.fabric.microsoft.com/v1"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
CONDITIONAL_KEYS = {"data_agent", "fabric_app", "rayfin"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _token_provider() -> Callable[[], str] | None:
    """Opt-in refresh so a poll outliving the access token is not read as a failed job.

    Set FABRIC_TOKEN_COMMAND to a command that prints a bearer token on stdout, e.g.
    'az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv'.
    """
    command = os.environ.get("FABRIC_TOKEN_COMMAND", "").strip()
    if not command:
        return None

    def refresh() -> str:
        argv = shlex.split(command)
        # Windows launchers such as az.cmd are not resolvable without a PATHEXT lookup.
        resolved = shutil.which(argv[0])
        if not resolved:
            raise RuntimeError(f"FABRIC_TOKEN_COMMAND executable not found: {argv[0]}")
        completed = subprocess.run(
            [resolved, *argv[1:]],
            capture_output=True,
            text=True,
            check=True,
            shell=False,
        )
        token = completed.stdout.strip()
        if not token:
            raise RuntimeError("FABRIC_TOKEN_COMMAND produced no token")
        return token

    return refresh


def _load_manifest() -> dict[str, Any]:
    return json.loads((ROOT / "deployment" / "manifest.json").read_text(encoding="utf-8"))


def _state_path() -> Path:
    configured = os.environ.get("FAO_DEPLOYMENT_STATE_PATH")
    return Path(configured) if configured else Path(tempfile.gettempdir()) / "fao-demo-runtime-state.json"


def _ordered_items(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    pending = {item["key"]: item for item in manifest["items"]}
    ordered: list[dict[str, Any]] = []
    resolved: set[str] = set()
    while pending:
        ready = sorted(
            (item for item in pending.values() if set(item.get("depends_on", [])) <= resolved),
            key=lambda item: item["key"],
        )
        if not ready:
            raise ValueError(f"Artifact dependency cycle or unknown dependency: {sorted(pending)}")
        for item in ready:
            ordered.append(item)
            resolved.add(item["key"])
            del pending[item["key"]]
    return ordered


class FabricClient:
    def __init__(
        self,
        token: str,
        timeout_seconds: int = 90,
        token_provider: Callable[[], str] | None = None,
    ) -> None:
        if not token or token.startswith("${"):
            raise ValueError("FABRIC_ACCESS_TOKEN must be supplied at runtime")
        self._token = token
        self._timeout_seconds = timeout_seconds
        self._token_provider = token_provider

    def request(
        self,
        method: str,
        path_or_url: str,
        payload: dict[str, Any] | None = None,
        accepted: set[int] | None = None,
    ) -> tuple[int, dict[str, str], dict[str, Any]]:
        accepted = accepted or {200}
        url = path_or_url if path_or_url.startswith("https://") else API_BASE + path_or_url
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        last_error = ""
        for attempt in range(6):
            request = urllib.request.Request(
                url,
                data=body,
                method=method,
                headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                    response_body = response.read()
                    parsed = json.loads(response_body) if response_body else {}
                    headers = {key.lower(): value for key, value in response.headers.items()}
                    if response.status not in accepted:
                        raise RuntimeError(f"Unexpected HTTP {response.status}")
                    return response.status, headers, parsed
            except urllib.error.HTTPError as exc:
                last_error = exc.read().decode("utf-8", errors="replace")[:4000]
                # A poll outliving the token is a client-side condition, not a job failure.
                if exc.code == 401 and self._token_provider is not None and attempt < 5:
                    self._token = self._token_provider()
                    continue
                if exc.code not in RETRYABLE_STATUS or attempt == 5:
                    raise RuntimeError(f"Fabric HTTP {exc.code}: {last_error}") from exc
                time.sleep(min(2**attempt, 30))
            except urllib.error.URLError as exc:
                last_error = str(exc.reason)
                if attempt == 5:
                    raise RuntimeError(f"Fabric request failed: {last_error}") from exc
                time.sleep(min(2**attempt, 30))
        raise RuntimeError(last_error or "Fabric request failed")

    def poll(self, operation_url: str, timeout_seconds: int) -> dict[str, Any]:
        started = time.monotonic()
        while time.monotonic() - started < timeout_seconds:
            _, headers, body = self.request("GET", operation_url, accepted={200})
            status = str(body.get("status", "")).lower()
            if status in {"completed", "succeeded"}:
                return body
            if status in {"failed", "cancelled", "deduped"}:
                raise RuntimeError(f"Fabric operation ended with {status}: {json.dumps(body)[:4000]}")
            time.sleep(min(int(headers.get("retry-after", "5")), 30))
        raise TimeoutError(
            "Fabric operation did not complete within "
            f"{timeout_seconds}s. The job is still running server-side; this is a client-side "
            f"timeout, not a deployment failure. Resume polling at {operation_url} and do not "
            "resubmit, which would start a competing run."
        )


def plan() -> dict[str, Any]:
    manifest = _load_manifest()
    ordered = _ordered_items(manifest)
    result = {
        "mode": "plan",
        "status": "VALIDATED",
        "environment": "dev",
        "resource_prefix": "fao-demo",
        "deployment_attempted": False,
        "artifact_order": [
            {
                "key": item["key"],
                "type": item["type"],
                "depends_on": item.get("depends_on", []),
                "status": "UNSUPPORTED" if item["key"] == "rayfin" else "IMPLEMENTED",
            }
            for item in ordered
        ],
        "blockers": [
            "Authentication and target workspace are required for apply.",
            "Native Rayfin is unsupported; the configurable app module remains source-only.",
        ],
    }
    print(json.dumps(result, indent=2))
    return result


def _runtime_values() -> tuple[str, str, str, str]:
    workspace_id = os.environ.get("FABRIC_WORKSPACE_ID", "")
    capacity_reference = os.environ.get("FABRIC_CAPACITY_REFERENCE", "")
    orchestrator_notebook_id = os.environ.get("FABRIC_ORCHESTRATOR_NOTEBOOK_ID", "")
    token = os.environ.get("FABRIC_ACCESS_TOKEN", "")
    if not all((workspace_id, capacity_reference, orchestrator_notebook_id, token)):
        raise ValueError(
            "Apply requires FABRIC_WORKSPACE_ID, FABRIC_CAPACITY_REFERENCE, "
            "FABRIC_ORCHESTRATOR_NOTEBOOK_ID, and FABRIC_ACCESS_TOKEN"
        )
    return workspace_id, capacity_reference, orchestrator_notebook_id, token


def apply(timeout_seconds: int) -> dict[str, Any]:
    workspace_id, capacity_reference, notebook_id, token = _runtime_values()
    client = FabricClient(token, token_provider=_token_provider())

    # Notebook 10 skips as SKIPPED_PREREQUISITE without both serving endpoints, so
    # claiming platform deployment without them silently produces no BI artifacts.
    warehouse_sql_endpoint = os.environ.get("FABRIC_WAREHOUSE_SQL_ENDPOINT", "")
    kql_query_uri = os.environ.get("FABRIC_KQL_QUERY_URI", "")
    include_platform = bool(warehouse_sql_endpoint and kql_query_uri)

    parameters = {
        "workspace_id": {"value": workspace_id, "type": "string"},
        "capacity_reference": {"value": capacity_reference, "type": "string"},
        "environment_name": {"value": "dev", "type": "string"},
        "resource_prefix": {"value": "fao-demo", "type": "string"},
        "simulation_profile": {"value": os.environ.get("FAO_SCALE_PROFILE", "smoke"), "type": "string"},
        "deployment_mode": {"value": "apply", "type": "string"},
        "run_second_pass": {"value": "true", "type": "bool"},
        "include_platform_deployment": {"value": "true" if include_platform else "false", "type": "bool"},
    }
    if include_platform:
        parameters["warehouse_sql_endpoint"] = {"value": warehouse_sql_endpoint, "type": "string"}
        parameters["kql_query_uri"] = {"value": kql_query_uri, "type": "string"}
        conditional = os.environ.get("FABRIC_DEPLOY_CONDITIONAL_ARTIFACTS", "").strip().lower() in {"1", "true", "yes"}
        parameters["deploy_conditional_artifacts"] = {"value": "true" if conditional else "false", "type": "bool"}

    execution_data = {"executionData": {"parameters": parameters}}
    path = f"/workspaces/{urllib.parse.quote(workspace_id)}/items/{urllib.parse.quote(notebook_id)}/jobs/instances?jobType=RunNotebook"
    status, headers, body = client.request("POST", path, execution_data, accepted={202})
    location = headers.get("location")
    if status != 202 or not location:
        raise RuntimeError("Fabric job submission did not return 202 and a Location header")
    completed = client.poll(location, timeout_seconds)
    result = {
        "mode": "apply",
        "status": "DEPLOYMENT_ATTEMPTED",
        "deployment_attempted": True,
        "job_status": completed.get("status", "completed"),
        "include_platform_deployment": include_platform,
        "platform_deployment_note": (
            "Serving endpoints supplied; semantic model, report, and Data Agent were requested."
            if include_platform
            else "FABRIC_WAREHOUSE_SQL_ENDPOINT and FABRIC_KQL_QUERY_URI were not supplied; "
            "notebook 10 is skipped and no semantic model, report, or Data Agent is deployed."
        ),
        "observed_at_utc": _utc_now(),
        "post_deployment_validation_required": True,
    }
    _state_path().write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


def validate() -> dict[str, Any]:
    workspace_id = os.environ.get("FABRIC_WORKSPACE_ID", "")
    token = os.environ.get("FABRIC_ACCESS_TOKEN", "")
    if not workspace_id or not token:
        raise ValueError("Validation requires FABRIC_WORKSPACE_ID and FABRIC_ACCESS_TOKEN")
    client = FabricClient(token)
    _, _, body = client.request("GET", f"/workspaces/{urllib.parse.quote(workspace_id)}/items", accepted={200})
    actual_items = body.get("value", [])
    manifest = _load_manifest()
    evidence: list[dict[str, Any]] = []
    mandatory_missing: list[str] = []
    for item in _ordered_items(manifest):
        matches = [
            actual
            for actual in actual_items
            if actual.get("displayName") == item["display_name"] and actual.get("type") == item["type"]
        ]
        if len(matches) == 1:
            evidence.append({"key": item["key"], "type": item["type"], "status": "DEPLOYED", "item_id": matches[0].get("id", "")})
        elif item["key"] == "rayfin":
            evidence.append({"key": item["key"], "type": item["type"], "status": "UNSUPPORTED", "item_id": ""})
        elif item["key"] in CONDITIONAL_KEYS:
            evidence.append({"key": item["key"], "type": item["type"], "status": "BLOCKED", "item_id": ""})
        else:
            mandatory_missing.append(item["key"])
            evidence.append({"key": item["key"], "type": item["type"], "status": "BLOCKED", "item_id": ""})
    result = {
        "mode": "validate",
        "status": "VALIDATED" if not mandatory_missing else "BLOCKED",
        "observed_at_utc": _utc_now(),
        "workspace_retrieved": True,
        "mandatory_missing": mandatory_missing,
        "artifacts": evidence,
    }
    _state_path().write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if mandatory_missing:
        raise RuntimeError(f"Mandatory Fabric artifacts were not retrieved: {mandatory_missing}")
    return result


def status() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        result = {"status": "BLOCKED", "detail": "No runtime deployment state exists", "path": str(path)}
    else:
        result = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(result, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fabric airport-operations deployment driver")
    parser.add_argument("command", choices=("plan", "apply", "validate", "status"))
    # A two-pass smoke run exceeds two hours; the previous 7200s default timed out mid-run.
    parser.add_argument("--timeout-seconds", type=int, default=21600)
    args = parser.parse_args(argv)
    if args.command == "plan":
        plan()
    elif args.command == "apply":
        apply(args.timeout_seconds)
    elif args.command == "validate":
        validate()
    else:
        status()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, TimeoutError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)