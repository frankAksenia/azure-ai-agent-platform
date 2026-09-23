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
    "AZURE_OPENAI_LLM_DEPLOYMENT_NAME",
    "AZURE_OPENAI_SLM_DEPLOYMENT_NAME",
]

for _name in REQUIRED_ENV_VARS:
    get_required_env(_name)


AZURE_OPENAI_ENDPOINT = get_required_env("AZURE_OPENAI_ENDPOINT")
CONTENT_SAFETY_ENDPOINT = get_required_env("CONTENT_SAFETY_ENDPOINT")
AI_SEARCH_ENDPOINT = os.getenv("AI_SEARCH_ENDPOINT", "")

AZURE_OPENAI_LLM_DEPLOYMENT_NAME = get_required_env("AZURE_OPENAI_LLM_DEPLOYMENT_NAME", "gpt-5")
AZURE_OPENAI_SLM_DEPLOYMENT_NAME = get_required_env("AZURE_OPENAI_SLM_DEPLOYMENT_NAME", "gpt-4")
EMBEDDING_MODEL_DEPLOYMENT_NAME = os.getenv("EMBEDDING_MODEL_DEPLOYMENT_NAME", "text-embedding-3-small")

AI_SEARCH_INDEX_NAME = os.getenv("AI_SEARCH_INDEX_NAME", "")

USER_NAME = os.getenv("USER_NAME", "Ksenia Frank")
USER_ROLE = os.getenv("USER_ROLE", "Customer")

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_API_URL = os.getenv("WEATHER_API_URL", "https://api.openweathermap.org/data/2.5/weather")

EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")
EXCHANGE_RATE_API_URL = os.getenv("EXCHANGE_RATE_API_URL", "https://v6.exchangerate-api.com/v6")
