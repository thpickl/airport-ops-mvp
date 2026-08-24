/* EASA regulatory reporting control plane. No official rule is encoded without signed inventory evidence. */

IF SCHEMA_ID('easa') IS NULL EXEC('CREATE SCHEMA [easa]');
GO
IF SCHEMA_ID('easa_audit') IS NULL EXEC('CREATE SCHEMA [easa_audit]');
GO
IF SCHEMA_ID('easa_security') IS NULL EXEC('CREATE SCHEMA [easa_security]');
GO

IF OBJECT_ID('easa.requirement_inventory', 'U') IS NULL
BEGIN
    CREATE TABLE easa.requirement_inventory (
        requirement_id varchar(128) NOT NULL,
        regulation varchar(1000) NOT NULL,
        submission_name varchar(500) NOT NULL,
        airport_scope varchar(500) NOT NULL,
        authority_name varchar(500) NOT NULL,
        frequency_rule varchar(500) NOT NULL,
        annual_submission_count int NULL,
        deadline_rule varchar(1000) NOT NULL,
        deadline_timezone varchar(128) NOT NULL,
        source_fields_json varchar(8000) NOT NULL,
        validation_rules_json varchar(8000) NOT NULL,
        output_format_reference varchar(1000) NOT NULL,
        automation_eligibility varchar(64) NOT NULL,
        approval_status varchar(64) NOT NULL,
        inventory_approved bit NOT NULL,
        manual_reason varchar(2000) NULL,
        effective_from date NULL,
        effective_to date NULL,
        signoff_evidence_reference varchar(1000) NULL,
        requirement_version_hash char(64) NOT NULL,
        recorded_at_utc datetime2(6) NOT NULL,
        is_placeholder bit NOT NULL
    );
END;
GO

IF OBJECT_ID('easa.source_registry', 'U') IS NULL
BEGIN
    CREATE TABLE easa.source_registry (
        source_id varchar(256) NOT NULL,
        source_domain varchar(64) NOT NULL,
        source_system varchar(500) NOT NULL,
        connector_type varchar(128) NOT NULL,
        connection_reference varchar(1000) NOT NULL,
        data_contract_reference varchar(1000) NOT NULL,
        data_classification varchar(128) NOT NULL,
        approved bit NOT NULL,
        ingestion_enabled bit NOT NULL,
        approved_by_object_id varchar(256) NULL,
        approved_at_utc datetime2(6) NULL,
        source_version_hash char(64) NOT NULL,
        recorded_at_utc datetime2(6) NOT NULL
    );
END;
GO

IF OBJECT_ID('easa.submission', 'U') IS NULL
BEGIN
    CREATE TABLE easa.submission (
        submission_id varchar(128) NOT NULL,
        requirement_id varchar(128) NOT NULL,
        airport_id varchar(128) NOT NULL,
        reporting_period_start date NOT NULL,
        reporting_period_end date NOT NULL,
        due_at_utc datetime2(6) NOT NULL,
        submission_version int NOT NULL,
        report_version_hash char(64) NOT NULL,
        submission_status varchar(64) NOT NULL,
        generated_at_utc datetime2(6) NOT NULL,
        is_synthetic bit NOT NULL
    );
END;
GO

IF OBJECT_ID('easa.quality_result', 'U') IS NULL
BEGIN
    CREATE TABLE easa.quality_result (
        quality_result_id varchar(128) NOT NULL,
        submission_id varchar(128) NOT NULL,
        quality_dimension varchar(32) NOT NULL,
        rule_id varchar(128) NOT NULL,
        rule_version_hash char(64) NOT NULL,
        severity varchar(16) NOT NULL,
        result_status varchar(16) NOT NULL,
        evaluated_record_count bigint NOT NULL,
        failed_record_count bigint NOT NULL,
        result_detail varchar(4000) NULL,
        evaluated_at_utc datetime2(6) NOT NULL
    );
END;
GO

IF OBJECT_ID('easa.quarantine_record', 'U') IS NULL
BEGIN
    CREATE TABLE easa.quarantine_record (
        quarantine_id varchar(128) NOT NULL,
        submission_id varchar(128) NULL,
        source_id varchar(256) NOT NULL,
        airport_id varchar(128) NULL,
        source_record_id varchar(256) NOT NULL,
        quality_dimension varchar(32) NOT NULL,
        rule_id varchar(128) NOT NULL,
        failure_code varchar(128) NOT NULL,
        payload_sha256 char(64) NOT NULL,
        quarantined_at_utc datetime2(6) NOT NULL,
        resolution_status varchar(32) NOT NULL,
        resolution_evidence_reference varchar(1000) NULL
    );
END;
GO

IF OBJECT_ID('easa.submission_exception', 'U') IS NULL
BEGIN
    CREATE TABLE easa.submission_exception (
        exception_id varchar(128) NOT NULL,
        submission_id varchar(128) NOT NULL,
        exception_type varchar(64) NOT NULL,
        severity varchar(16) NOT NULL,
        exception_status varchar(32) NOT NULL,
        exception_detail varchar(4000) NOT NULL,
        owner_object_id varchar(256) NULL,
        opened_at_utc datetime2(6) NOT NULL,
        closed_at_utc datetime2(6) NULL,
        closure_evidence_reference varchar(1000) NULL
    );
END;
GO

IF OBJECT_ID('easa.approval_event', 'U') IS NULL
BEGIN
    CREATE TABLE easa.approval_event (
        approval_event_id varchar(128) NOT NULL,
        submission_id varchar(128) NOT NULL,
        report_version_hash char(64) NOT NULL,
        approval_status varchar(32) NOT NULL,
        approver_object_id varchar(256) NOT NULL,
        approver_function varchar(128) NOT NULL,
        decision_at_utc datetime2(6) NOT NULL,
        decision_reason varchar(4000) NULL,
        evidence_sha256 char(64) NOT NULL
    );
END;
GO

IF OBJECT_ID('easa.export_event', 'U') IS NULL
BEGIN
    CREATE TABLE easa.export_event (
        export_event_id varchar(128) NOT NULL,
        submission_id varchar(128) NOT NULL,
        report_version_hash char(64) NOT NULL,
        action_type varchar(32) NOT NULL,
        action_status varchar(32) NOT NULL,
        output_format_reference varchar(1000) NOT NULL,
        official_interface_reference varchar(1000) NULL,
        authorization_reference varchar(1000) NULL,
        exported_object_reference varchar(1000) NULL,
        exported_object_sha256 char(64) NULL,
        actor_object_id varchar(256) NOT NULL,
        action_at_utc datetime2(6) NOT NULL
    );
END;
GO

IF OBJECT_ID('easa_audit.evidence_ledger', 'U') IS NULL
BEGIN
    CREATE TABLE easa_audit.evidence_ledger (
        evidence_id varchar(128) NOT NULL,
        submission_id varchar(128) NULL,
        evidence_type varchar(64) NOT NULL,
        object_reference varchar(1000) NOT NULL,
        object_version varchar(256) NOT NULL,
        object_sha256 char(64) NOT NULL,
        previous_evidence_sha256 char(64) NULL,
        actor_object_id varchar(256) NOT NULL,
        event_at_utc datetime2(6) NOT NULL,
        evidence_json varchar(8000) NOT NULL,
        legal_hold bit NOT NULL
    );
END;
GO

IF OBJECT_ID('easa_audit.pipeline_run', 'U') IS NULL
BEGIN
    CREATE TABLE easa_audit.pipeline_run (
        pipeline_run_id varchar(128) NOT NULL,
        pipeline_name varchar(256) NOT NULL,
        environment_name varchar(32) NOT NULL,
        source_id varchar(256) NULL,
        run_status varchar(32) NOT NULL,
        input_count bigint NOT NULL,
        accepted_count bigint NOT NULL,
        quarantined_count bigint NOT NULL,
        started_at_utc datetime2(6) NOT NULL,
        completed_at_utc datetime2(6) NULL,
        correlation_id varchar(256) NOT NULL,
        evidence_sha256 char(64) NOT NULL
    );
END;
GO

IF OBJECT_ID('easa_security.principal_scope', 'U') IS NULL
BEGIN
    CREATE TABLE easa_security.principal_scope (
        principal_object_id varchar(256) NOT NULL,
        principal_name varchar(500) NOT NULL,
        airport_id varchar(128) NOT NULL,
        function_name varchar(128) NOT NULL,
        access_status varchar(32) NOT NULL,
        approved_by_object_id varchar(256) NOT NULL,
        effective_from_utc datetime2(6) NOT NULL,
        effective_to_utc datetime2(6) NULL,
        evidence_reference varchar(1000) NOT NULL
    );
END;
GO