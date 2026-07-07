param aiFoundryName string = 'default'
param aiProjectName string = '${aiFoundryName}-proj'
param contentSafetyName string = '${aiFoundryName}-content-safety'
param location string = resourceGroup().location

param llm_model string = 'gpt-4.1-mini'
param slm_model string = 'Phi-4-mini-instruct'

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
    modelName: 'Phi-4-mini-instruct'
    modelFormat: 'Microsoft'
    modelVersion: '1'
    skuName: 'GlobalStandard'
    capacity: 1
  }
  dependsOn: [
    llmDeployment
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
