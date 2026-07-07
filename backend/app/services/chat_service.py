import logging
from prompts.prompt_builder import build_system_instruction
from tokens.token_counter import count_tokens, truncate_system_instruction
from core.settings import USER_NAME, USER_ROLE

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, safety_service, model_router, config: dict):
        self.safety_service = safety_service
        self.model_router = model_router
        self.config = config

    def chat(
        self,
        user_message_content: str,
        session_state: str | None = None,
        grounding_results: str | None = None
    ):
        system_instruction = build_system_instruction(
            user_name=USER_NAME,
            user_role=USER_ROLE,
            session_state=session_state,
            grounding_results=grounding_results
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
                "content": user_message_content
            }
        ]

        response, latency_ms, token_usage, model_name = self.model_router.route(
            user_question=user_message_content,
            messages=messages,
            config=self.config
        )

        if not self.safety_service.is_text_safe(response):
            logger.info("Blocked: Model response contains unsafe content.")
            return self.config["system_instruction"]["safe_response"]

        logger.info("Content Safety Check Passed: Model response is safe.")

        return {
            "response": response,
            "model": model_name,
            "latency_ms": latency_ms,
            "token_usage": token_usage
        }
