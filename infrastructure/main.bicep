targetScope = 'subscription'

param location string = 'francecentral'
param resourceGroupName string = 'rg-olist-lakehouse-dev'

var storageAccountName = 'stolist${uniqueString(subscription().id, resourceGroupName)}'

resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: {
    project: 'olist-lakehouse'
    environment: 'dev'
    managedBy: 'bicep'
  }
}

module storage './storage.bicep' = {
  name: 'deployOlistStorage'
  scope: resourceGroup
  params: {
    location: location
    storageAccountName: storageAccountName
  }
}

output resourceGroupName string = resourceGroup.name
output storageAccountName string = storage.outputs.storageAccountName