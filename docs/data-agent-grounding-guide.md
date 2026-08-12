# Data Agent Grounding Guide

The Fabric Data Agent source package is read-only and grounded only on approved Gold products, `ops.vw_*` Warehouse views, and curated KQL functions/views. Bronze, Silver, quarantine, raw files, direct passenger/employee records, external sources, secrets, and operational systems are denied.

Every answer must state the KPI definition, source object, filters/scope, data-as-of timestamp, freshness, value semantics (simulated observation, forecast, target, benchmark, or recommendation), confidence, quality warnings, ambiguity, and human-approval requirement. Small cohorts below 10 are suppressed.

Mandatory refusals cover identity, sensitive attributes, re-identification, raw passenger/employee records, credentials, control commands, ATC/aircraft instructions, AODB/BHS/BMS/equipment writes, staff dispatch/scheduling, and unsupported regulatory conclusions.

The 23-case evaluation suite covers grounding, source choice, KPI semantics, synonyms, ambiguity, prompt injection, unauthorized sources, PII, re-identification, stale/missing data, low confidence, small cohorts, cross-source reconciliation, operational control, regulatory conclusions, advisory language, and human approval.

Deployment is capability-probed. A target without a supported Data Agent item-definition path remains `BLOCKED` or `UNSUPPORTED`; source completeness is not deployment evidence.