@description('Name of the Azure Container Registry.')
param name string

@description('Azure region for the Azure Container Registry.')
param location string

@description('Tags applied to the Azure Container Registry.')
param tags object = {}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

@description('Resource ID of the Azure Container Registry.')
output id string = containerRegistry.id

@description('Name of the Azure Container Registry.')
output registryName string = containerRegistry.name

@description('Login server for the Azure Container Registry.')
output loginServer string = containerRegistry.properties.loginServer

@description('Admin username for the Azure Container Registry.')
output username string = containerRegistry.name

#disable-next-line outputs-should-not-contain-secrets
@secure()
@description('Admin password for the Azure Container Registry.')
output password string = containerRegistry.listCredentials().passwords[0].value
