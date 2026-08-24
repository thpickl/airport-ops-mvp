targetScope = 'resourceGroup'

// Ingestion, AI, and ML plane for the airport operations demo.
// Complements infra/environments/dev (Fabric) and infra/digital-twin (ADT).
// All identities are managed; no secret is generated, stored, or output here.

@description('Azure region for regional resources.')
param location string = resourceGroup().location

@description('Resource name prefix. Lowercase letters, digits, hyphens.')
@minLength(3)
@maxLength(12)
param resourcePrefix string = 'faodemo'

@allowed(['dev', 'test'])
@description('Environment tag. Production is intentionally rejected.')
param environment string = 'dev'

@description('Object ID of the operator granted data-plane roles for interactive work.')
param operatorPrincipalId string

@allowed(['User', 'Group', 'ServicePrincipal'])
@description('Principal type of operatorPrincipalId.')
param operatorPrincipalType string = 'User'

@allowed(['F1', 'B1', 'B2', 'S1'])
@description('IoT Hub SKU. F1 is free and limited to one per subscription.')
param iotHubSku string = 'F1'

@description('Deploy Azure OpenAI model deployments. Disable if regional quota is unavailable.')
param deployOpenAiModels bool = true

@description('Chat model deployment verified available in the target region.')
param chatModel object = {
  name: 'gpt-4.1-mini'
  version: '2025-04-14'
  skuName: 'Standard'
  capacity: 10
}

@description('Embedding model deployment verified available in the target region.')
param embeddingModel object = {
  name: 'text-embedding-3-small'
  version: '1'
  skuName: 'GlobalStandard'
  capacity: 10
}

var suffix = uniqueString(resourceGroup().id)
var baseName = '${resourcePrefix}-${environment}'
var tags = {
  workload: 'airport-operations'
  environment: environment
  dataClassification: 'synthetic'
  managedBy: 'bicep'
}

// Built-in role definition IDs (least privilege, data-plane only).
var roles = {
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  cognitiveServicesOpenAIUser: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  eventHubsDataSender: '2b629674-e913-4c01-ae53-ef4638d8f975'
  eventHubsDataReceiver: 'a638d3c7-ab3a-418d-83e6-5f17a39d4fde'
  azureMapsDataReader: '423170ca-a8f6-4b0f-8487-9e4eb8f49bfa'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  iotHubDataContributor: '4fc6c259-987e-4a07-842e-c321cc9d413f'
}

// ---------------------------------------------------------------------------
// Identity
// ---------------------------------------------------------------------------

module platformIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.6.0' = {
  name: 'platform-identity'
  params: {
    name: 'id-${baseName}-platform'
    location: location
    tags: tags
    enableTelemetry: false
  }
}

// ---------------------------------------------------------------------------
// Observability
// ---------------------------------------------------------------------------

module logAnalytics 'br/public:avm/res/operational-insights/workspace:0.16.1' = {
  name: 'log-analytics'
  params: {
    name: 'log-${baseName}'
    location: location
    tags: tags
    enableTelemetry: false
    dataRetention: 30
  }
}

module appInsights 'br/public:avm/res/insights/component:0.8.0' = {
  name: 'app-insights'
  params: {
    name: 'appi-${baseName}'
    location: location
    tags: tags
    enableTelemetry: false
    workspaceResourceId: logAnalytics.outputs.resourceId
  }
}

// ---------------------------------------------------------------------------
// Key Vault - RBAC only, no access policies, purge protection on
// ---------------------------------------------------------------------------

module keyVault 'br/public:avm/res/key-vault/vault:0.14.0' = {
  name: 'key-vault'
  params: {
    name: 'kv-${resourcePrefix}-${substring(suffix, 0, 8)}'
    location: location
    tags: tags
    enableTelemetry: false
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled'
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalytics.outputs.resourceId
      }
    ]
    roleAssignments: [
      {
        principalId: platformIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: roles.keyVaultSecretsUser
      }
      {
        principalId: operatorPrincipalId
        principalType: operatorPrincipalType
        roleDefinitionIdOrName: 'Key Vault Secrets Officer'
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Azure OpenAI - ground-ops orchestration, retail personalisation, grounding
// ---------------------------------------------------------------------------

module openAi 'br/public:avm/res/cognitive-services/account:0.19.0' = {
  name: 'openai'
  params: {
    name: 'oai-${baseName}-${substring(suffix, 0, 6)}'
    location: location
    tags: tags
    enableTelemetry: false
    kind: 'OpenAI'
    sku: 'S0'
    customSubDomainName: 'oai-${baseName}-${substring(suffix, 0, 6)}'
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: true
    managedIdentities: {
      systemAssigned: true
    }
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalytics.outputs.resourceId
      }
    ]
    deployments: deployOpenAiModels
      ? [
          {
            name: chatModel.name
            model: {
              format: 'OpenAI'
              name: chatModel.name
              version: chatModel.version
            }
            sku: {
              name: chatModel.skuName
              capacity: chatModel.capacity
            }
          }
          {
            name: embeddingModel.name
            model: {
              format: 'OpenAI'
              name: embeddingModel.name
              version: embeddingModel.version
            }
            sku: {
              name: embeddingModel.skuName
              capacity: embeddingModel.capacity
            }
          }
        ]
      : []
    roleAssignments: [
      {
        principalId: platformIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: roles.cognitiveServicesOpenAIUser
      }
      {
        principalId: operatorPrincipalId
        principalType: operatorPrincipalType
        roleDefinitionIdOrName: roles.cognitiveServicesOpenAIUser
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Azure Maps - terminal, stand, and flow geospatial layers
// ---------------------------------------------------------------------------

module maps 'br/public:avm/res/maps/account:0.2.1' = {
  name: 'maps'
  params: {
    name: 'map-${baseName}'
    location: 'global'
    tags: tags
    enableTelemetry: false
    sku: 'G2'
    roleAssignments: [
      {
        principalId: platformIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: roles.azureMapsDataReader
      }
      {
        principalId: operatorPrincipalId
        principalType: operatorPrincipalType
        roleDefinitionIdOrName: roles.azureMapsDataReader
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Event Hubs - streaming ingestion plane consumed by Fabric Eventstream
// ---------------------------------------------------------------------------

module eventHubs 'br/public:avm/res/event-hub/namespace:0.15.0' = {
  name: 'event-hubs'
  params: {
    name: 'evhns-${baseName}-${substring(suffix, 0, 6)}'
    location: location
    tags: tags
    enableTelemetry: false
    skuName: 'Standard'
    skuCapacity: 1
    // Fabric Eventstream rejects WorkspaceIdentity for EventHub sources and requires a
    // shared access key, covered by policy exemption fao-demo-eventstream-sas-waiver.
    // Producers still authenticate with Entra; only Eventstream uses a Listen-only key.
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
    zoneRedundant: false
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalytics.outputs.resourceId
      }
    ]
    eventhubs: [
      {
        name: 'flight-events'
        partitionCount: 4
        messageRetentionInDays: 1
        consumerGroups: [{ name: 'fabric-eventstream' }]
      }
      {
        name: 'turnaround-events'
        partitionCount: 4
        messageRetentionInDays: 1
        consumerGroups: [{ name: 'fabric-eventstream' }]
      }
      {
        name: 'passenger-flow'
        partitionCount: 4
        messageRetentionInDays: 1
        consumerGroups: [{ name: 'fabric-eventstream' }]
      }
      {
        name: 'energy-telemetry'
        partitionCount: 2
        messageRetentionInDays: 1
        consumerGroups: [{ name: 'fabric-eventstream' }]
      }
      {
        name: 'baggage-events'
        partitionCount: 4
        messageRetentionInDays: 1
        consumerGroups: [{ name: 'fabric-eventstream' }]
      }
      {
        name: 'asset-telemetry'
        partitionCount: 2
        messageRetentionInDays: 1
        consumerGroups: [{ name: 'fabric-eventstream' }]
      }
      {
        name: 'retail-pos'
        partitionCount: 2
        messageRetentionInDays: 1
        consumerGroups: [{ name: 'fabric-eventstream' }]
      }
      {
        name: 'incident-events'
        partitionCount: 2
        messageRetentionInDays: 1
        consumerGroups: [{ name: 'fabric-eventstream' }]
      }
    ]
    roleAssignments: [
      {
        principalId: platformIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: roles.eventHubsDataSender
      }
      {
        principalId: platformIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: roles.eventHubsDataReceiver
      }
      {
        principalId: operatorPrincipalId
        principalType: operatorPrincipalType
        roleDefinitionIdOrName: roles.eventHubsDataSender
      }
      {
        principalId: operatorPrincipalId
        principalType: operatorPrincipalType
        roleDefinitionIdOrName: roles.eventHubsDataReceiver
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// IoT Hub - stand, gate, checkpoint, and terminal energy device telemetry
// ---------------------------------------------------------------------------

module iotHub 'br/public:avm/res/devices/iot-hub:0.3.0' = {
  name: 'iot-hub'
  params: {
    name: 'iot-${baseName}-${substring(suffix, 0, 6)}'
    location: location
    tags: tags
    enableTelemetry: false
    skuName: iotHubSku
    skuCapacity: 1
    disableLocalAuth: false
    managedIdentities: {
      systemAssigned: true
    }
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalytics.outputs.resourceId
      }
    ]
    roleAssignments: [
      {
        principalId: operatorPrincipalId
        principalType: operatorPrincipalType
        roleDefinitionIdOrName: roles.iotHubDataContributor
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Azure Machine Learning - 15-minute passenger-flow forecasting
// ---------------------------------------------------------------------------

module mlStorage 'br/public:avm/res/storage/storage-account:0.33.0' = {
  name: 'ml-storage'
  params: {
    name: 'st${resourcePrefix}ml${substring(suffix, 0, 8)}'
    location: location
    tags: tags
    enableTelemetry: false
    skuName: 'Standard_LRS'
    kind: 'StorageV2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Enabled'
    roleAssignments: [
      {
        principalId: platformIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: roles.storageBlobDataContributor
      }
      {
        principalId: operatorPrincipalId
        principalType: operatorPrincipalType
        roleDefinitionIdOrName: roles.storageBlobDataContributor
      }
    ]
  }
}

module mlWorkspace 'br/public:avm/res/machine-learning-services/workspace:0.14.0' = {
  name: 'ml-workspace'
  params: {
    name: 'mlw-${baseName}'
    location: location
    tags: tags
    enableTelemetry: false
    sku: 'Basic'
    kind: 'Default'
    associatedStorageAccountResourceId: mlStorage.outputs.resourceId
    associatedKeyVaultResourceId: keyVault.outputs.resourceId
    associatedApplicationInsightsResourceId: appInsights.outputs.resourceId
    publicNetworkAccess: 'Enabled'
    systemDatastoresAuthMode: 'Identity'
    managedIdentities: {
      systemAssigned: true
    }
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalytics.outputs.resourceId
      }
    ]
    roleAssignments: [
      {
        principalId: operatorPrincipalId
        principalType: operatorPrincipalType
        roleDefinitionIdOrName: 'AzureML Data Scientist'
      }
    ]
  }
}

// ---------------------------------------------------------------------------
// Outputs - endpoints and identity references only. No keys, no secrets.
// ---------------------------------------------------------------------------

output platformIdentityClientId string = platformIdentity.outputs.clientId
output platformIdentityPrincipalId string = platformIdentity.outputs.principalId
output platformIdentityResourceId string = platformIdentity.outputs.resourceId
output keyVaultUri string = keyVault.outputs.uri
output keyVaultName string = keyVault.outputs.name
output openAiEndpoint string = openAi.outputs.endpoint
output openAiName string = openAi.outputs.name
output openAiChatDeployment string = deployOpenAiModels ? chatModel.name : ''
output openAiEmbeddingDeployment string = deployOpenAiModels ? embeddingModel.name : ''
output mapsAccountResourceId string = maps.outputs.resourceId
output mapsAccountName string = maps.outputs.name
output eventHubsNamespaceName string = eventHubs.outputs.name
output eventHubsFqdn string = '${eventHubs.outputs.name}.servicebus.windows.net'
output iotHubName string = iotHub.outputs.name
output iotHubHostname string = '${iotHub.outputs.name}.azure-devices.net'
output mlWorkspaceName string = mlWorkspace.outputs.name
output logAnalyticsResourceId string = logAnalytics.outputs.resourceId
output appInsightsName string = appInsights.outputs.name
