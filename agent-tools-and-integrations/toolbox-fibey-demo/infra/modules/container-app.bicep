@description('Name of the Container App.')
param name string

@description('azd service name associated with the Container App.')
param serviceName string

@description('Azure region for the Container App.')
param location string

@description('Resource ID of the Container Apps environment.')
param environmentId string

@description('Container image to deploy.')
param containerImage string

@description('Ingress target port for the container.')
param targetPort int

@description('Environment variables to inject into the container.')
param env array

@description('Container registry server used for pulling the image.')
param registryServer string

@description('Container registry username used for pulling the image.')
param registryUsername string

@secure()
@description('Container registry password used for pulling the image.')
param registryPassword string

@description('Minimum replica count for the Container App.')
param minReplicas int = 1

@description('Maximum replica count for the Container App.')
param maxReplicas int = 3

@description('Tags applied to the Container App.')
param tags object = {}

var resolvedContainerImage = empty(containerImage) ? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' : containerImage
var appTags = union(tags, {
  'azd-service-name': serviceName
})

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: appTags
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
      }
      registries: [
        {
          server: registryServer
          username: registryUsername
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: [
        {
          name: 'registry-password'
          value: registryPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: serviceName
          image: resolvedContainerImage
          env: env
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

@description('Resource ID of the Container App.')
output id string = containerApp.id

@description('Fully qualified domain name of the Container App ingress endpoint.')
output fqdn string = containerApp.properties.configuration.ingress.fqdn
