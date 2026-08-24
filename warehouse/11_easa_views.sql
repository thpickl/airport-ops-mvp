/* Curated serving views. Bronze, Silver, raw payloads, and quarantine details are not exposed to report readers. */

CREATE OR ALTER VIEW ops.vw_easa_requirement_inventory AS
WITH ranked AS (
    SELECT requirement_id, regulation, submission_name, airport_scope, authority_name,
           frequency_rule, annual_submission_count, deadline_rule, deadline_timezone,
           output_format_reference, automation_eligibility, approval_status,
           inventory_approved, manual_reason, effective_from, effective_to,
           signoff_evidence_reference, requirement_version_hash, recorded_at_utc,
           is_placeholder,
           ROW_NUMBER() OVER (PARTITION BY requirement_id ORDER BY recorded_at_utc DESC, requirement_version_hash DESC) AS row_number
    FROM easa.requirement_inventory
)
SELECT requirement_id, regulation, submission_name, airport_scope, authority_name,
       frequency_rule, annual_submission_count, deadline_rule, deadline_timezone,
       output_format_reference, automation_eligibility, approval_status,
       inventory_approved, manual_reason, effective_from, effective_to,
       signoff_evidence_reference, requirement_version_hash, recorded_at_utc,
       is_placeholder
FROM ranked WHERE row_number = 1;
GO

CREATE OR ALTER VIEW ops.vw_easa_quality_summary AS
SELECT submission_id,
       COUNT_BIG(*) AS quality_check_count,
       SUM(CASE WHEN result_status = 'PASS' THEN 1 ELSE 0 END) AS passed_check_count,
       SUM(CASE WHEN severity = 'BLOCKING' AND result_status <> 'PASS' THEN 1 ELSE 0 END) AS blocking_failure_count,
       SUM(failed_record_count) AS failed_record_count,
       MAX(evaluated_at_utc) AS evaluated_at_utc
FROM easa.quality_result
GROUP BY submission_id;
GO

CREATE OR ALTER VIEW ops.vw_easa_exception_summary AS
SELECT submission_id,
       COUNT_BIG(*) AS exception_count,
       SUM(CASE WHEN severity = 'BLOCKING' AND exception_status <> 'CLOSED' THEN 1 ELSE 0 END) AS open_blocking_exception_count,
       MAX(opened_at_utc) AS latest_exception_at_utc
FROM easa.submission_exception
GROUP BY submission_id;
GO

CREATE OR ALTER VIEW ops.vw_easa_latest_approval AS
WITH ranked AS (
    SELECT approval_event_id, submission_id, report_version_hash, approval_status,
           approver_object_id, approver_function, decision_at_utc, evidence_sha256,
           ROW_NUMBER() OVER (PARTITION BY submission_id, report_version_hash ORDER BY decision_at_utc DESC, approval_event_id DESC) AS row_number
    FROM easa.approval_event
)
SELECT approval_event_id, submission_id, report_version_hash, approval_status,
       approver_object_id, approver_function, decision_at_utc, evidence_sha256
FROM ranked WHERE row_number = 1;
GO

CREATE OR ALTER VIEW ops.vw_easa_submission_status AS
SELECT s.submission_id, s.requirement_id, s.airport_id,
       s.reporting_period_start, s.reporting_period_end, s.due_at_utc,
       s.submission_version, s.report_version_hash, s.submission_status,
       s.generated_at_utc, s.is_synthetic,
       r.submission_name, r.regulation, r.authority_name, r.output_format_reference,
       r.automation_eligibility, r.inventory_approved,
       COALESCE(q.quality_check_count, 0) AS quality_check_count,
       COALESCE(q.passed_check_count, 0) AS passed_check_count,
       COALESCE(q.blocking_failure_count, 0) AS blocking_failure_count,
       COALESCE(q.failed_record_count, 0) AS failed_record_count,
       COALESCE(x.open_blocking_exception_count, 0) AS open_blocking_exception_count,
       a.approval_status, a.approver_object_id, a.decision_at_utc,
       CASE
           WHEN r.inventory_approved = 0 THEN 'BLOCKED_REQUIREMENT_UNAPPROVED'
           WHEN r.automation_eligibility <> 'ELIGIBLE' THEN 'MANUAL'
           WHEN COALESCE(q.quality_check_count, 0) < 6 THEN 'BLOCKED_QUALITY_INCOMPLETE'
           WHEN COALESCE(q.blocking_failure_count, 0) > 0 THEN 'BLOCKED_QUALITY'
           WHEN COALESCE(x.open_blocking_exception_count, 0) > 0 THEN 'BLOCKED_EXCEPTION'
           WHEN a.approval_status <> 'APPROVED' OR a.report_version_hash <> s.report_version_hash THEN 'AWAITING_HUMAN_APPROVAL'
           ELSE 'READY_FOR_EXPORT'
       END AS release_status,
       CASE WHEN SYSUTCDATETIME() > s.due_at_utc AND s.submission_status NOT IN ('RELEASED', 'SUBMITTED') THEN 1 ELSE 0 END AS is_overdue,
       DATEDIFF(day, CAST(SYSUTCDATETIME() AS date), CAST(s.due_at_utc AS date)) AS days_until_due
FROM easa.submission s
JOIN ops.vw_easa_requirement_inventory r ON r.requirement_id = s.requirement_id
LEFT JOIN ops.vw_easa_quality_summary q ON q.submission_id = s.submission_id
LEFT JOIN ops.vw_easa_exception_summary x ON x.submission_id = s.submission_id
LEFT JOIN ops.vw_easa_latest_approval a ON a.submission_id = s.submission_id AND a.report_version_hash = s.report_version_hash;
GO

CREATE OR ALTER VIEW ops.vw_easa_automation_coverage AS
SELECT
    SUM(CASE WHEN inventory_approved = 1 THEN annual_submission_count ELSE 0 END) AS approved_annual_submission_count,
    SUM(CASE WHEN inventory_approved = 1 AND automation_eligibility = 'ELIGIBLE' THEN annual_submission_count ELSE 0 END) AS eligible_annual_submission_count,
    CAST(100.0 * SUM(CASE WHEN inventory_approved = 1 AND automation_eligibility = 'ELIGIBLE' THEN annual_submission_count ELSE 0 END)
         / NULLIF(SUM(CASE WHEN inventory_approved = 1 THEN annual_submission_count ELSE 0 END), 0) AS decimal(9,2)) AS automation_coverage_percent,
    CASE
        WHEN SUM(CASE WHEN inventory_approved = 1 THEN annual_submission_count ELSE 0 END) = 0 THEN 'BLOCKED_NO_APPROVED_INVENTORY'
        WHEN 100.0 * SUM(CASE WHEN inventory_approved = 1 AND automation_eligibility = 'ELIGIBLE' THEN annual_submission_count ELSE 0 END)
             / NULLIF(SUM(CASE WHEN inventory_approved = 1 THEN annual_submission_count ELSE 0 END), 0) >= 78.0 THEN 'TARGET_MET'
        ELSE 'BLOCKED_COVERAGE_TARGET'
    END AS coverage_status
FROM ops.vw_easa_requirement_inventory;
GO

CREATE OR ALTER VIEW ops.vw_easa_manual_inventory AS
SELECT requirement_id, submission_name, authority_name, airport_scope,
       annual_submission_count, automation_eligibility, approval_status,
       CASE WHEN inventory_approved = 0 THEN 'Inventory not approved' ELSE manual_reason END AS manual_reason
FROM ops.vw_easa_requirement_inventory
WHERE inventory_approved = 0 OR automation_eligibility <> 'ELIGIBLE';
GO

CREATE OR ALTER VIEW ops.vw_easa_data_quality AS
SELECT q.submission_id, s.airport_id, s.requirement_id, q.quality_dimension,
       q.rule_id, q.severity, q.result_status, q.evaluated_record_count,
       q.failed_record_count, q.result_detail, q.evaluated_at_utc
FROM easa.quality_result q
JOIN easa.submission s ON s.submission_id = q.submission_id;
GO

CREATE OR ALTER VIEW ops.vw_easa_exceptions AS
SELECT x.exception_id, x.submission_id, s.airport_id, s.requirement_id,
       x.exception_type, x.severity, x.exception_status, x.exception_detail,
       x.owner_object_id, x.opened_at_utc, x.closed_at_utc,
       x.closure_evidence_reference
FROM easa.submission_exception x
JOIN easa.submission s ON s.submission_id = x.submission_id;
GO

CREATE OR ALTER VIEW ops.vw_easa_evidence AS
SELECT evidence_id, submission_id, evidence_type, object_reference,
       object_version, object_sha256, previous_evidence_sha256,
       actor_object_id, event_at_utc, legal_hold
FROM easa_audit.evidence_ledger;
GO

CREATE OR ALTER VIEW ops.vw_easa_airport AS
SELECT DISTINCT airport_id FROM easa.submission;
GO

CREATE OR ALTER VIEW ops.vw_easa_principal_scope AS
SELECT principal_object_id, principal_name, airport_id, function_name,
       access_status, effective_from_utc, effective_to_utc
FROM easa_security.principal_scope
WHERE access_status = 'ACTIVE'
  AND effective_from_utc <= SYSUTCDATETIME()
  AND (effective_to_utc IS NULL OR effective_to_utc > SYSUTCDATETIME());
GO

CREATE OR ALTER VIEW ops.vw_easa_release_gate_violations AS
SELECT submission_id, requirement_id, airport_id, release_status,
       blocking_failure_count, open_blocking_exception_count,
       approval_status, report_version_hash
FROM ops.vw_easa_submission_status
WHERE release_status <> 'READY_FOR_EXPORT';
GO

CREATE OR ALTER VIEW ops.vw_easa_monitoring_alerts AS
SELECT 'PIPELINE_FAILURE' AS alert_type, 'CRITICAL' AS severity,
             pipeline_run_id AS subject_id, pipeline_name AS subject_name,
             run_status AS alert_detail, started_at_utc AS detected_at_utc
FROM easa_audit.pipeline_run
WHERE run_status = 'FAILED'
UNION ALL
SELECT 'UNAPPROVED_SOURCE_ENABLED', 'CRITICAL', source_id, source_domain,
             'Source is enabled without approval', recorded_at_utc
FROM easa.source_registry
WHERE ingestion_enabled = 1 AND approved = 0
UNION ALL
SELECT 'RELEASE_GATE_BLOCKED', 'WARNING', submission_id, requirement_id,
             release_status, SYSUTCDATETIME()
FROM ops.vw_easa_release_gate_violations
UNION ALL
SELECT 'UNAUTHORIZED_ACTION', 'CRITICAL', e.export_event_id, e.submission_id,
             CONCAT(e.action_type, ':', e.action_status), e.action_at_utc
FROM easa.export_event e
LEFT JOIN ops.vw_easa_submission_status s ON s.submission_id = e.submission_id
WHERE e.action_status = 'SUCCEEDED'
    AND (s.release_status <> 'READY_FOR_EXPORT'
             OR (e.action_type = 'TRANSMIT' AND (e.official_interface_reference IS NULL OR e.authorization_reference IS NULL)));
GO