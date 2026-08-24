output "workspace_id" {
  value       = local.effective_workspace_id
  description = "Target Fabric workspace ID. Pass to the notebook deployment path as FABRIC_WORKSPACE_ID."
}

output "workspace_display_name" {
  value       = local.effective_workspace_display_name
  description = "Target Fabric workspace display name."
}

output "lakehouse_id" {
  value = module.core_items.lakehouse_id
}

output "warehouse_id" {
  value = module.core_items.warehouse_id
}

output "eventhouse_id" {
  value = module.core_items.eventhouse_id
}

output "kql_database_id" {
  value = module.core_items.kql_database_id
}

output "warehouse_connection_string" {
  value       = module.core_items.warehouse_connection_string
  description = "Runtime-only Warehouse SQL connection string."
  sensitive   = true
}

output "eventhouse_query_uri" {
  value       = module.core_items.eventhouse_query_uri
  description = "Runtime-only Eventhouse query service URI."
  sensitive   = true
}
