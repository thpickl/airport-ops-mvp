/* Least-privilege database roles. Add members outside this script through governed identity automation. */

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_report_reader')
    CREATE ROLE airport_ops_report_reader;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_data_agent_reader')
    CREATE ROLE airport_ops_data_agent_reader;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_deployer')
    CREATE ROLE airport_ops_deployer;
GO

GRANT SELECT ON SCHEMA::ops TO airport_ops_report_reader;
GRANT SELECT ON OBJECT::ops.vw_data_agent_grounding TO airport_ops_data_agent_reader;
GRANT SELECT ON OBJECT::ops.vw_data_agent_enterprise_grounding TO airport_ops_data_agent_reader;
GRANT SELECT ON OBJECT::ops.vw_deployment_status TO airport_ops_deployer;
GRANT INSERT, SELECT ON OBJECT::audit.deployment_run TO airport_ops_deployer;
GO

/* Deliberately no Bronze/Silver grants and no operational write roles. */
