targetScope = 'subscription'

param location string = 'francecentral'
param resourceGroupName string = 'rg-olist-lakehouse-dev'

@description('Microsoft Entra object ID of the identity allowed to upload data.')
param uploaderPrincipalObjectId string

var storageAccountName = 'stolist${uniqueString(subscription().id, resourceGroupName)}'
var dataFactoryName = 'adfolist${uniqueString(subscription().id, resourceGroupName)}'

resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: {
    project: 'olist-lakehouse'
    environment: 'dev'
    managedBy: 'bicep'
  }
}

module dataFactory './datafactory.bicep' = {
  name: 'deployOlistDataFactory'
  scope: resourceGroup
  params: {
    location: location
    dataFactoryName: dataFactoryName
  }
}

module storage './storage.bicep' = {
  name: 'deployOlistStorage'
  scope: resourceGroup
  params: {
    location: location
    storageAccountName: storageAccountName
    uploaderPrincipalObjectId: uploaderPrincipalObjectId
    dataFactoryPrincipalObjectId: dataFactory.outputs.principalId
  }
}

output resourceGroupName string = resourceGroup.name
output storageAccountName string = storage.outputs.storageAccountName
output dataFactoryName string = dataFactory.outputs.dataFactoryName
output dataFactoryPrincipalId string = dataFactory.outputs.principalId