output "lakehouse_id" {
  value       = fabric_lakehouse.this.id
  description = "AirportOpsLakehouse item ID."
}

output "warehouse_id" {
  value       = fabric_warehouse.this.id
  description = "AirportOpsWarehouse item ID."
}

output "warehouse_connection_string" {
  value       = fabric_warehouse.this.properties.connection_string
  description = "Warehouse SQL connection string (runtime only)."
  sensitive   = true
}

output "eventhouse_id" {
  value       = fabric_eventhouse.this.id
  description = "AirportOpsEventhouse item ID."
}

output "eventhouse_query_uri" {
  value       = fabric_eventhouse.this.properties.query_service_uri
  description = "Eventhouse query service URI (runtime only)."
  sensitive   = true
}

output "kql_database_id" {
  value       = fabric_kql_database.this.id
  description = "AirportOpsRealtime KQL database item ID."
}
