param aiFoundryName string
param location string

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: aiFoundryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    allowProjectManagement: true
    customSubDomainName: aiFoundryName
    disableLocalAuth: false
  }
}

output aiFoundryName string = aiFoundry.name
output openAiEndpoint string = 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/openai/v1'
