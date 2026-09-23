param aiFoundryName string
param aiProjectName string
param location string

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2026-07-01' existing = {
  name: aiFoundryName
}

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2026-07-01' = {
  name: aiProjectName
  parent: aiFoundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

output aiProjectName string = aiProject.name
