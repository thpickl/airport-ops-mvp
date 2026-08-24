using './main.bicep'

// Operator object ID is supplied at runtime; never commit a tenant principal ID.
// Prefer: az deployment group create --parameters operatorPrincipalId=$(az ad signed-in-user show --query id -o tsv)
param operatorPrincipalId = readEnvironmentVariable('AZ_OPERATOR_PRINCIPAL_ID', '')

param location = 'francecentral'
param resourcePrefix = 'faodemo'
param environment = 'dev'
param operatorPrincipalType = 'User'
param iotHubSku = 'F1'
param deployOpenAiModels = true
