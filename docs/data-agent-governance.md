# Fabric Data Agent Governance

## Grounding boundary

The machine-readable package is `data-agent/definition.json`. It allows only approved Gold tables, curated `ops.vw_*` Warehouse views, and curated KQL `fn_*`/`view_*` functions. It denies Bronze, Silver, quarantine, raw Files, external sources, and operational systems. Action tools are disabled.

## Answer contract

Every substantive answer must include:

1. Answer and entity scope.
2. Grounded drivers.
3. Fixed as-of timestamp and freshness.
4. Value semantics: actual, forecast, target, benchmark, or recommendation.
5. Confidence and evidence completeness.
6. Advisory recommendation and human-approval status.
7. Citations to approved serving objects/business keys.
8. Explicit fictional/synthetic scope limitation.

## Ambiguity

Ask one focused question when airport, period, KPI definition, value type, or unit changes the result materially. Do not infer missing entities, dates, units, or ownership relationships.

## Refusal and escalation

Refuse identity, biometric, credential, restricted-area, vulnerability, live operational, or autonomous-control requests. Never claim an operational action occurred. Route high-impact analytical recommendations to an authorized human; low-confidence or incomplete evidence must be stated explicitly.

## Evaluation

`data-agent/evaluation-cases.json` includes grounding, freshness, ownership-truthfulness, synthetic-benchmark, period ambiguity, identity refusal, staff/gate/BHS control refusal, forecast confidence, provenance, and source-denial tests. These are source-level evaluation contracts; actual Data Agent response execution requires supported target capability and authentication.
