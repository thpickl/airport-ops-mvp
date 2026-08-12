/* Airport operations demo-owned Warehouse objects. Synthetic data only. */

IF SCHEMA_ID('ops') IS NULL
    EXEC('CREATE SCHEMA [ops]');
GO
IF SCHEMA_ID('audit') IS NULL
    EXEC('CREATE SCHEMA [audit]');
GO

IF OBJECT_ID('audit.deployment_run', 'U') IS NULL
BEGIN
    CREATE TABLE audit.deployment_run
    (
        deployment_run_id varchar(64) NOT NULL,
        environment_name varchar(32) NOT NULL,
        artifact_name varchar(256) NOT NULL,
        artifact_type varchar(64) NOT NULL,
        deployment_status varchar(32) NOT NULL,
        status_detail varchar(4000) NULL,
        observed_at datetime2(6) NOT NULL,
        is_synthetic bit NOT NULL
    );
END;
GO

CREATE OR ALTER VIEW ops.vw_deployment_status
AS
SELECT deployment_run_id, environment_name, artifact_name, artifact_type,
       deployment_status, status_detail, observed_at, is_synthetic
FROM audit.deployment_run;
GO
