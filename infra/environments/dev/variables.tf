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
