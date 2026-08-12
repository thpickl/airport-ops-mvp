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

module "workspace" {
  source                    = "../../modules/fabric-workspace"
  environment               = var.environment
  resource_prefix           = var.resource_prefix
  capacity_id               = local.effective_capacity_id
  enable_workspace_identity = var.enable_workspace_identity
}

module "core_items" {
  source                               = "../../modules/fabric-core-items"
  workspace_id                         = module.workspace.workspace_id
  lakehouse_enable_schemas             = var.lakehouse_enable_schemas
  eventhouse_minimum_consumption_units = var.eventhouse_minimum_consumption_units
}
