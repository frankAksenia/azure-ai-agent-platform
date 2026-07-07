# Azure Agent

Azure Agent is a Python sample backend for a customer-support chat agent running on Azure AI services.

The app builds a support-agent system prompt, checks user input with Azure AI Content Safety, classifies the request as simple or complex, routes the request to either a small or larger Azure OpenAI model deployment, checks the generated answer for safety, and returns the response with model, latency, and token-usage metadata.

## What The Project Does

- Uses `DefaultAzureCredential` for Azure authentication.
- Uses Azure OpenAI-compatible chat completions for intent classification and response generation.
- Routes simple requests to the SLM deployment and complex requests to the LLM deployment.
- Applies Azure AI Content Safety checks before and after model generation.
- Builds system instructions with persona, safety boundaries, grounding rules, tool instructions, user name, user role, and optional session state.
- Reads runtime behavior such as token limits, temperatures, and safety thresholds from `config.yaml`.
- Includes Bicep infrastructure templates for Azure AI Foundry, model deployments, and Content Safety resources.

## Project Structure

```text
backend/app/
  main.py                     # Local entry point
  core/                       # Settings, Azure clients, logging
  services/                   # Chat orchestration
  routing/                    # Intent classification and model routing
  safety/                     # Content Safety integration
  prompts/                    # System prompt builder
  tokens/                     # Token counting and truncation
infra/                        # Azure Bicep templates
config.yaml                   # Runtime model and safety configuration
.env.example                  # Environment variable template
requirements.txt              # Python dependencies
```

## Prerequisites

- Python 3.11 or later.
- Azure CLI installed.
- Access to an Azure subscription with permission to use Azure AI Foundry, Azure OpenAI model deployments, and Azure AI Content Safety.
- Azure login configured locally:

```bash
az login
```

The app uses `DefaultAzureCredential`, so it authenticates with your Azure CLI session during local development.

## Set Environment Variables

Create a local `.env` file from the example:

```bash
cp .env.example .env
```

Fill in the values:

```bash
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_LLM_DEPLOYMENT_NAME=
AZURE_OPENAI_SLM_DEPLOYMENT_NAME=
CONTENT_SAFETY_ENDPOINT=
USER_NAME="John Doe"
USER_ROLE="Customer"
```

Environment variables:

- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint or AI Foundry inference endpoint used by the OpenAI client.
- `AZURE_OPENAI_LLM_DEPLOYMENT_NAME`: Deployment name for the larger model used for complex requests.
- `AZURE_OPENAI_SLM_DEPLOYMENT_NAME`: Deployment name for the smaller model used for intent classification and simple requests.
- `CONTENT_SAFETY_ENDPOINT`: Azure AI Content Safety endpoint.
- `USER_NAME`: Optional user name inserted into the support-agent prompt.
- `USER_ROLE`: Optional user role inserted into the support-agent prompt.

The Python code reads these values from the process environment. If you use a `.env` file, export it before running the app:

```bash
set -a
source .env
set +a
```

## Install Dependencies

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Run The App

From the repository root, run:

```bash
python backend/app/main.py
```

The current entry point sends a sample message from `backend/app/main.py`:


The script prints a result similar to:

```python
{
    "response": "...",
    "model": "Phi-4 (SLM)",
    "latency_ms": 1234.56,
    "token_usage": {
        "prompt_tokens": 100,
        "completion_tokens": 25,
        "total_tokens": 125
    }
}
```

To test another message, update `user_message_content` in `backend/app/main.py`.

## Configure Runtime Behavior

Edit `config.yaml` to tune:

- Content Safety severity threshold and fallback response.
- Maximum system-instruction token budget.
- Intent-classifier generation settings.
- LLM and SLM generation settings.
- Number of past messages passed to each model.

## Deploy Azure Infrastructure

The `infra/` directory contains Bicep templates, and the `Makefile` contains Azure CLI helper commands for deployment.

Common commands:

```bash
make deploy
make outputs
make cleanup
```

Before using the Makefile, confirm the values at the top of `Makefile`, including resource group, location, AI Foundry account name, and Bicep template path.

## Development Notes

Regenerate dependencies only when intentionally updating package versions:

```bash
pip freeze > requirements.txt
```

If the virtual environment needs to be recreated:

```bash
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
