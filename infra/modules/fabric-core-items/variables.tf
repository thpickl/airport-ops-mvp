variable "workspace_id" {
  type        = string
  description = "Target Fabric workspace ID."
}

variable "lakehouse_enable_schemas" {
  type        = bool
  default     = false
  description = "Enable Lakehouse schemas. Keep false for notebooks that use unqualified saveAsTable names."
}

variable "eventhouse_minimum_consumption_units" {
  type        = number
  default     = 0
  description = "Eventhouse always-on minimum consumption units. 0 disables minimum consumption. Accepted: 0, 2.25, 4.25, 8.5, 13, 18, 26, 34, 50, or 51-322."

  validation {
    condition     = contains([0, 2.25, 4.25, 8.5, 13, 18, 26, 34, 50], var.eventhouse_minimum_consumption_units) || (var.eventhouse_minimum_consumption_units >= 51 && var.eventhouse_minimum_consumption_units <= 322)
    error_message = "eventhouse_minimum_consumption_units must be an accepted value per the Fabric provider schema."
  }
}
