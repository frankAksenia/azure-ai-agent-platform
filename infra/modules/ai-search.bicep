param aiSearchName string
param location string

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: aiSearchName
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    disableLocalAuth: true
  }
}

output AI_SEARCH_SERVICE_ENDPOINT string = 'https://${searchService.name}.search.windows.net'
output AI_SEARCH_SERVICE_DEPLOYMENT_NAME string = searchService.name
