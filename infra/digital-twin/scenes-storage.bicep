targetScope = 'resourceGroup'

@description('Globally unique StorageV2 account name for Azure Digital Twins 3D Scenes Studio.')
param storageAccountName string

@description('Azure region for the storage account.')
param location string

@description('Object ID of the interactive 3D Scenes builder.')
param builderPrincipalId string

@description('Name of the private container used by 3D Scenes Studio.')
param containerName string = '3d-scenes'

module scenesStorage 'br/public:avm/res/storage/storage-account:0.33.0' = {
  params: {
    name: storageAccountName
    location: location
    kind: 'StorageV2'
    skuName: 'Standard_LRS'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    enableTelemetry: false
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    publicNetworkAccess: 'Enabled'
    supportsHttpsTrafficOnly: true
    blobServices: {
      containerDeleteRetentionPolicyDays: 14
      containerDeleteRetentionPolicyEnabled: true
      containers: [
        {
          name: containerName
          publicAccess: 'None'
          roleAssignments: [
            {
              principalId: builderPrincipalId
              principalType: 'User'
              roleDefinitionIdOrName: 'Storage Blob Data Contributor'
            }
          ]
        }
      ]
      corsRules: [
        {
          allowedHeaders: [
            'Authorization'
            'Content-Type'
            'Content-Length'
            'x-ms-version'
            'x-ms-blob-type'
            'x-ms-copy-source'
            'x-ms-requires-sync'
          ]
          allowedMethods: [
            'GET'
            'OPTIONS'
            'POST'
            'PUT'
          ]
          allowedOrigins: [
            'https://explorer.digitaltwins.azure.net'
          ]
          exposedHeaders: []
          maxAgeInSeconds: 3600
        }
      ]
      deleteRetentionPolicyDays: 14
      deleteRetentionPolicyEnabled: true
      isVersioningEnabled: true
    }
    roleAssignments: [
      {
        principalId: builderPrincipalId
        principalType: 'User'
        roleDefinitionIdOrName: 'Reader'
      }
    ]
    tags: {
      SecurityControl: 'Ignore'
      environment: 'dev'
      workload: 'airport-ops-synthetic-demo'
      dataClassification: 'SyntheticMaster'
    }
  }
}

output containerName string = containerName
output containerUrl string = '${scenesStorage.outputs.primaryBlobEndpoint}${containerName}'
output storageAccountId string = scenesStorage.outputs.resourceId
output storageAccountName string = scenesStorage.outputs.name
