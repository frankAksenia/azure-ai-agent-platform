import logging
from backend.app.agents.support_agent.support_agent import SupportAgent
from backend.app.agents.billing_agent.billing_agent import BillingAgent
from backend.app.services.simple_intent_responder import SimpleIntentResponder
from tools.exchange_rate import ExchangeRateTool
from tools.tool_registry import ToolRegistry
from tools.weather_tool import WeatherTool
from config.config import load_config
from core.clients import get_openai_client, get_content_safety_client

from core.settings import (
    AZURE_OPENAI_LLM_DEPLOYMENT_NAME,
    AZURE_OPENAI_SLM_DEPLOYMENT_NAME,
    WEATHER_API_URL,
    WEATHER_API_KEY,
    EXCHANGE_RATE_API_URL,
    EXCHANGE_RATE_API_KEY,
)

from safety.content_safety import ContentSafetyService
from routing.intent_classifier import IntentClassificationService
from services.chat_service import ChatService
from core.logging import setup_logging

logger = logging.getLogger(__name__)

def main():

    setup_logging()

    logger.info("Starting chat service.")

    config = load_config()
    logger.info("Configuration loaded.")

    openai_client = get_openai_client()
    logger.info("OpenAI client initialized.")

    content_safety_client = get_content_safety_client()
    logger.info("Content Safety client initialized.")

    tool_registry = ToolRegistry()
    logger.info("Registering tools.")

    tool_registry.register_tool(WeatherTool(
        api_url=WEATHER_API_URL, 
        api_key=WEATHER_API_KEY)
        )
    logger.info("Registered Weather Tool.")

    tool_registry.register_tool(ExchangeRateTool(
        api_url=EXCHANGE_RATE_API_URL, 
        api_key=EXCHANGE_RATE_API_KEY)
        )
    logger.info("Registered Exchange Rate Tool.")

    # setup_search_index(openai_client)

    safety_service = ContentSafetyService(
        client=content_safety_client, 
        config=config,
        )
    logger.info("Content Safety Service initialized.")

    intent_classifier = IntentClassificationService(
        openai_client=openai_client, 
        slm_deployment_name=AZURE_OPENAI_SLM_DEPLOYMENT_NAME, 
        config=config)
    logger.info("Intent Classification Service initialized.")

    support_agent = SupportAgent(
        openai_client=openai_client, 
        llm_deployment_name=AZURE_OPENAI_LLM_DEPLOYMENT_NAME, 
        config=config)
    logger.info("Support Agent initialized.")

    billing_agent = BillingAgent(
        openai_client=openai_client, 
        llm_deployment_name=AZURE_OPENAI_LLM_DEPLOYMENT_NAME, 
        config=config)
    logger.info("Billing Agent initialized.")

    simple_intent_responder = SimpleIntentResponder(
        openai_client=openai_client,
        slm_deployment_name=AZURE_OPENAI_SLM_DEPLOYMENT_NAME,
        config=config,
    )
    logger.info("Simple Intent Responder initialized.")

    # retriever = AzureSearchRetriever(
    #     ai_search_client=get_ai_search_client(),
    #     openai_client=openai_client,
    #     embedding_model_deployment_name=EMBEDDING_MODEL_DEPLOYMENT_NAME,
    # )

    chat_service = ChatService(
        content_safety_service=safety_service, 
        intent_classification_service=intent_classifier, 
        support_agent=support_agent, 
        billing_agent=billing_agent, 
        simple_intent_responder=simple_intent_responder,
        tool_registry=tool_registry,
        conversation_history=[], 
        config=config)
    logger.info("Chat Service initialized.")

    logger.info("STARTING CONVERSATION")

    print("Type 'quit', 'exit', or 'bye' to end the conversation.\n")

    user_input = input("[You] ")

    while user_input.lower() not in ["quit", "exit", "bye"]:

        response = chat_service.process_message(user_input)

        print(f"\n[ASSISTANT - {chat_service.current_agent}] {response}")

        user_input = input("\n[You] ")

    print("\n" + "=" * 50)
    print("CONVERSATION ENDED")
    print("=" * 50)
    print(f"Final agent: {chat_service.current_agent}")




if __name__ == "__main__":
    main()
