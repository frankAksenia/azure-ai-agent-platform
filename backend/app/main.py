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


    logger.info("Starting chat service.")

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

    chat_service = ChatService(
        safety_service=safety_service,
        model_router=model_router,
        config=config
    )


    while user_input.lower() not in ["quit", "exit", "bye"]:
        # Input filtering (from Unit 3)
        if not safety_service.is_text_safe(user_input):
            print("\n[ASSISTANT] I cannot process that request due to content safety.")
            user_input = input("\n[You] ")
            continue

        # Process through manager (delegates to appropriate specialist)
        response = manager_agent.process_message(user_input)

        if not safety_service.is_text_safe(response):
            print(f"\n[ASSISTANT] {config['content_safety']['safe_response']}")
        else:
            print(f"\n[ASSISTANT] {response}")

        user_input = input("\n[You] ")

    # Display routing metrics
    print("\n" + "=" * 50)
    print("CONVERSATION ENDED")
    print("=" * 50)

    metrics = manager_agent.get_metrics()
    print("\nROUTING METRICS:")
    print("-" * 40)
    print(f"Total requests routed: {metrics['total_requests']}")
    print(f"  → RefundAgent: {metrics['refund']}")
    print(f"  → ProductAgent: {metrics['product']}")
    print(f"  → AccountAgent: {metrics['account']}")
    print(f"  → Unable to route: {metrics['unable_to_route']}")




if __name__ == "__main__":
    main()
