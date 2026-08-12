locals {
  workspace_display_name = "${var.resource_prefix}-${var.environment}-airport-ops"
}

# Verified against microsoft/fabric provider v1.12.1 (resources/workspace).
resource "fabric_workspace" "this" {
  display_name = local.workspace_display_name
  description  = var.disclaimer
  capacity_id  = var.capacity_id != "" ? var.capacity_id : null
  identity     = var.enable_workspace_identity ? { type = "SystemAssigned" } : null

  # Guard against accidental deletion of the demo workspace and its items.
  lifecycle {
    prevent_destroy = true
  }
}
