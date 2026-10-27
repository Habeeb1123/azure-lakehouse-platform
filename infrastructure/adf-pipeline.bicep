param dataFactoryName string

resource factory 'Microsoft.DataFactory/factories@2018-06-01' existing = {
  name: dataFactoryName
}

resource bronzeDataset 'Microsoft.DataFactory/factories/datasets@2018-06-01' = {
  parent: factory
  name: 'ds_olist_bronze_folder'
  properties: {
    description: 'Dataset for the Olist Bronze folder.'
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
    description: 'Validates the presence of all nine expected Olist Parquet files and the ingestion manifest.'
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
        name: 'Validate_Required_Bronze_Files'
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
            value: '@and(contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'olist_customers_dataset.parquet\'), contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'olist_geolocation_dataset.parquet\'), contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'olist_order_items_dataset.parquet\'), contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'olist_order_payments_dataset.parquet\'), contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'olist_order_reviews_dataset.parquet\'), contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'olist_orders_dataset.parquet\'), contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'olist_products_dataset.parquet\'), contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'olist_sellers_dataset.parquet\'), contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'product_category_name_translation.parquet\'), contains(string(activity(\'Get_Bronze_Child_Items\').output.childItems), \'_ingestion_manifest.json\'))'
            type: 'Expression'
          }
          ifTrueActivities: []
          ifFalseActivities: [
            {
              name: 'Fail_Required_Bronze_Files_Missing'
              type: 'Fail'
              typeProperties: {
                message: 'One or more required Olist Bronze files are missing.'
                errorCode: 'BRONZE_REQUIRED_FILE_MISSING'
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