# Azure AI Agent Platform

This project is a Python-based CLI chat application for Azure AI Foundry. It routes user requests through a lightweight intent classifier, invokes either a support or billing agent, applies Azure AI Content Safety checks, and can expose local tools for weather and currency conversion.

The current implementation is an interactive local workflow rather than a web service or REST API. It is designed to be run directly from the repository root and to work with Azure-hosted model deployments and Azure AI Content Safety.

## What it does

- Authenticates to Azure using `DefaultAzureCredential`
- Connects to Azure OpenAI-compatible chat completion endpoints
- Checks user input and model output with Azure AI Content Safety
- Classifies requests as `simple` or `complex`
- Uses a simple responder for low-risk requests
- Routes complex requests to a support agent and can hand off to a billing agent
- Registers local function tools for weather and exchange-rate lookup
- Keeps a local in-memory conversation history for the current session

## Current architecture

```text
backend/app/
  main.py                     # CLI entry point and service wiring
  agents/
    billing_agent/
      billing_agent.py
      billing_agent_prompt.py
    support_agent/
      support_agent.py
      support_agent_prompt.py
  config/
    config.py                 # YAML config loader
  core/
    clients.py                # Azure client factories
    logging.py                # Logging setup
    settings.py               # Env var and default config access
  rag/
    document_loader.py
    embeddings.py
    indexer.py
    retriever.py
    setup.py                  # Azure AI Search scaffolding
  routing/
    intent_classifier.py      # Simple vs complex classification
  safety/
    content_safety.py         # Safety checks
  services/
    chat_service.py           # Orchestration logic
    simple_intent_responder.py
  tools/
    exchange_rate.py          # Currency conversion tool
    tool_registry.py          # Tool registration and schema builder
    weather_tool.py           # Weather lookup tool
infra/
  main.bicep
  modules/
    ai-foundry.bicep
    ai-project.bicep
    ai-search.bicep
    content-safety.bicep
    model-deployment.bicep
config.yaml                  # Runtime settings
requirements.txt             # Python dependencies
Makefile                     # Azure deployment helper commands
```

## Runtime flow

1. `backend/app/main.py` loads `config.yaml`.
2. It initializes Azure clients for OpenAI and Content Safety.
3. It registers local tools in a `ToolRegistry`.
4. It builds the `ContentSafetyService`, `IntentClassificationService`, support agent, billing agent, and chat service.
5. The user enters a prompt in the terminal loop.
6. `ChatService` validates the input with Content Safety.
7. The intent classifier decides whether the request is simple or complex.
8. Simple requests are handled by `SimpleIntentResponder`.
9. Complex requests are processed by the support agent and may hand off to billing.
10. The final answer is checked for safety before returning it to the terminal.

## Prerequisites

- Python 3.11+
- Azure CLI
- Azure subscription access for Azure AI Foundry / Azure OpenAI-compatible deployments
- Azure AI Content Safety resource
- Optional API keys for local tools:
  - OpenWeather
  - ExchangeRate-API

Log in before running locally:

```bash
az login
```

The project uses `DefaultAzureCredential`, so local development relies on your Azure CLI session or another supported identity source.

## Environment variables

Create a local `.env` file or export these variables before running the app.

```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.services.ai.azure.com/api/projects/<project>"
export AZURE_OPENAI_LLM_DEPLOYMENT_NAME="gpt-4o"
export AZURE_OPENAI_SLM_DEPLOYMENT_NAME="phi-4-mini"
export CONTENT_SAFETY_ENDPOINT="https://<your-content-safety-resource>.cognitiveservices.azure.com"
export USER_NAME="John Doe"
export USER_ROLE="Customer"
export WEATHER_API_KEY="<openweather-key>"
export WEATHER_API_URL="https://api.openweathermap.org/data/2.5/weather"
export EXCHANGE_RATE_API_KEY="<exchange-rate-key>"
export EXCHANGE_RATE_API_URL="https://v6.exchangerate-api.com/v6"
```

Optional values used by the Azure AI Search/RAG scaffolding:

```bash
export AI_SEARCH_ENDPOINT="https://<your-search-service>.search.windows.net"
export AI_SEARCH_INDEX_NAME="support-docs"
export EMBEDDING_MODEL_DEPLOYMENT_NAME="text-embedding-3-small"
```

## Configuration

The runtime settings live in `config.yaml`.

```yaml
content_safety:
  severity_threshold: 1
  safe_response: "I cannot generate a response to that question due to content safety concerns."

llm:
  max_past_messages: 10
  max_tokens: 150
  temperature: 0.5
  top_p: 0.5
  timeout_seconds: 30

slm:
  max_past_messages: 5
  max_tokens: 250
  temperature: 0.25
  top_p: 0.25
  timeout_seconds: 15

tool_calls:
  timeout_seconds: 30
  max_retries: 3
  backoff_seconds: 5
```

Key settings:

- `content_safety.severity_threshold`: maximum allowed severity before blocking content
- `content_safety.safe_response`: fallback answer when input or output is blocked
- `llm`: parameters for the larger support model path
- `slm`: parameters for the smaller classification/simple responder path
- `tool_calls`: retry and timeout behavior for local tools

## Local setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the app

From the repository root:

```bash
python backend/app/main.py
```

The app will prompt for a message until you type one of:

```text
quit
exit
bye
```

Example interaction:

```text
[You] I need a refund for my subscription.
[ASSISTANT - BillingAgent] ...
```

## Tools included

The app currently includes two local function tools:

### Weather tool

- Name: `get_weather`
- Purpose: returns current weather for a city
- API: OpenWeather

### Exchange rate tool

- Name: `get_exchange_rate`
- Purpose: returns conversion rate and converted value for two currencies
- API: ExchangeRate-API

## Notes on the current implementation

- This is a local interactive application; there is no HTTP endpoint or REST API layer.
- The project includes Azure AI Search and RAG modules, but the default runtime path is not wired to remote search retrieval in the main CLI loop.
- The support and billing agents are prompt-driven and can perform handoff logic based on intent and tool call results.
- The repo contains Bicep templates under `infra/` for provisioning Azure AI resources, but the app itself is run locally from Python.

## Azure deployment assets

The `infra` folder contains Bicep templates for provisioning:

- Azure AI Foundry account
- AI project
- model deployments
- Azure AI Content Safety
- Azure AI Search scaffolding

Useful commands:

```bash
make validate
make what-if
make deploy
make outputs
make cleanup
```

## Known limitations

- No dedicated web server or FastAPI application is included in the current branch
- No automated test suite is currently implemented in the repo
- Search/RAG functionality is scaffolded but not enabled by default in the interactive chat flow
- Live Azure resources are required for a full end-to-end run

## Development notes

To regenerate the dependency lock file intentionally:

```bash
pip freeze > requirements.txt
```

If you need to recreate the virtual environment:

```bash
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
