param contentSafetyName string
param location string

resource contentSafety 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: contentSafetyName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'ContentSafety'
  properties: {
    customSubDomainName: contentSafetyName
    disableLocalAuth: true
  }
}

output contentSafetyName string = contentSafety.name
output contentSafetyEndpoint string = 'https://${contentSafety.properties.customSubDomainName}.cognitiveservices.azure.com/'
