# ==========================================================
# Azure Infrastructure Makefile
#
# Common development commands for deploying and managing
# Azure AI Foundry resources.
#
# Usage:
#   make deploy
#   make outputs
#   make cleanup
# ==========================================================


# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------

# Azure Resource Group
RESOURCE_GROUP = rg-generalagent-dev

# Azure region
LOCATION = swedencentral

# Azure AI Foundry account name
AI_FOUNDRY_NAME = fndry-generalagent-dev

# Main Bicep template
TEMPLATE_FILE = infra/main.bicep

# Azure deployment name
DEPLOYMENT_NAME = foundry-resources


# Declare targets that are not files
.PHONY: group validate what-if deploy outputs cleanup deleted purge list


# ----------------------------------------------------------
# Create the resource group if it does not already exist.
# Azure simply returns the existing one when rerun.
# ----------------------------------------------------------
group:
	az group create \
		--name $(RESOURCE_GROUP) \
		--location $(LOCATION)


# ----------------------------------------------------------
# Validate the Bicep template without deploying resources.
# Useful for catching syntax or parameter errors.
# ----------------------------------------------------------
validate:
	az deployment group validate \
		--resource-group $(RESOURCE_GROUP) \
		--template-file $(TEMPLATE_FILE) \
		--parameters aiFoundryName=$(AI_FOUNDRY_NAME)


# ----------------------------------------------------------
# Preview infrastructure changes before deployment.
# Similar to Terraform's "plan".
# ----------------------------------------------------------
what-if:
	az deployment group what-if \
		--resource-group $(RESOURCE_GROUP) \
		--template-file $(TEMPLATE_FILE) \
		--parameters aiFoundryName=$(AI_FOUNDRY_NAME)


# ----------------------------------------------------------
# Deploy Azure infrastructure.
# Automatically creates the resource group first.
# ----------------------------------------------------------
deploy: group
	az deployment group create \
		--name $(DEPLOYMENT_NAME) \
		--resource-group $(RESOURCE_GROUP) \
		--template-file $(TEMPLATE_FILE) \
		--parameters aiFoundryName=$(AI_FOUNDRY_NAME)


# ----------------------------------------------------------
# Show deployment outputs such as endpoints and deployment
# names defined in the Bicep outputs.
# ----------------------------------------------------------
outputs:
	az deployment group show \
		--resource-group $(RESOURCE_GROUP) \
		--name $(DEPLOYMENT_NAME) \
		--query properties.outputs \
		--output json


# ----------------------------------------------------------
# Delete the entire resource group and all contained
# resources to stop Azure charges.
# ----------------------------------------------------------
cleanup:
	az group delete \
		--name $(RESOURCE_GROUP) \
		--yes \
		--no-wait


# ----------------------------------------------------------
# List all resource groups in the subscription.
# ----------------------------------------------------------
list:
	az group list --output table


# ----------------------------------------------------------
# Show soft-deleted Cognitive Services accounts.
# Azure keeps them for a retention period before permanent
# removal.
# ----------------------------------------------------------
deleted:
	az cognitiveservices account list-deleted \
		--output table


# ----------------------------------------------------------
# Permanently purge the soft-deleted AI Foundry account.
# Required if you want to immediately reuse the same name.
# ----------------------------------------------------------
purge:
	az cognitiveservices account purge \
		--location $(LOCATION) \
		--resource-group $(RESOURCE_GROUP) \
		--name $(AI_FOUNDRY_NAME)
