/*
  Parameterized persona security for Fabric Warehouse.
  Microsoft Learn reference: https://learn.microsoft.com/en-us/fabric/data-warehouse/row-level-security
  Populate security.principal_scope at deployment time with Entra principal names; no identities are committed here.
*/

IF SCHEMA_ID('security') IS NULL
    EXEC('CREATE SCHEMA security');
GO

IF OBJECT_ID('security.principal_scope', 'U') IS NULL
BEGIN
    CREATE TABLE security.principal_scope
    (
        principal_name VARCHAR(320) NOT NULL,
        persona VARCHAR(40) NOT NULL,
        scope_type VARCHAR(20) NOT NULL,
        scope_value VARCHAR(100) NOT NULL,
        is_active BIT NOT NULL
    );
END;
GO

CREATE OR ALTER VIEW security.vw_authorized_airport_performance
AS
SELECT performance.*
FROM ops.vw_airport_performance AS performance
JOIN ops.vw_dim_airport AS airport
    ON performance.airport_id = airport.airport_id
WHERE EXISTS
(
    SELECT 1
    FROM security.principal_scope AS access_map
    WHERE access_map.principal_name = USER_NAME()
      AND access_map.is_active = 1
      AND
      (
          access_map.persona = 'GroupExecutive'
          OR (access_map.scope_type = 'Airport' AND access_map.scope_value = performance.airport_id)
          OR (access_map.scope_type = 'Region' AND access_map.scope_value = airport.region)
      )
);
GO

CREATE OR ALTER VIEW security.vw_authorized_airline_performance
AS
SELECT performance.*
FROM ops.vw_airline_route_performance AS performance
WHERE EXISTS
(
    SELECT 1
    FROM security.principal_scope AS access_map
    WHERE access_map.principal_name = USER_NAME()
      AND access_map.is_active = 1
      AND
      (
          access_map.persona = 'GroupExecutive'
          OR (access_map.scope_type = 'Airline' AND access_map.scope_value = performance.airline_id)
          OR (access_map.scope_type = 'Airport' AND access_map.scope_value = performance.airport_id)
      )
);
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_group_executive') CREATE ROLE airport_ops_group_executive;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_regional_executive') CREATE ROLE airport_ops_regional_executive;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_airport_manager') CREATE ROLE airport_ops_airport_manager;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_airline_partner') CREATE ROLE airport_ops_airline_partner;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_operations') CREATE ROLE airport_ops_operations;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_maintenance') CREATE ROLE airport_ops_maintenance;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_commercial') CREATE ROLE airport_ops_commercial;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_sustainability') CREATE ROLE airport_ops_sustainability;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_compliance') CREATE ROLE airport_ops_compliance;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'airport_ops_it_platform') CREATE ROLE airport_ops_it_platform;
GO

GRANT SELECT ON OBJECT::security.vw_authorized_airport_performance TO airport_ops_group_executive;
GRANT SELECT ON OBJECT::security.vw_authorized_airport_performance TO airport_ops_regional_executive;
GRANT SELECT ON OBJECT::security.vw_authorized_airport_performance TO airport_ops_airport_manager;
GRANT SELECT ON OBJECT::security.vw_authorized_airline_performance TO airport_ops_airline_partner;
GRANT SELECT ON OBJECT::security.vw_authorized_airport_performance TO airport_ops_operations;
GRANT SELECT ON OBJECT::security.vw_authorized_airport_performance TO airport_ops_maintenance;
GRANT SELECT ON OBJECT::security.vw_authorized_airport_performance TO airport_ops_commercial;
GRANT SELECT ON OBJECT::security.vw_authorized_airport_performance TO airport_ops_sustainability;
GRANT SELECT ON OBJECT::security.vw_authorized_airport_performance TO airport_ops_compliance;
GRANT SELECT ON SCHEMA::ops TO airport_ops_it_platform;
GO

/* Only the deployment identity receives INSERT/UPDATE/DELETE on the mapping table. */
GRANT SELECT, INSERT, UPDATE, DELETE ON OBJECT::security.principal_scope TO airport_ops_deployer;
GO