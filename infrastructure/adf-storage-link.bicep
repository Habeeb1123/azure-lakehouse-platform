param dataFactoryName string
param storageAccountName string

resource factory 'Microsoft.DataFactory/factories@2018-06-01' existing = {
  name: dataFactoryName
}

resource lakeConnection 'Microsoft.DataFactory/factories/linkedservices@2018-06-01' = {
  parent: factory
  name: 'ls_adls_olist'
  properties: {
    description: 'Olist data lake connection using the factory managed identity.'
    type: 'AzureBlobFS'
    typeProperties: {
      url: 'https://${storageAccountName}.dfs.core.windows.net'
    }
  }
}

output linkedServiceName string = lakeConnection.name