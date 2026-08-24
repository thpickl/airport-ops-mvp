targetScope = 'resourceGroup'

@description('Name of the Azure Digital Twins instance.')
param digitalTwinsName string

@description('Azure region supported by Azure Digital Twins.')
param location string

@description('Object ID granted Azure Digital Twins Data Owner at resource scope.')
param dataOwnerPrincipalId string

@description('Existing deterministic role-assignment GUID to adopt without duplication.')
param dataOwnerRoleAssignmentName string

module digitalTwins 'br/public:avm/res/digital-twins/digital-twins-instance:0.5.0' = {
  params: {
    name: digitalTwinsName
    location: location
    enableTelemetry: false
    publicNetworkAccess: 'Enabled'
    roleAssignments: [
      {
        name: dataOwnerRoleAssignmentName
        principalId: dataOwnerPrincipalId
        principalType: 'User'
        roleDefinitionIdOrName: 'Azure Digital Twins Data Owner'
      }
    ]
  }
}

output endpoint string = 'https://${digitalTwins.outputs.hostname}'
output resourceId string = digitalTwins.outputs.resourceId
