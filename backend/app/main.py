import logging
from tools.exchange_rate import ExchangeRateTool
from tools.tool_registry import ToolRegistry
from tools.weather_tool import WeatherTool
from config.config import load_config
# Azure AI Search is disabled for now because this environment does not have
# an AI Search resource provisioned.
# from rag.document_loader import get_documents, upload_documents
# from rag.indexer import create_index
# from rag.retriever import AzureSearchRetriever
from core.clients import (
    get_openai_client,
    get_content_safety_client,
    # get_ai_search_client,
    # get_ai_search_index_client,
)
from core.settings import (
    AZURE_OPENAI_LLM_DEPLOYMENT_NAME,
    AZURE_OPENAI_SLM_DEPLOYMENT_NAME,
    # AI_SEARCH_INDEX_NAME,
    # EMBEDDING_MODEL_DEPLOYMENT_NAME,
    WEATHER_API_URL,
    WEATHER_API_KEY,
    EXCHANGE_RATE_API_URL,
    EXCHANGE_RATE_API_KEY,
)
from safety.content_safety import ContentSafetyService
from routing.intent_classifier import IntentClassifier
from routing.model_router import ModelRouter
from services.chat_service import ChatService
from core.logging import setup_logging

logger = logging.getLogger(__name__)


HARDCODED_GROUNDING_RESULTS = """
[Source 1]
Title: Order: 55-inch 4K Smart TV
Category: order

Content:
Order ID: 12345. Customer purchased a 55-inch 4K Ultra HD Smart TV,
brand: Contoso Electronics, model: UltraView 5500, serial number: TV-987654321.
Order date: 2024-11-15. Delivery address: 123 Main St, Sydney, NSW.
The TV features HDR, built-in Wi-Fi, and voice assistant support.
""".strip()


class HardcodedGroundingRetriever:
    def retrieve(self, question: str, top_k: int = 1) -> str:
        logger.info(
            "Using hard-coded grounding results instead of Azure AI Search: top_k=%s, question_chars=%s",
            top_k,
            len(question),
        )
        return HARDCODED_GROUNDING_RESULTS


# def setup_search_index(openai_client):
#     logger.info(
#         "Setting up Azure AI Search grounding index: index_name=%s, embedding_model=%s",
#         AI_SEARCH_INDEX_NAME,
#         EMBEDDING_MODEL_DEPLOYMENT_NAME,
#     )
#
#     index_result = create_index(
#         index_client=get_ai_search_index_client(),
#         index_name=AI_SEARCH_INDEX_NAME,
#     )
#     logger.info("Index setup result: %s", index_result)
#
#     upload_documents(
#         ai_search_client=get_ai_search_client(),
#         openai_client=openai_client,
#         embedding_model_deployment_name=EMBEDDING_MODEL_DEPLOYMENT_NAME,
#         index_name=AI_SEARCH_INDEX_NAME,
#         documents=get_documents(),
#     )
#     logger.info(
#         "Azure AI Search grounding index setup completed: index_name=%s",
#         AI_SEARCH_INDEX_NAME,
#     )


def main():

    setup_logging()

    # user_message_content = "Can you please refund my order? I bought a TV previously, with an order ID of 12345, and it was not functioning when I first got it out of the box."

    user_message_content = "Whats the weather in Vienna?"

    session_state = "awaiting_order_number - user asked about refund but no order number"

    logger.info("Starting chat service.")

    logger.info(f"User message content: {user_message_content}")

    logger.info(f"Session state: {session_state}")

    config = load_config()

    openai_client = get_openai_client()
    content_safety_client = get_content_safety_client()

    tool_registry = ToolRegistry()

    tool_registry.register_tool(
        WeatherTool(
            weather_api_url=WEATHER_API_URL,
            api_key=WEATHER_API_KEY,
        )
    )

    tool_registry.register_tool(
        ExchangeRateTool(
            exchange_rate_api_url=EXCHANGE_RATE_API_URL,
            api_key=EXCHANGE_RATE_API_KEY,
        )
    )

    # setup_search_index(openai_client)

    safety_service = ContentSafetyService(
        client=content_safety_client,
        severity_threshold=config["content_safety"]["severity_threshold"]
    )

    intent_classifier = IntentClassifier(
        client=openai_client,
        deployment_name=AZURE_OPENAI_SLM_DEPLOYMENT_NAME
    )

    model_router = ModelRouter(
        client=openai_client,
        intent_classifier=intent_classifier,
        llm_deployment=AZURE_OPENAI_LLM_DEPLOYMENT_NAME,
        slm_deployment=AZURE_OPENAI_SLM_DEPLOYMENT_NAME
    )

    # retriever = AzureSearchRetriever(
    #     ai_search_client=get_ai_search_client(),
    #     openai_client=openai_client,
    #     embedding_model_deployment_name=EMBEDDING_MODEL_DEPLOYMENT_NAME,
    # )
    retriever = HardcodedGroundingRetriever()

    chat_service = ChatService(
        safety_service=safety_service,
        model_router=model_router,
        retriever=retriever,
        config=config
    )

    result = chat_service.chat(
        user_message_content=user_message_content,
        session_state=session_state
    )

    print(result)


if __name__ == "__main__":
    main()
