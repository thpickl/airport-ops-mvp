-- Fabric Lakehouse Spark SQL. Real-source execution is blocked until source and requirement approval.

CREATE TABLE IF NOT EXISTS bronze_easa_source_record (
    ingestion_run_id STRING NOT NULL,
    source_id STRING NOT NULL,
    source_domain STRING NOT NULL,
    airport_id STRING,
    source_record_id STRING NOT NULL,
    source_event_at TIMESTAMP,
    received_at_utc TIMESTAMP NOT NULL,
    source_uri STRING NOT NULL,
    payload_json STRING NOT NULL,
    payload_sha256 STRING NOT NULL,
    source_contract_version STRING,
    data_classification STRING NOT NULL,
    is_synthetic BOOLEAN NOT NULL,
    ingested_by STRING NOT NULL
) USING DELTA
TBLPROPERTIES (
    'delta.appendOnly' = 'true',
    'easa.layer' = 'bronze',
    'easa.immutableEvidence' = 'true'
);

CREATE TABLE IF NOT EXISTS silver_easa_validated_record (
    validation_run_id STRING NOT NULL,
    ingestion_run_id STRING NOT NULL,
    requirement_id STRING NOT NULL,
    source_id STRING NOT NULL,
    source_domain STRING NOT NULL,
    airport_id STRING NOT NULL,
    source_record_id STRING NOT NULL,
    source_event_at TIMESTAMP,
    received_at_utc TIMESTAMP NOT NULL,
    conformed_payload_json STRING NOT NULL,
    payload_sha256 STRING NOT NULL,
    validation_rule_set_version STRING NOT NULL,
    validated_at_utc TIMESTAMP NOT NULL,
    is_synthetic BOOLEAN NOT NULL
) USING DELTA
TBLPROPERTIES ('easa.layer' = 'silver');

CREATE TABLE IF NOT EXISTS silver_easa_quarantine (
    quarantine_id STRING NOT NULL,
    validation_run_id STRING NOT NULL,
    ingestion_run_id STRING NOT NULL,
    requirement_id STRING,
    source_id STRING NOT NULL,
    source_record_id STRING NOT NULL,
    airport_id STRING,
    quality_dimension STRING NOT NULL,
    rule_id STRING NOT NULL,
    failure_code STRING NOT NULL,
    failure_detail STRING NOT NULL,
    payload_sha256 STRING NOT NULL,
    quarantined_at_utc TIMESTAMP NOT NULL,
    resolved_at_utc TIMESTAMP,
    resolution_evidence_reference STRING,
    is_synthetic BOOLEAN NOT NULL
) USING DELTA
TBLPROPERTIES (
    'delta.appendOnly' = 'true',
    'easa.layer' = 'silver-quarantine'
);

CREATE TABLE IF NOT EXISTS gold_easa_submission_snapshot (
    submission_id STRING NOT NULL,
    requirement_id STRING NOT NULL,
    airport_id STRING NOT NULL,
    reporting_period_start DATE NOT NULL,
    reporting_period_end DATE NOT NULL,
    due_at_utc TIMESTAMP NOT NULL,
    submission_version INT NOT NULL,
    report_version_hash STRING NOT NULL,
    submission_status STRING NOT NULL,
    quality_status STRING NOT NULL,
    approval_status STRING NOT NULL,
    export_status STRING NOT NULL,
    transmission_status STRING NOT NULL,
    generated_at_utc TIMESTAMP NOT NULL,
    is_synthetic BOOLEAN NOT NULL
) USING DELTA
TBLPROPERTIES ('easa.layer' = 'gold');

CREATE TABLE IF NOT EXISTS gold_easa_quality_result (
    quality_result_id STRING NOT NULL,
    validation_run_id STRING NOT NULL,
    requirement_id STRING NOT NULL,
    airport_id STRING,
    quality_dimension STRING NOT NULL,
    rule_id STRING NOT NULL,
    severity STRING NOT NULL,
    result_status STRING NOT NULL,
    evaluated_record_count BIGINT NOT NULL,
    failed_record_count BIGINT NOT NULL,
    evaluated_at_utc TIMESTAMP NOT NULL,
    rule_version_hash STRING NOT NULL,
    is_synthetic BOOLEAN NOT NULL
) USING DELTA
TBLPROPERTIES ('easa.layer' = 'gold-quality');

CREATE TABLE IF NOT EXISTS gold_easa_approval_event (
    approval_event_id STRING NOT NULL,
    submission_id STRING NOT NULL,
    report_version_hash STRING NOT NULL,
    approval_status STRING NOT NULL,
    approver_object_id STRING NOT NULL,
    approver_function STRING NOT NULL,
    decision_at_utc TIMESTAMP NOT NULL,
    decision_reason STRING,
    evidence_sha256 STRING NOT NULL,
    is_synthetic BOOLEAN NOT NULL
) USING DELTA
TBLPROPERTIES (
    'delta.appendOnly' = 'true',
    'easa.layer' = 'gold-approval'
);

CREATE TABLE IF NOT EXISTS gold_easa_action_event (
    action_event_id STRING NOT NULL,
    submission_id STRING NOT NULL,
    report_version_hash STRING NOT NULL,
    action_type STRING NOT NULL,
    action_status STRING NOT NULL,
    actor_object_id STRING NOT NULL,
    action_at_utc TIMESTAMP NOT NULL,
    blocker_codes_json STRING NOT NULL,
    evidence_sha256 STRING NOT NULL,
    is_synthetic BOOLEAN NOT NULL
) USING DELTA
TBLPROPERTIES (
    'delta.appendOnly' = 'true',
    'easa.layer' = 'gold-action'
);

CREATE TABLE IF NOT EXISTS gold_easa_evidence_ledger (
    evidence_id STRING NOT NULL,
    submission_id STRING,
    evidence_type STRING NOT NULL,
    object_reference STRING NOT NULL,
    object_version STRING NOT NULL,
    object_sha256 STRING NOT NULL,
    previous_evidence_sha256 STRING,
    actor_object_id STRING NOT NULL,
    event_at_utc TIMESTAMP NOT NULL,
    evidence_json STRING NOT NULL,
    legal_hold BOOLEAN NOT NULL,
    is_synthetic BOOLEAN NOT NULL
) USING DELTA
TBLPROPERTIES (
    'delta.appendOnly' = 'true',
    'easa.layer' = 'gold-evidence',
    'easa.immutableEvidence' = 'true'
);