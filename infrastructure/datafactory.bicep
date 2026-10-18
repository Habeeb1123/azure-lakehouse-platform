param location string
param dataFactoryName string

resource dataFactory 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: dataFactoryName
  location: location

  identity: {
    type: 'SystemAssigned'
  }

  properties: {
    publicNetworkAccess: 'Enabled'
  }

  tags: {
    project: 'olist-lakehouse'
    environment: 'dev'
    managedBy: 'bicep'
  }
}

output dataFactoryName string = dataFactory.name
output dataFactoryId string = dataFactory.id
output principalId string = dataFactory.identity.principalId