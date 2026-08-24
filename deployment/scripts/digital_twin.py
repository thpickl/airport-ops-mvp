from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


API_VERSION = "2023-10-31"
TOKEN_RESOURCE = "https://digitaltwins.azure.net"

# 15 base interfaces plus the five ;2 interfaces that carry observed operational state.
EXPECTED_MODEL_COUNT = 20


@dataclass(frozen=True)
class TwinPackage:
    models: list[dict[str, Any]]
    twins: list[dict[str, Any]]
    relationships: list[dict[str, Any]]


def canonical(value: Any) -> str:
    if isinstance(value, str):
        value = json.loads(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def model_is_or_extends(
    actual_model_id: str,
    expected_model_id: str,
    models_by_id: dict[str, dict[str, Any]],
) -> bool:
    pending = [actual_model_id]
    visited: set[str] = set()
    while pending:
        model_id = pending.pop()
        if model_id == expected_model_id:
            return True
        if model_id in visited:
            continue
        visited.add(model_id)
        model = models_by_id.get(model_id, {})
        parent_ids = model.get("extends", [])
        if isinstance(parent_ids, str):
            parent_ids = [parent_ids]
        pending.extend(parent_ids)
    return False


def effective_contents(
    model_id: str, models_by_id: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    model = models_by_id[model_id]
    parent_ids = model.get("extends", [])
    if isinstance(parent_ids, str):
        parent_ids = [parent_ids]
    inherited = [
        content
        for parent_id in parent_ids
        for content in effective_contents(parent_id, models_by_id)
    ]
    return [*inherited, *model.get("contents", [])]


def load_package(
    artifact_root: Path,
    twins_file: str = "sample-twins.json",
    relationships_file: str = "sample-relationships.json",
) -> TwinPackage:
    models = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((artifact_root / "dtdl").glob("*.json"))
    ]
    twins = json.loads(
        (artifact_root / "instances" / twins_file).read_text(encoding="utf-8")
    )
    relationships = json.loads(
        (artifact_root / "relationships" / relationships_file).read_text(encoding="utf-8")
    )

    model_ids = {model["@id"] for model in models}
    twin_ids = {twin["$dtId"] for twin in twins}
    if len(models) != EXPECTED_MODEL_COUNT or len(model_ids) != len(models):
        raise ValueError(f"Expected {EXPECTED_MODEL_COUNT} unique DTDL models")
    if not all(model.get("@context") == "dtmi:dtdl:context;2" for model in models):
        raise ValueError("Every model must use DTDL v2")
    if len(twin_ids) != len(twins):
        raise ValueError("Twin IDs must be unique")
    if not all(twin["$metadata"]["$model"] in model_ids for twin in twins):
        raise ValueError("Every twin model must resolve to the local package")
    if not all(
        relationship["$sourceId"] in twin_ids and relationship["$targetId"] in twin_ids
        for relationship in relationships
    ):
        raise ValueError("Every relationship endpoint must resolve to a local twin")

    models_by_id = {model["@id"]: model for model in models}
    twins_by_id = {twin["$dtId"]: twin for twin in twins}
    for relationship in relationships:
        source_model_id = twins_by_id[relationship["$sourceId"]]["$metadata"]["$model"]
        target_model_id = twins_by_id[relationship["$targetId"]]["$metadata"]["$model"]
        definition = next(
            (
                content
                for content in effective_contents(source_model_id, models_by_id)
                if content.get("@type") == "Relationship"
                and content.get("name") == relationship["$relationshipName"]
            ),
            None,
        )
        if definition is None or not model_is_or_extends(
            target_model_id, definition.get("target", ""), models_by_id
        ):
            raise ValueError(
                f"Relationship {relationship['$relationshipId']} does not match its DTDL definition"
            )
        allowed_properties = {
            item["name"] for item in definition.get("properties", []) if "name" in item
        }
        custom_properties = {name for name in relationship if not name.startswith("$")}
        undeclared_properties = custom_properties - allowed_properties
        if undeclared_properties:
            raise ValueError(
                f"Relationship {relationship['$relationshipId']} has undeclared properties: "
                + ", ".join(sorted(undeclared_properties))
            )

    return TwinPackage(models=models, twins=twins, relationships=relationships)


def normalize_endpoint(value: str) -> str:
    endpoint = value.rstrip("/")
    parsed = urlparse(endpoint)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".digitaltwins.azure.net")
        or parsed.path
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Endpoint must be an Azure Digital Twins HTTPS endpoint")
    return endpoint


def azure_cli_json(arguments: list[str]) -> Any:
    azure_cli = shutil.which("az")
    if not azure_cli:
        raise RuntimeError("Azure CLI was not found")

    command = [azure_cli, *arguments, "--output", "json", "--only-show-errors"]
    if os.name == "nt" and Path(azure_cli).suffix.lower() in {".bat", ".cmd"}:
        bundled_python = Path(azure_cli).resolve().parents[1] / "python.exe"
        if bundled_python.is_file():
            command = [
                str(bundled_python),
                "-IBm",
                "azure.cli",
                *arguments,
                "--output",
                "json",
                "--only-show-errors",
            ]

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError("Azure CLI failed: " + completed.stderr.strip()[:2000])
    return json.loads(completed.stdout)


def get_access_token(subscription: str | None) -> str:
    arguments = ["account", "get-access-token", "--resource", TOKEN_RESOURCE]
    if subscription:
        if not re.fullmatch(r"[0-9a-fA-F-]{36}", subscription):
            raise ValueError("Subscription must be a GUID")
        arguments.extend(["--subscription", subscription])
    token_payload = azure_cli_json(arguments)
    token = token_payload.get("accessToken")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Azure CLI did not return an access token")
    return token


class DigitalTwinsClient:
    def __init__(self, endpoint: str, token: str) -> None:
        self.endpoint = normalize_endpoint(endpoint)
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        payload: Any | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.token}"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if extra_headers:
            headers.update(extra_headers)
        request = Request(self.endpoint + path, data=data, headers=headers, method=method)
        for attempt in range(1, 6):
            try:
                with urlopen(request, timeout=120) as response:
                    body = response.read().decode("utf-8")
                return json.loads(body) if body else None
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code == 429 and attempt < 5:
                    retry_after = min(int(exc.headers.get("Retry-After", "1")), 30)
                    time.sleep(max(retry_after, 1))
                    continue
                raise RuntimeError(
                    f"ADT {method} {path} failed ({exc.code}): {detail[:2000]}"
                ) from exc
            except URLError as exc:
                raise RuntimeError(f"ADT {method} {path} failed: {exc.reason}") from exc
        raise RuntimeError(f"ADT {method} {path} exhausted retries")


def classify_models(
    local_models: list[dict[str, Any]], existing_response: Any
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    existing_models = (
        existing_response.get("value", [])
        if isinstance(existing_response, dict)
        else existing_response
    )
    if not isinstance(existing_models, list):
        raise ValueError("ADT model discovery returned an unexpected response shape")
    existing_by_id = {model["id"]: model for model in existing_models}
    missing: list[dict[str, Any]] = []
    identical: list[str] = []
    conflicts: list[str] = []
    for model in local_models:
        model_id = model["@id"]
        existing = existing_by_id.get(model_id)
        if existing is None:
            missing.append(model)
        elif canonical(existing.get("model")) == canonical(model):
            identical.append(model_id)
        else:
            conflicts.append(model_id)
    return missing, identical, conflicts


def split_twin_payloads(
    package: TwinPackage,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    models_by_id = {model["@id"]: model for model in package.models}
    telemetry_by_model = {
        model["@id"]: {
            content["name"]
            for content in effective_contents(model["@id"], models_by_id)
            if content.get("@type") == "Telemetry"
        }
        for model in package.models
    }
    payloads: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for twin in package.twins:
        telemetry_names = telemetry_by_model[twin["$metadata"]["$model"]]
        twin_payload = {name: value for name, value in twin.items() if name not in telemetry_names}
        telemetry_payload = {
            name: twin[name] for name in sorted(telemetry_names) if name in twin
        }
        payloads.append((twin_payload, telemetry_payload))
    return payloads


def deploy(package: TwinPackage, client: DigitalTwinsClient, apply: bool) -> None:
    existing_models = client.request(
        "GET", f"/models?api-version={API_VERSION}&includeModelDefinition=true"
    )
    missing, identical, conflicts = classify_models(package.models, existing_models)
    print(
        "MODELS"
        f" identical={len(identical)} missing={len(missing)} conflicts={len(conflicts)}"
    )
    if conflicts:
        raise RuntimeError("Immutable model conflicts: " + ", ".join(sorted(conflicts)))

    twin_payloads = split_twin_payloads(package)
    telemetry_messages = sum(bool(telemetry) for _, telemetry in twin_payloads)
    telemetry_values = sum(len(telemetry) for _, telemetry in twin_payloads)
    print(
        "GRAPH"
        f" models={len(package.models)} twins={len(package.twins)}"
        f" relationships={len(package.relationships)}"
        f" telemetry_messages={telemetry_messages} telemetry_values={telemetry_values}"
    )
    if not apply:
        print("DRY_RUN PASS")
        return

    if missing:
        client.request("POST", f"/models?api-version={API_VERSION}", missing)

    for twin_payload, telemetry_payload in twin_payloads:
        twin_id_value = twin_payload["$dtId"]
        twin_id = quote(twin_id_value, safe="")
        client.request(
            "PUT", f"/digitaltwins/{twin_id}?api-version={API_VERSION}", twin_payload
        )
        if telemetry_payload:
            message_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{client.endpoint}/{twin_id_value}/{canonical(telemetry_payload)}",
                )
            )
            client.request(
                "POST",
                f"/digitaltwins/{twin_id}/telemetry?api-version={API_VERSION}",
                telemetry_payload,
                extra_headers={"Message-Id": message_id},
            )

    for relationship in package.relationships:
        source_id = quote(relationship["$sourceId"], safe="")
        relationship_id = quote(relationship["$relationshipId"], safe="")
        client.request(
            "PUT",
            f"/digitaltwins/{source_id}/relationships/{relationship_id}?api-version={API_VERSION}",
            relationship,
        )

    live_response = client.request("GET", f"/models?api-version={API_VERSION}")
    live_models = live_response.get("value", []) if isinstance(live_response, dict) else live_response
    if not isinstance(live_models, list):
        raise RuntimeError("Live model verification returned an unexpected response shape")
    live_model_ids = {model["id"] for model in live_models}
    if not {model["@id"] for model in package.models}.issubset(live_model_ids):
        raise RuntimeError("Live model verification failed")

    for twin in package.twins:
        twin_id = quote(twin["$dtId"], safe="")
        client.request("GET", f"/digitaltwins/{twin_id}?api-version={API_VERSION}")

    for relationship in package.relationships:
        source_id = quote(relationship["$sourceId"], safe="")
        relationship_id = quote(relationship["$relationshipId"], safe="")
        client.request(
            "GET",
            f"/digitaltwins/{source_id}/relationships/{relationship_id}?api-version={API_VERSION}",
        )

    query_result = client.request(
        "POST",
        f"/query?api-version={API_VERSION}",
        {"query": "SELECT TOP(1) FROM DIGITALTWINS"},
    )
    print(
        "VERIFY"
        f" models={len(package.models)} twins={len(package.twins)}"
        f" relationships={len(package.relationships)} telemetry_messages={telemetry_messages}"
        f" query_rows={len(query_result.get('value', []))}"
    )
    print("APPLY PASS")


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Deploy the portable Azure Digital Twins graph")
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--subscription")
    parser.add_argument("--artifact-root", type=Path, default=project_root / "digital-twin")
    parser.add_argument("--twins-file", default="sample-twins.json")
    parser.add_argument("--relationships-file", default="sample-relationships.json")
    parser.add_argument("--apply", action="store_true", help="Apply idempotent model and graph upserts")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        package = load_package(
            args.artifact_root.resolve(), args.twins_file, args.relationships_file
        )
        token = get_access_token(args.subscription)
        client = DigitalTwinsClient(args.endpoint, token)
        deploy(package, client, args.apply)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())