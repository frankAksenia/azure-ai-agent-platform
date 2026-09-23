import os


def get_required_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Create a local .env file or export it before running the app."
        )
    return value


REQUIRED_ENV_VARS = [
    "AZURE_OPENAI_ENDPOINT",
    "CONTENT_SAFETY_ENDPOINT",
    "AI_SEARCH_ENDPOINT",
    "AI_SEARCH_INDEX_NAME",
    "AZURE_OPENAI_LLM_DEPLOYMENT_NAME",
    "AZURE_OPENAI_SLM_DEPLOYMENT_NAME",
    "WEATHER_API_KEY",
    "WEATHER_API_URL",
    "EXCHANGE_RATE_API_KEY",
    "EXCHANGE_RATE_API_URL",
]

for _name in REQUIRED_ENV_VARS:
    get_required_env(_name)


AZURE_OPENAI_ENDPOINT = get_required_env("AZURE_OPENAI_ENDPOINT")
CONTENT_SAFETY_ENDPOINT = get_required_env("CONTENT_SAFETY_ENDPOINT")
AI_SEARCH_ENDPOINT = get_required_env("AI_SEARCH_ENDPOINT")


AZURE_OPENAI_LLM_DEPLOYMENT_NAME = get_required_env("AZURE_OPENAI_LLM_DEPLOYMENT_NAME", "gpt-5")
AZURE_OPENAI_SLM_DEPLOYMENT_NAME = get_required_env("AZURE_OPENAI_SLM_DEPLOYMENT_NAME", "gpt-4")
EMBEDDING_MODEL_DEPLOYMENT_NAME = get_required_env("EMBEDDING_MODEL_DEPLOYMENT_NAME", "text-embedding-3-small")


AI_SEARCH_INDEX_NAME = get_required_env("AI_SEARCH_INDEX_NAME")


USER_NAME = os.getenv("USER_NAME", "Ksenia Frank")
USER_ROLE = os.getenv("USER_ROLE", "Customer")

WEATHER_API_KEY = get_required_env("WEATHER_API_KEY")
WEATHER_API_URL = get_required_env("WEATHER_API_URL")

EXCHANGE_RATE_API_KEY = get_required_env("EXCHANGE_RATE_API_KEY")
EXCHANGE_RATE_API_URL = get_required_env("EXCHANGE_RATE_API_URL")
