from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.contentsafety import ContentSafetyClient

from core.settings import AZURE_OPENAI_ENDPOINT, CONTENT_SAFETY_ENDPOINT


def get_openai_client() -> OpenAI:
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://ai.azure.com/.default"
    )

    return OpenAI(
        base_url=AZURE_OPENAI_ENDPOINT,
        api_key=token_provider
    )


def get_content_safety_client() -> ContentSafetyClient:
    return ContentSafetyClient(
        endpoint=CONTENT_SAFETY_ENDPOINT,
        credential=DefaultAzureCredential()
    )
