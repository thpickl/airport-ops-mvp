# All resources and attributes verified against microsoft/fabric provider v1.12.1.

resource "fabric_lakehouse" "this" {
  display_name = "AirportOpsLakehouse"
  description  = "Synthetic airport operations medallion lakehouse (Bronze/Silver/Gold)."
  workspace_id = var.workspace_id

  configuration = {
    enable_schemas = var.lakehouse_enable_schemas
  }
}

resource "fabric_warehouse" "this" {
  display_name = "AirportOpsWarehouse"
  description  = "Synthetic airport operations serving warehouse."
  workspace_id = var.workspace_id

  configuration = {
    collation_type = "Latin1_General_100_BIN2_UTF8"
  }
}

resource "fabric_eventhouse" "this" {
  display_name = "AirportOpsEventhouse"
  description  = "Synthetic airport operations real-time eventhouse."
  workspace_id = var.workspace_id

  configuration = var.eventhouse_minimum_consumption_units > 0 ? {
    minimum_consumption_units = var.eventhouse_minimum_consumption_units
  } : null
}

resource "fabric_kql_database" "this" {
  display_name = "AirportOpsRealtime"
  description  = "Synthetic airport operations KQL database."
  workspace_id = var.workspace_id

  configuration = {
    database_type = "ReadWrite"
    eventhouse_id = fabric_eventhouse.this.id
  }
}
