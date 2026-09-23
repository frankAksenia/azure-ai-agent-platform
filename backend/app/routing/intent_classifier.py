import logging

logger = logging.getLogger(__name__)


class IntentClassificationService:
    def __init__(self, openai_client, slm_deployment_name, config: dict):
        self.client = openai_client
        self.slm_deployment_name = slm_deployment_name
        self.config = config

    def classify_intent(self, user_message: str) -> str:
        logger.info("Starting intent classification")

        messages = self._get_classification_prompt(user_message)

        response = self.client.responses.create(
            model=self.slm_deployment_name,
            input=messages,
            max_output_tokens=self.config["slm"]["max_tokens"],
            temperature=self.config["slm"]["temperature"],
            top_p=self.config["slm"]["top_p"],
            timeout=self.config["slm"]["timeout_seconds"],
        )
        raw_classification = getattr(response, "output_text", "").strip().lower()

        classification = raw_classification.strip("\"'`.,:; \n\r\t")

        logger.info(
            "Intent classification completed: raw_classification=%s, parsed_classification=%s",
            raw_classification,
            classification,
        )

        if classification.startswith("simple"):
            return "simple"

        if classification.startswith("complex"):
            return "complex"

        logger.warning("Unexpected classification: %s", raw_classification)
        return "complex"

    def _get_classification_prompt(self, user_message: str) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": """
                You are an intent classifier.

                Classify each user request into exactly one category: simple or complex.

                simple:
                - Greetings, thanks, or casual conversation.
                - Simple questions answerable directly from general knowledge.
                - Short, low-risk requests that do not require tools, external data,
                user-specific data, or multi-step reasoning.

                complex:
                - Requires a tool or external service.
                - Requires current, real-time, or user-specific information.
                - Refunds, billing, payments, complaints, account issues, or order issues.
                - Requires company policies, internal records, or grounded information.
                - Requires multiple steps or substantial reasoning.
                - Requires performing an action.

                Rules:
                - Return exactly one word: simple or complex.
                - Do not provide an explanation.
                - Do not include punctuation or additional text.
                - If a tool might be required, return complex.
                - If uncertain, return complex.
                """,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]
