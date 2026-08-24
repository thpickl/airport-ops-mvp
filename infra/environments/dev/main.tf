# Microsoft Fabric provider. Authentication is supplied at runtime via Azure CLI,
# Managed Identity, or Service Principal environment variables. No secrets in code.
provider "fabric" {}

# Resolve the Fabric capacity by display name when an explicit capacity_id is not supplied.
data "fabric_capacity" "this" {
  count        = var.capacity_id == "" && var.capacity_name != "" ? 1 : 0
  display_name = var.capacity_name
}

locals {
  effective_capacity_id = var.capacity_id != "" ? var.capacity_id : (
    length(data.fabric_capacity.this) > 0 ? data.fabric_capacity.this[0].id : ""
  )
}

# Reuse an existing workspace when its ID is supplied; otherwise provision one.
data "fabric_workspace" "existing" {
  count = var.existing_workspace_id != "" ? 1 : 0
  id    = var.existing_workspace_id
}

module "workspace" {
  count                     = var.existing_workspace_id == "" ? 1 : 0
  source                    = "../../modules/fabric-workspace"
  environment               = var.environment
  resource_prefix           = var.resource_prefix
  capacity_id               = local.effective_capacity_id
  enable_workspace_identity = var.enable_workspace_identity
}

locals {
  effective_workspace_id = var.existing_workspace_id != "" ? var.existing_workspace_id : one(module.workspace[*].workspace_id)

  effective_workspace_display_name = var.existing_workspace_id != "" ? one(data.fabric_workspace.existing[*].display_name) : one(module.workspace[*].workspace_display_name)
}

module "core_items" {
  source                               = "../../modules/fabric-core-items"
  workspace_id                         = local.effective_workspace_id
  lakehouse_enable_schemas             = var.lakehouse_enable_schemas
  eventhouse_minimum_consumption_units = var.eventhouse_minimum_consumption_units
}
