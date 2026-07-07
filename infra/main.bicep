param aiFoundryName string = 'default'
param aiProjectName string = '${aiFoundryName}-proj'
param contentSafetyName string = '${aiFoundryName}-content-safety'
param location string = resourceGroup().location

param llm_model string = 'gpt-4.1-mini'
param slm_model string = 'Phi-4-mini-instruct'
param embedding_model string = 'text-embedding-3-small'

module aiFoundry './modules/ai-foundry.bicep' = {
  name: 'deploy-ai-foundry'
  params: {
    aiFoundryName: aiFoundryName
    location: location
  }
}

module aiProject './modules/ai-project.bicep' = {
  name: 'deploy-ai-project'
  params: {
    aiFoundryName: aiFoundryName
    aiProjectName: aiProjectName
    location: location
  }
  dependsOn: [
    aiFoundry
  ]
}

module llmDeployment './modules/model-deployment.bicep' = {
  name: 'deploy-llm-model'
  params: {
    aiFoundryName: aiFoundryName
    deploymentName: llm_model
    modelName: llm_model
    modelFormat: 'OpenAI'
    modelVersion: '2025-04-14'
    skuName: 'GlobalStandard'
    capacity: 1
  }
  dependsOn: [
    aiFoundry
  ]
}

module slmDeployment './modules/model-deployment.bicep' = {
  name: 'deploy-slm-model'
  params: {
    aiFoundryName: aiFoundryName
    deploymentName: slm_model
    modelName: slm_model
    modelFormat: 'Microsoft'
    modelVersion: '1'
    skuName: 'GlobalStandard'
    capacity: 1
  }
  dependsOn: [
    llmDeployment
  ]
}

module embeddingDeployment './modules/model-deployment.bicep' = {
  name: 'deploy-embedding-model'
  params: {
    aiFoundryName: aiFoundryName
    deploymentName: embedding_model
    modelName: embedding_model
    modelFormat: 'OpenAI'
    modelVersion: '1'
    skuName: 'GlobalStandard'
    capacity: 1
  }
  dependsOn: [
    slmDeployment
  ]
}

module aiSearch './modules/ai-search.bicep' = {
  name: 'deploy-ai-search'
  params: {
    aiSearchName: '${aiFoundryName}-search'
    location: location
  }
  dependsOn: [
    embeddingDeployment
  ]
}

module contentSafety './modules/content-safety.bicep' = {
  name: 'deploy-content-safety'
  params: {
    contentSafetyName: contentSafetyName
    location: location
  }
}

output OPENAI_ENDPOINT string = aiFoundry.outputs.openAiEndpoint
output LLM_MODEL_DEPLOYMENT_NAME string = llmDeployment.outputs.deploymentName
output SLM_MODEL_DEPLOYMENT_NAME string = slmDeployment.outputs.deploymentName
output CONTENT_SAFETY_ENDPOINT string = contentSafety.outputs.contentSafetyEndpoint
output AI_SEARCH_ENDPOINT string = aiSearch.outputs.AI_SEARCH_SERVICE_ENDPOINT
output AI_SEARCH_SERVICE_NAME string = aiSearch.outputs.AI_SEARCH_SERVICE_DEPLOYMENT_NAME
