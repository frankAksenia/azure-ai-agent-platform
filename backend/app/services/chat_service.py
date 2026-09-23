import json
import logging
<<<<<<< HEAD
from tools.tool_registry import ToolRegistry
from tokens.token_counter import count_tokens, truncate_system_instruction
from core.settings import USER_NAME, USER_ROLE
=======
>>>>>>> ec49f2d (Fix handoff workflow.)

logger = logging.getLogger(__name__)


class ChatService:
<<<<<<< HEAD
    def __init__(self, safety_service, model_router, config: dict):
        self.safety_service = safety_service
        self.model_router = model_router
        self.config = config

    def chat(
=======
    def __init__(
>>>>>>> ec49f2d (Fix handoff workflow.)
        self,
        content_safety_service,
        intent_classification_service,
        support_agent,
        billing_agent,
        simple_intent_responder,
        tool_registry,
        conversation_history,
        config,
    ):
<<<<<<< HEAD
        logger.info("Starting chat session", extra={
                    "session_state": session_state})
=======
        self.content_safety_service = content_safety_service
        self.intent_classifier = intent_classification_service
        self.support_agent = support_agent
        self.billing_agent = billing_agent
        self.tool_registry = tool_registry
        self.simple_intent_responder = simple_intent_responder
        self.conversation_history = conversation_history if conversation_history is not None else []
        self.current_agent = "SupportAgent"
        self.config = config 
>>>>>>> ec49f2d (Fix handoff workflow.)

    def _generate_session_state(self) -> str:
        if not self.conversation_history:
            return json.dumps({"messages": []})
        return json.dumps({"messages": self.conversation_history})

<<<<<<< HEAD
        tools = ToolRegistry().get_available_tools()

        logger.info("Available tools:", extra={"tools": tools})

        system_instruction = build_system_instruction(
            user_name=USER_NAME,
            user_role=USER_ROLE,
            session_state=session_state,
            grounding_results=None  # grounding_results
        )

        token_count = count_tokens(system_instruction)

        if token_count > self.config["system_instruction"]["max_tokens"]:
            logger.info(
                f"System instruction exceeds max token limit of {self.config['system_instruction']['max_tokens']}. Truncating...")
            system_instruction, token_count = truncate_system_instruction(
                system_instruction
            )

        if not self.safety_service.is_text_safe(user_message_content):
            logger.info("Blocked: User message contains unsafe content.")
            return self.config["system_instruction"]["safe_response"]

        logger.info("Content Safety Check Passed: User message is safe.")

        messages = [
            {
                "role": "system",
                "content": system_instruction
            },
            {
                "role": "user",
                "content": user_message
            }
=======
    def _looks_like_billing_request(self, user_message: str) -> bool:
        lower = user_message.lower()
        billing_keywords = [
            "refund",
            "charge",
            "charged",
            "billing",
            "invoice",
            "payment",
            "receipt",
            "credit card",
            "debit card",
            "subscription",
            "cancel plan",
            "billing issue",
            "payment method",
>>>>>>> ec49f2d (Fix handoff workflow.)
        ]
        return any(keyword in lower for keyword in billing_keywords)

    def _generate_simple_response(self, user_message: str) -> str:
        if self.simple_intent_responder is None:
            return "I can help with that."
        return self.simple_intent_responder.respond(user_message)

    def process_message(self, user_message: str):
        logger.info("Starting chat session")

        if not self.content_safety_service.is_text_safe(user_message):
            logger.info("Blocked: User input contains unsafe content.")
            return self.config["content_safety"]["safe_response"]

        logger.info("Classify intent for user message.")
        classification = self.intent_classifier.classify_intent(user_message)

        if classification == "simple":
            self.current_agent = "SLMFallbackAgent"
            response = self._generate_simple_response(user_message)
        else:
            self.current_agent = "SupportAgent"
            session_state = self._generate_session_state()
            support_result = self.support_agent.process_message(user_message, session_state=session_state)

            if isinstance(support_result, tuple):
                response, handoff = support_result
            else:
                response, handoff = support_result, None

            if handoff and handoff.get("handoff_to") == "BillingAgent":
                self.current_agent = "BillingAgent"
                billing_result = self.billing_agent.process_message(user_message, session_state=session_state)
                if isinstance(billing_result, tuple):
                    response, _ = billing_result
                else:
                    response = billing_result
            elif self._looks_like_billing_request(user_message):
                self.current_agent = "BillingAgent"
                billing_result = self.billing_agent.process_message(user_message, session_state=session_state)
                if isinstance(billing_result, tuple):
                    response, _ = billing_result
                else:
                    response = billing_result

        if response is None:
            response = self.config["content_safety"]["safe_response"]

        if not self.content_safety_service.is_text_safe(response):
            logger.info("Blocked: Model response contains unsafe content.")
            return self.config["content_safety"]["safe_response"]

        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response})

        logger.info("Content Safety Check Passed: User input and model response are safe.")
        return response