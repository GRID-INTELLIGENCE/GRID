# Minimal Terraform to provision Azure Event Hub and Blob Storage
# Replace with your resource group and location as needed

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "grid-integration-rg"
  location = "East US"
}

# Event Hubs namespace
resource "azurerm_eventhub_namespace" "ns" {
  name                = "grid-eventhub-ns"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Standard"
  capacity            = 1
}

# Event Hubs (topics)
resource "azurerm_eventhub" "raw_events" {
  name                = "raw-events"
  namespace_name      = azurerm_eventhub_namespace.ns.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count      = 6
  message_retention    = 7
}

resource "azurerm_eventhub" "features" {
  name                = "features"
  namespace_name      = azurerm_eventhub_namespace.ns.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count      = 6
  message_retention    = 7
}

resource "azurerm_eventhub" "predictions" {
  name                = "predictions"
  namespace_name      = azurerm_eventhub_namespace.ns.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count      = 3
  message_retention    = 7
}

resource "azurerm_eventhub" "dlq" {
  name                = "raw-events-dlq"
  namespace_name      = azurerm_eventhub_namespace.ns.name
  resource_group_name = azurerm_resource_group.rg.name
  partition_count      = 3
  message_retention    = 7
}

# Storage account for snapshots
resource "azurerm_storage_account" "st" {
  name                     = "gridstorageacct"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "snapshots" {
  name                  = "snapshots"
  storage_account_name  = azurerm_storage_account.st.name
  container_access_type = "private"
}
