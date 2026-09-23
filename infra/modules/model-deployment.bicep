param aiFoundryName string
param deploymentName string
param modelName string
param modelFormat string
param modelVersion string
param skuName string = 'GlobalStandard'
param capacity int = 1

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2026-07-01' existing = {
  name: aiFoundryName
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2026-07-01' = {
  parent: aiFoundry
  name: deploymentName
  sku: {
    capacity: capacity
    name: skuName
  }
  properties: {
    model: {
      name: modelName
      format: modelFormat
      version: modelVersion
    }
  }
}

output deploymentName string = modelDeployment.name
