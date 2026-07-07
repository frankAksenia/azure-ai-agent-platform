from openai import OpenAI

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.contentsafety import ContentSafetyClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

from core.settings import AZURE_OPENAI_ENDPOINT, CONTENT_SAFETY_ENDPOINT, AI_SEARCH_ENDPOINT, AI_SEARCH_INDEX_NAME


def get_openai_client() -> OpenAI:
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://ai.azure.com/.default"
    )

    return OpenAI(
        base_url=AZURE_OPENAI_ENDPOINT,
        api_key=token_provider,
        timeout=30.0,
        max_retries=2,
    )


def get_content_safety_client() -> ContentSafetyClient:
    return ContentSafetyClient(
        endpoint=CONTENT_SAFETY_ENDPOINT,
        credential=DefaultAzureCredential()
    )


def get_ai_search_client() -> SearchClient:
    return SearchClient(
        endpoint=AI_SEARCH_ENDPOINT,
        index_name=AI_SEARCH_INDEX_NAME,
        credential=DefaultAzureCredential(),
    )


def get_ai_search_index_client() -> SearchIndexClient:
    return SearchIndexClient(
        endpoint=AI_SEARCH_ENDPOINT,
        credential=DefaultAzureCredential(),
    )
