/* Membership is assigned outside source through governed Entra automation. */

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'easa_report_reader') CREATE ROLE easa_report_reader;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'easa_compliance_approver') CREATE ROLE easa_compliance_approver;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'easa_pipeline_writer') CREATE ROLE easa_pipeline_writer;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'easa_auditor') CREATE ROLE easa_auditor;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'easa_security_administrator') CREATE ROLE easa_security_administrator;
GO

GRANT SELECT ON OBJECT::ops.vw_easa_requirement_inventory TO easa_report_reader;
GRANT SELECT ON OBJECT::ops.vw_easa_submission_status TO easa_report_reader;
GRANT SELECT ON OBJECT::ops.vw_easa_automation_coverage TO easa_report_reader;
GRANT SELECT ON OBJECT::ops.vw_easa_manual_inventory TO easa_report_reader;
GRANT SELECT ON OBJECT::ops.vw_easa_data_quality TO easa_report_reader;
GRANT SELECT ON OBJECT::ops.vw_easa_exceptions TO easa_report_reader;
GRANT SELECT ON OBJECT::ops.vw_easa_airport TO easa_report_reader;
GRANT SELECT ON OBJECT::ops.vw_easa_principal_scope TO easa_report_reader;
GRANT SELECT ON OBJECT::ops.vw_easa_monitoring_alerts TO easa_report_reader;
GO

GRANT SELECT ON OBJECT::ops.vw_easa_submission_status TO easa_compliance_approver;
GRANT SELECT ON OBJECT::ops.vw_easa_release_gate_violations TO easa_compliance_approver;
GRANT INSERT, SELECT ON OBJECT::easa.approval_event TO easa_compliance_approver;
GRANT INSERT, SELECT ON OBJECT::easa_audit.evidence_ledger TO easa_compliance_approver;
GO

GRANT INSERT, SELECT ON OBJECT::easa.source_registry TO easa_pipeline_writer;
GRANT INSERT, SELECT ON OBJECT::easa.submission TO easa_pipeline_writer;
GRANT INSERT, SELECT ON OBJECT::easa.quality_result TO easa_pipeline_writer;
GRANT INSERT, SELECT ON OBJECT::easa.quarantine_record TO easa_pipeline_writer;
GRANT INSERT, SELECT ON OBJECT::easa.submission_exception TO easa_pipeline_writer;
GRANT INSERT, SELECT ON OBJECT::easa.export_event TO easa_pipeline_writer;
GRANT INSERT, SELECT ON OBJECT::easa_audit.pipeline_run TO easa_pipeline_writer;
GRANT INSERT, SELECT ON OBJECT::easa_audit.evidence_ledger TO easa_pipeline_writer;
GO

GRANT SELECT ON OBJECT::ops.vw_easa_evidence TO easa_auditor;
GRANT SELECT ON OBJECT::easa.quarantine_record TO easa_auditor;
GRANT SELECT ON OBJECT::easa_audit.pipeline_run TO easa_auditor;
GRANT SELECT ON OBJECT::ops.vw_easa_monitoring_alerts TO easa_auditor;
GO

GRANT INSERT, SELECT ON OBJECT::easa_security.principal_scope TO easa_security_administrator;
GO

/* Deliberately no UPDATE or DELETE grant on approval, export, pipeline, quarantine, or evidence ledgers. */
/* Deliberately no report-reader access to raw payload, Bronze, Silver, quarantine detail, or direct identifiers. */