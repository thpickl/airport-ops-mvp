from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

QUALITY_DIMENSIONS = (
    "reconciliation",
    "completeness",
    "validity",
    "duplicate",
    "timeliness",
    "cross_field",
)


@dataclass(frozen=True)
class CoverageResult:
    status: str
    approved_annual_submissions: int
    eligible_annual_submissions: int
    coverage_percent: float | None
    target_percent: float
    target_met: bool
    manual_submissions: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ReleaseDecision:
    allowed: bool
    action: str
    blockers: tuple[str, ...]


def _contains_todo(value: Any) -> bool:
    if isinstance(value, str):
        return "TODO" in value.upper()
    if isinstance(value, Mapping):
        return any(_contains_todo(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_todo(item) for item in value)
    return False


def _is_approved(requirement: Mapping[str, Any]) -> bool:
    signoff = requirement.get("compliance_owner_signoff", {})
    return (
        requirement.get("inventory_approved") is True
        and requirement.get("approval_status") == "APPROVED"
        and bool(signoff.get("approved_by"))
        and bool(signoff.get("approved_at_utc"))
        and bool(signoff.get("evidence_reference"))
    )


def validate_requirements_matrix(matrix: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    requirements = matrix.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        return ("requirements must contain at least one inventory row",)

    seen_ids: set[str] = set()
    required_fields = {
        "requirement_id",
        "regulation",
        "submission",
        "airport",
        "authority",
        "frequency",
        "annual_submission_count",
        "deadline",
        "source_fields",
        "validation_rules",
        "output_format",
        "automation_eligibility",
        "approval_status",
        "inventory_approved",
        "official_interface",
        "compliance_owner_signoff",
        "manual_reason",
    }
    for index, requirement in enumerate(requirements):
        prefix = f"requirements[{index}]"
        missing = required_fields - set(requirement)
        if missing:
            errors.append(f"{prefix} missing fields: {sorted(missing)}")
            continue
        requirement_id = str(requirement["requirement_id"])
        if requirement_id in seen_ids:
            errors.append(f"duplicate requirement_id: {requirement_id}")
        seen_ids.add(requirement_id)

        if _is_approved(requirement):
            approval_fields = (
                "regulation",
                "submission",
                "airport",
                "authority",
                "frequency",
                "deadline",
                "source_fields",
                "validation_rules",
                "output_format",
            )
            if any(_contains_todo(requirement[field]) for field in approval_fields):
                errors.append(f"{requirement_id} is approved but contains unresolved TODO values")
            annual_count = requirement.get("annual_submission_count")
            if not isinstance(annual_count, int) or isinstance(annual_count, bool) or annual_count < 1:
                errors.append(f"{requirement_id} approved annual_submission_count must be a positive integer")
            if requirement.get("automation_eligibility") not in {"ELIGIBLE", "MANUAL"}:
                errors.append(f"{requirement_id} approved row must be classified ELIGIBLE or MANUAL")
            if requirement.get("automation_eligibility") == "MANUAL" and not requirement.get("manual_reason"):
                errors.append(f"{requirement_id} manual row requires manual_reason")
            if requirement.get("automation_eligibility") == "ELIGIBLE":
                rules = requirement.get("validation_rules", [])
                rule_types = {rule.get("rule_type") for rule in rules}
                required_types = {
                    "RECONCILIATION",
                    "COMPLETENESS",
                    "VALIDITY",
                    "DUPLICATE",
                    "TIMELINESS",
                    "CROSS_FIELD",
                }
                if rule_types < required_types:
                    errors.append(f"{requirement_id} eligible row is missing validation dimensions: {sorted(required_types - rule_types)}")
                executable_types = {"VALIDITY", "TIMELINESS", "CROSS_FIELD"}
                if any(rule.get("rule_type") in executable_types and not rule.get("sql_expression") for rule in rules):
                    errors.append(f"{requirement_id} eligible row has a non-executable validation rule")
            interface = requirement.get("official_interface", {})
            if interface.get("documented") and _contains_todo(interface.get("reference")):
                errors.append(f"{requirement_id} documented interface reference is unresolved")
            if interface.get("transmission_authorized") and _contains_todo(interface.get("authorization_reference")):
                errors.append(f"{requirement_id} transmission authorization reference is unresolved")
        elif requirement.get("automation_eligibility") == "ELIGIBLE":
            errors.append(f"{requirement_id} cannot be ELIGIBLE before compliance-owner approval")

    return tuple(errors)


def calculate_automation_coverage(matrix: Mapping[str, Any]) -> CoverageResult:
    errors = validate_requirements_matrix(matrix)
    if errors:
        raise ValueError("; ".join(errors))

    target = float(matrix["coverage_policy"]["target_percent"])
    approved_total = 0
    eligible_total = 0
    manual: list[dict[str, Any]] = []
    for requirement in matrix["requirements"]:
        annual_count = requirement.get("annual_submission_count")
        if _is_approved(requirement):
            approved_total += annual_count
            if requirement["automation_eligibility"] == "ELIGIBLE":
                eligible_total += annual_count
            else:
                manual.append(
                    {
                        "requirement_id": requirement["requirement_id"],
                        "submission": requirement["submission"],
                        "annual_submission_count": annual_count,
                        "reason": requirement["manual_reason"],
                    }
                )
        else:
            manual.append(
                {
                    "requirement_id": requirement["requirement_id"],
                    "submission": requirement["submission"],
                    "annual_submission_count": annual_count,
                    "reason": requirement["manual_reason"] or "Inventory row is not approved.",
                }
            )

    if approved_total == 0:
        return CoverageResult(
            status="BLOCKED_NO_APPROVED_INVENTORY",
            approved_annual_submissions=0,
            eligible_annual_submissions=0,
            coverage_percent=None,
            target_percent=target,
            target_met=False,
            manual_submissions=tuple(manual),
        )

    coverage = round(eligible_total * 100.0 / approved_total, 2)
    target_met = coverage >= target
    return CoverageResult(
        status="TARGET_MET" if target_met else "BLOCKED_COVERAGE_TARGET",
        approved_annual_submissions=approved_total,
        eligible_annual_submissions=eligible_total,
        coverage_percent=coverage,
        target_percent=target,
        target_met=target_met,
        manual_submissions=tuple(manual),
    )


def evaluate_release(
    requirement: Mapping[str, Any],
    quality_evidence: Mapping[str, Any],
    approval_evidence: Mapping[str, Any],
    action: str,
) -> ReleaseDecision:
    normalized_action = action.upper()
    if normalized_action not in {"EXPORT", "TRANSMIT"}:
        raise ValueError("action must be EXPORT or TRANSMIT")

    blockers: list[str] = []
    if not _is_approved(requirement):
        blockers.append("REQUIREMENT_NOT_APPROVED")
    if requirement.get("automation_eligibility") != "ELIGIBLE":
        blockers.append("AUTOMATION_NOT_ELIGIBLE")
    for dimension in QUALITY_DIMENSIONS:
        if quality_evidence.get(dimension) != "PASS":
            blockers.append(f"QUALITY_{dimension.upper()}_NOT_PASS")
    if quality_evidence.get("quarantined_count", 0) != 0:
        blockers.append("QUARANTINED_RECORDS_PRESENT")
    if quality_evidence.get("blocking_exception_count", 0) != 0:
        blockers.append("BLOCKING_EXCEPTIONS_PRESENT")
    if approval_evidence.get("status") != "APPROVED":
        blockers.append("HUMAN_APPROVAL_REQUIRED")
    for field in ("approved_by", "approved_at_utc", "evidence_hash", "report_version"):
        if not approval_evidence.get(field):
            blockers.append(f"APPROVAL_{field.upper()}_MISSING")
    if _contains_todo(requirement.get("output_format")):
        blockers.append("AUTHORITY_TEMPLATE_UNVERIFIED")
    if normalized_action == "TRANSMIT":
        interface = requirement.get("official_interface", {})
        if not interface.get("documented") or not interface.get("reference"):
            blockers.append("OFFICIAL_INTERFACE_NOT_DOCUMENTED")
        if not interface.get("transmission_authorized") or not interface.get("authorization_reference"):
            blockers.append("TRANSMISSION_NOT_AUTHORIZED")
    return ReleaseDecision(not blockers, normalized_action, tuple(blockers))