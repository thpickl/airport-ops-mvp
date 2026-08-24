variable "environment" {
  type    = string
  default = "dev"
}

variable "resource_prefix" {
  type    = string
  default = "fao-demo"
}

variable "capacity_id" {
  type      = string
  default   = ""
  sensitive = true
}

variable "capacity_name" {
  type        = string
  default     = ""
  description = "Fabric capacity display name, resolved to an ID via the fabric_capacity data source when capacity_id is not set."
}

variable "existing_workspace_id" {
  type        = string
  default     = ""
  description = "Target an existing Fabric workspace by ID. When set, no workspace is created or destroyed and only core items are managed."

  validation {
    condition     = var.existing_workspace_id == "" || can(regex("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", var.existing_workspace_id))
    error_message = "existing_workspace_id must be empty or a GUID."
  }
}

variable "enable_workspace_identity" {
  type    = bool
  default = true
}

variable "lakehouse_enable_schemas" {
  type    = bool
  default = false
}

variable "eventhouse_minimum_consumption_units" {
  type    = number
  default = 0
}
