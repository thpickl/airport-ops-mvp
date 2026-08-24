/* Retrieval checks consumed by deployment validation. Any returned row is a release blocker. */

SELECT requirement_id, submission_name
FROM easa.requirement_inventory
WHERE inventory_approved = 1
  AND (regulation LIKE '%TODO%' OR authority_name LIKE '%TODO%'
       OR deadline_rule LIKE '%TODO%' OR output_format_reference LIKE '%TODO%');
GO

SELECT requirement_id, submission_name
FROM easa.requirement_inventory
WHERE automation_eligibility = 'ELIGIBLE'
  AND (inventory_approved = 0 OR approval_status <> 'APPROVED'
       OR signoff_evidence_reference IS NULL OR annual_submission_count IS NULL);
GO

SELECT submission_id, requirement_id, airport_id, release_status
FROM ops.vw_easa_submission_status
WHERE release_status = 'READY_FOR_EXPORT'
  AND (quality_check_count < 6 OR blocking_failure_count > 0
       OR open_blocking_exception_count > 0 OR approval_status <> 'APPROVED');
GO

SELECT e.export_event_id, e.submission_id, e.action_type, e.action_status
FROM easa.export_event e
LEFT JOIN ops.vw_easa_submission_status s ON s.submission_id = e.submission_id
WHERE e.action_status = 'SUCCEEDED'
  AND (s.release_status <> 'READY_FOR_EXPORT'
       OR (e.action_type = 'TRANSMIT' AND (e.official_interface_reference IS NULL OR e.authorization_reference IS NULL)));
GO

SELECT source_id, source_domain
FROM easa.source_registry
WHERE ingestion_enabled = 1
  AND (approved = 0 OR approved_by_object_id IS NULL OR approved_at_utc IS NULL);
GO