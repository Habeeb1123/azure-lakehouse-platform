param dataFactoryName string

resource factory 'Microsoft.DataFactory/factories@2018-06-01' existing = {
  name: dataFactoryName
}

resource bronzeDataset 'Microsoft.DataFactory/factories/datasets@2018-06-01' = {
  parent: factory
  name: 'ds_olist_bronze_folder'
  properties: {
    description: 'Bronze Olist folder used for data presence validation.'
    linkedServiceName: {
      referenceName: 'ls_adls_olist'
      type: 'LinkedServiceReference'
    }
    type: 'Binary'
    typeProperties: {
      location: {
        type: 'AzureBlobFSLocation'
        fileSystem: 'bronze'
        folderPath: 'olist'
      }
    }
  }
}

resource bronzeValidationPipeline 'Microsoft.DataFactory/factories/pipelines@2018-06-01' = {
  parent: factory
  name: 'pl_olist_bronze_validation'
  properties: {
    description: 'Validates that the Bronze Olist folder contains files.'
    activities: [
      {
        name: 'Get_Bronze_Child_Items'
        type: 'GetMetadata'
        policy: {
          timeout: '0.00:05:00'
          retry: 1
          retryIntervalInSeconds: 30
          secureOutput: false
          secureInput: false
        }
        typeProperties: {
          dataset: {
            referenceName: bronzeDataset.name
            type: 'DatasetReference'
          }
          fieldList: [
            'childItems'
          ]
        }
      }
      {
        name: 'Validate_Bronze_Not_Empty'
        type: 'IfCondition'
        dependsOn: [
          {
            activity: 'Get_Bronze_Child_Items'
            dependencyConditions: [
              'Succeeded'
            ]
          }
        ]
        typeProperties: {
          expression: {
            value: '@greater(length(activity(\'Get_Bronze_Child_Items\').output.childItems), 0)'
            type: 'Expression'
          }
          ifTrueActivities: []
          ifFalseActivities: [
            {
              name: 'Fail_Bronze_Empty'
              type: 'Fail'
              typeProperties: {
                message: 'Bronze Olist folder contains no child items.'
                errorCode: 'BRONZE_FOLDER_EMPTY'
              }
            }
          ]
        }
      }
    ]
  }
}

output datasetName string = bronzeDataset.name
output pipelineName string = bronzeValidationPipeline.name