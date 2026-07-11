# Azure Agent

Azure Agent is a Python sample backend for a customer-support chat agent that runs against Azure AI services.

The app checks user and model text with Azure AI Content Safety, classifies the request as simple or complex, routes simple requests to a smaller deployment and complex requests to a larger deployment, optionally exposes local and MCP tools to the larger model, and returns response metadata such as selected model, latency, and token usage.

## Current Capabilities

- Authenticates to Azure with `DefaultAzureCredential`.
- Uses the OpenAI-compatible Azure AI Foundry endpoint for chat completions.
- Uses Azure AI Content Safety before and after generation.
- Classifies each request as `simple` or `complex`.
- Routes simple requests to the SLM deployment and complex requests to the LLM deployment.
- Supports GPT-5-style deployments by omitting `temperature` and `top_p` when the deployment name starts with `gpt-5`.
- Exposes local function tools for weather and exchange-rate lookup.
- Connects to a remote MCP server and adapts discovered MCP tools into OpenAI function-tool definitions.
- Builds support-agent prompts with persona, safety boundaries, grounding rules, optional session state, user name, and user role.
- Limits retained chat history per model using values from `config.yaml`.
- Includes Bicep templates for Azure AI Foundry, model deployments, Content Safety, AI Project, and scaffolded AI Search resources.

## Project Structure

```text
backend/app/
  main.py                     # Async local entry point and wiring
  config/                     # YAML config loader
  core/                       # Environment settings, Azure clients, logging
  mcp_connection/             # Remote MCP client, registry, and tool adapter
  prompts/                    # System and user prompt builders
  rag/                        # Azure AI Search indexing/retrieval scaffolding
  routing/                    # Intent classification, model routing, tool loop
  safety/                     # Content Safety integration
  services/                   # Chat orchestration
  tokens/                     # Token counting and truncation helpers
  tools/                      # Local weather and exchange-rate tools
infra/                        # Azure Bicep templates
config.yaml                   # Runtime model, safety, retrieval, and tool settings
.env.example                  # Environment variable template
requirements.txt              # Python dependencies
Makefile                      # Azure CLI deployment helpers
```

## Runtime Flow

1. `backend/app/main.py` loads `config.yaml`, creates Azure clients, registers local tools, and connects MCP servers.
2. `ChatService` optionally retrieves grounding context, builds the support-agent system prompt, and checks the user input with Content Safety.
3. `IntentClassifier` classifies the request as `simple` or `complex` using the SLM deployment.
4. `ModelRouter` selects the SLM or LLM deployment.
5. Simple requests are sent directly to the selected model.
6. Complex requests are sent to the LLM with available local and MCP tools. The router executes requested tools and sends tool results back to the model for a final answer.
7. The generated answer is checked with Content Safety before returning the final result.

## Prerequisites

- Python 3.11 or later.
- Azure CLI.
- Access to an Azure subscription that can create or use Azure AI Foundry, model deployments, and Azure AI Content Safety.
- Optional API keys for local tools:
  - OpenWeather for `get_weather`.
  - ExchangeRate-API for `get_exchange_rate`.
- Optional MCP endpoint for web-search-style tools. The default example uses Exa MCP.

Log in before running locally:

```bash
az login
```

The app uses `DefaultAzureCredential`, so local development authenticates through your Azure CLI session.

## Environment Variables

Create a local `.env` file:

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
WEATHER_API_KEY=
WEATHER_API_URL="https://api.openweathermap.org/data/2.5/weather"
EXCHANGE_RATE_API_KEY=
EXCHANGE_RATE_API_URL="https://v6.exchangerate-api.com/v6"
EXA_MCP_URL="https://mcp.exa.ai/mcp"
```

Environment variable reference:

- `AZURE_OPENAI_ENDPOINT`: Azure AI Foundry/OpenAI-compatible endpoint. The Bicep output is `OPENAI_ENDPOINT`.
- `AZURE_OPENAI_LLM_DEPLOYMENT_NAME`: Larger deployment used for complex requests. The current Bicep output is `LLM_MODEL_DEPLOYMENT_NAME_V2`.
- `AZURE_OPENAI_SLM_DEPLOYMENT_NAME`: Smaller deployment used for classification and simple requests. The current Bicep output is `SLM_MODEL_DEPLOYMENT_NAME_V2`.
- `CONTENT_SAFETY_ENDPOINT`: Azure AI Content Safety endpoint. The Bicep output is `CONTENT_SAFETY_ENDPOINT`.
- `USER_NAME`: Optional user name inserted into the support-agent prompt.
- `USER_ROLE`: Optional user role inserted into the support-agent prompt.
- `WEATHER_API_KEY`: API key for the OpenWeather current-weather endpoint.
- `WEATHER_API_URL`: Base URL for weather lookup.
- `EXCHANGE_RATE_API_KEY`: API key for ExchangeRate-API.
- `EXCHANGE_RATE_API_URL`: Base URL for exchange-rate lookup.
- `EXA_MCP_URL`: Streamable HTTP MCP endpoint registered as the `exa` MCP server.

Export the `.env` file before running:

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

## Run Locally

From the repository root:

```bash
python backend/app/main.py
```

The current entry point contains example messages for refund, weather, exchange-rate, and MCP-backed web research requests. To test another prompt, edit `user_message_content` in `backend/app/main.py`.

The script prints a result similar to:

```python
{
    "response": "...",
    "model": "GPT-4.1-Mini (LLM)",
    "latency_ms": 1234.56,
    "token_usage": {
        "prompt_tokens": 100,
        "completion_tokens": 25,
        "total_tokens": 125
    }
}
```

## Configuration

Edit `config.yaml` to tune runtime behavior:

- `content_safety.severity_threshold`: Maximum allowed Content Safety severity.
- `content_safety.safe_response`: Fallback response when user input or model output is blocked.
- `system_instruction.max_tokens`: Maximum token budget for the generated system instruction.
- `ai_search.top_k`: Number of grounding records requested from the retriever.
- `tool_calls`: Tool timeout, retry, and backoff settings.
- `intent_classifier`: Classification generation limits and timeout.
- `llm`: Complex-request model history, output, sampling, and timeout settings.
- `slm`: Simple-request model history, output, sampling, and timeout settings.

## Tools

Local tools are registered in `backend/app/main.py` through `ToolRegistry`:

- `get_weather`: Uses OpenWeather to return current weather for a city.
- `get_exchange_rate`: Uses ExchangeRate-API to return a currency conversion rate.

MCP tools are registered through `create_mcp_registry()` in `backend/app/mcp_connection/bootstrap.py`. The current registry creates one MCP client named `exa`. Discovered MCP tool names are prefixed with the server name to avoid collisions, for example:

```text
exa__web_search_exa
```

Only complex requests receive tool definitions. Simple requests are sent to the SLM without tools.

## Grounding And AI Search

The repository includes Azure AI Search indexing and retrieval modules under `backend/app/rag/`, plus an `infra/modules/ai-search.bicep` template. The active local runtime currently uses `HardcodedGroundingRetriever` in `backend/app/main.py` because Azure AI Search client setup is commented out.

To enable Azure AI Search, restore the commented search client imports and setup in `backend/app/main.py` and `backend/app/core/clients.py`, deploy or provide an AI Search resource, and set the relevant search and embedding environment variables.

## Deploy Azure Infrastructure

The `infra/` directory contains Bicep templates, and the `Makefile` wraps common Azure CLI commands.

Check and adjust the configuration at the top of `Makefile` before deploying:

- `RESOURCE_GROUP`
- `LOCATION`
- `AI_FOUNDRY_NAME`
- `TEMPLATE_FILE`
- `DEPLOYMENT_NAME`

Common commands:

```bash
make validate
make what-if
make deploy
make outputs
make cleanup
```

The current `infra/main.bicep` deploys:

- Azure AI Foundry account.
- Azure AI Project.
- GPT-5 Mini deployment for the LLM path.
- GPT-5 Nano deployment for the SLM path.
- Azure AI Content Safety account.

AI Search and embedding deployment blocks are present but commented out in `infra/main.bicep`.

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
