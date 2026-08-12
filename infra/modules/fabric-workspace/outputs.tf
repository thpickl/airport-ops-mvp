output "workspace_id" {
  value       = fabric_workspace.this.id
  description = "The provisioned Fabric workspace ID."
}

output "workspace_display_name" {
  value       = fabric_workspace.this.display_name
  description = "The provisioned Fabric workspace display name."
}
