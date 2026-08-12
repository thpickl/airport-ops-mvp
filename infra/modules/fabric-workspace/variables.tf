variable "environment" {
  type        = string
  description = "Deployment environment. Production is refused by this demonstration."

  validation {
    condition     = contains(["dev", "test"], var.environment)
    error_message = "environment must be dev or test; production is not permitted for this synthetic demo."
  }
}

variable "resource_prefix" {
  type        = string
  default     = "fao-demo"
  description = "Lowercase resource prefix used to name the workspace."

  validation {
    condition     = can(regex("^[a-z0-9-]{3,24}$", var.resource_prefix))
    error_message = "resource_prefix must be 3-24 lowercase letters, digits, or hyphens."
  }
}

variable "capacity_id" {
  type        = string
  default     = ""
  sensitive   = true
  description = "Fabric Capacity ID. Supply at runtime via TF_VAR_capacity_id; never commit a real ID."

  validation {
    condition     = var.capacity_id == "" || can(regex("^[0-9a-fA-F-]{36}$", var.capacity_id))
    error_message = "capacity_id must be empty or a GUID."
  }
}

variable "enable_workspace_identity" {
  type        = bool
  default     = true
  description = "Assign a system-assigned workspace identity for governed item operations."
}

variable "disclaimer" {
  type        = string
  default     = "Synthetic airport operations demonstration. Real airport identities are public reference anchors only; all operations are synthetic and advisory."
  description = "Workspace description carrying the synthetic-data disclaimer."
}
