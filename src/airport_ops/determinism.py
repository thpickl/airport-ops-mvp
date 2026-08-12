"""Canonical serialization, identifiers, and logical checksums."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

GENERATOR_NAMESPACE = uuid.UUID("9a8be8aa-cc7a-5d15-987d-10b523c0039f")


def _json_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_json_value(item) for item in value), key=canonical_json)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("Naive datetimes are not valid deterministic inputs")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, Enum):
        return _json_value(value.value)
    if isinstance(value, Path):
        return value.as_posix()
    return value


def canonical_json(value: Any) -> str:
    """Serialize supported values using stable ordering and no insignificant space."""

    return json.dumps(
        _json_value(value),
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def stable_uuid(entity_type: str, *natural_key_parts: object) -> str:
    """Return a deterministic UUIDv5 for a typed natural key."""

    if not entity_type.strip() or not natural_key_parts:
        raise ValueError("entity_type and at least one natural-key part are required")
    name = canonical_json([entity_type, *natural_key_parts])
    return str(uuid.uuid5(GENERATOR_NAMESPACE, name))


def logical_checksum(records: Iterable[Mapping[str, Any]], key_fields: Iterable[str]) -> str:
    """Hash logical records in deterministic business-key order."""

    keys = tuple(key_fields)
    if not keys:
        raise ValueError("At least one key field is required")
    materialized = list(records)
    for record in materialized:
        missing = [key for key in keys if key not in record]
        if missing:
            raise KeyError(f"Checksum record is missing key fields: {missing}")
    ordered = sorted(
        materialized,
        key=lambda record: tuple(canonical_json(record[key]) for key in keys),
    )
    digest = hashlib.sha256()
    for record in ordered:
        digest.update(canonical_json(record).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()