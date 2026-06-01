@description('Unique environment name used for resource naming.')
param environmentName string

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Tags applied to all resources.')
param tags object = {
  'azd-env-name': environmentName
}

@description('Container image for the ui service.')
param uiImageName string = ''

@description('Container image for the gateway service.')
param gatewayImageName string = ''

@description('Container image for the inventory-mcp service.')
param inventoryMcpImageName string = ''

@description('Container image for the work-orders-api service.')
param workOrdersApiImageName string = ''

@description('Container image for the status-dashboard service.')
param statusDashboardImageName string = ''

@description('Azure AI Foundry project endpoint used by the gateway.')
param foundryProjectEndpoint string = ''

@description('Azure AI Foundry model deployment name used by the gateway.')
param foundryModel string = ''

@description('Foundry Toolbox MCP endpoint used by the gateway.')
param toolboxMcpUrl string = ''

var resourceToken = toLower(uniqueString(subscription().subscriptionId, resourceGroup().id, environmentName))
var sanitizedEnvironmentName = replace(toLower(environmentName), '-', '')

var containerAppsEnvironmentName = '${environmentName}-cae'
var logAnalyticsWorkspaceName = '${environmentName}-logs'
var registryName = 'acr${take(sanitizedEnvironmentName, 15)}${take(resourceToken, 8)}'
var storageAccountName = 'st${take(sanitizedEnvironmentName, 10)}${take(resourceToken, 12)}'
var searchServiceName = '${environmentName}-search'

var uiAppName = '${environmentName}-ui'
var gatewayAppName = '${environmentName}-gateway'
var inventoryMcpAppName = '${environmentName}-inventory-mcp'
var workOrdersApiAppName = '${environmentName}-work-orders-api'
var statusDashboardAppName = '${environmentName}-status-dashboard'

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics'
  params: {
    name: logAnalyticsWorkspaceName
    location: location
    tags: tags
  }
}

module containerRegistry 'modules/container-registry.bicep' = {
  name: 'container-registry'
  params: {
    name: registryName
    location: location
    tags: tags
  }
}

module storageAccount 'modules/storage-account.bicep' = {
  name: 'storage-account'
  params: {
    name: storageAccountName
    location: location
    tags: tags
  }
}

module aiSearch 'modules/ai-search.bicep' = {
  name: 'ai-search'
  params: {
    name: searchServiceName
    location: location
    tags: tags
    sku: 'basic'
  }
}

// Grant AI Search managed identity "Storage Blob Data Reader" on the storage account
resource storageAccountRef 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource searchBlobReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccountRef.id, searchServiceName, 'Storage Blob Data Reader')
  scope: storageAccountRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalId: aiSearch.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

module containerAppsEnvironment 'modules/container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  params: {
    name: containerAppsEnvironmentName
    location: location
    logAnalyticsWorkspaceCustomerId: logAnalytics.outputs.customerId
    logAnalyticsWorkspaceSharedKey: logAnalytics.outputs.sharedKey
    tags: tags
  }
}

module inventoryMcp 'modules/container-app.bicep' = {
  name: 'inventory-mcp-app'
  params: {
    name: inventoryMcpAppName
    serviceName: 'inventory-mcp'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: inventoryMcpImageName
    targetPort: 8001
    env: []
    registryServer: containerRegistry.outputs.loginServer
    registryUsername: containerRegistry.outputs.username
    registryPassword: containerRegistry.outputs.password
    tags: tags
  }
}

module workOrdersApi 'modules/container-app.bicep' = {
  name: 'work-orders-api-app'
  params: {
    name: workOrdersApiAppName
    serviceName: 'work-orders-api'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: workOrdersApiImageName
    targetPort: 8002
    env: []
    registryServer: containerRegistry.outputs.loginServer
    registryUsername: containerRegistry.outputs.username
    registryPassword: containerRegistry.outputs.password
    tags: tags
  }
}

module statusDashboard 'modules/container-app.bicep' = {
  name: 'status-dashboard-app'
  params: {
    name: statusDashboardAppName
    serviceName: 'status-dashboard'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: statusDashboardImageName
    targetPort: 8003
    env: []
    registryServer: containerRegistry.outputs.loginServer
    registryUsername: containerRegistry.outputs.username
    registryPassword: containerRegistry.outputs.password
    tags: tags
  }
}

module gateway 'modules/container-app.bicep' = {
  name: 'gateway-app'
  params: {
    name: gatewayAppName
    serviceName: 'gateway'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: gatewayImageName
    targetPort: 8000
    env: [
      {
        name: 'FOUNDRY_PROJECT_ENDPOINT'
        value: foundryProjectEndpoint
      }
      {
        name: 'FOUNDRY_MODEL'
        value: foundryModel
      }
      {
        name: 'TOOLBOX_MCP_URL'
        value: toolboxMcpUrl
      }
      {
        name: 'INVENTORY_MCP_URL'
        value: 'https://${inventoryMcp.outputs.fqdn}'
      }
      {
        name: 'WORK_ORDERS_API_URL'
        value: 'https://${workOrdersApi.outputs.fqdn}'
      }
      {
        name: 'STATUS_DASHBOARD_URL'
        value: 'https://${statusDashboard.outputs.fqdn}'
      }
    ]
    registryServer: containerRegistry.outputs.loginServer
    registryUsername: containerRegistry.outputs.username
    registryPassword: containerRegistry.outputs.password
    tags: tags
  }
}

module ui 'modules/container-app.bicep' = {
  name: 'ui-app'
  params: {
    name: uiAppName
    serviceName: 'ui'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: uiImageName
    targetPort: 80
    env: [
      {
        name: 'VITE_API_URL'
        value: '/api'
      }
    ]
    registryServer: containerRegistry.outputs.loginServer
    registryUsername: containerRegistry.outputs.username
    registryPassword: containerRegistry.outputs.password
    tags: tags
  }
}

@description('Fully qualified domain name for the ui container app.')
output uiFqdn string = ui.outputs.fqdn

@description('Fully qualified domain name for the gateway container app.')
output gatewayFqdn string = gateway.outputs.fqdn

@description('Fully qualified domain name for the inventory-mcp container app.')
output inventoryMcpFqdn string = inventoryMcp.outputs.fqdn

@description('Fully qualified domain name for the work-orders-api container app.')
output workOrdersApiFqdn string = workOrdersApi.outputs.fqdn

@description('Fully qualified domain name for the status-dashboard container app.')
output statusDashboardFqdn string = statusDashboard.outputs.fqdn

@description('Storage account name for FoundryIQ documents.')
output storageAccountName string = storageAccount.outputs.name

@description('Azure AI Search service name.')
output searchServiceName string = aiSearch.outputs.name

@description('Azure AI Search endpoint.')
output searchServiceEndpoint string = aiSearch.outputs.endpoint

@description('Container registry login server used for service images.')
output registryLoginServer string = containerRegistry.outputs.loginServer
