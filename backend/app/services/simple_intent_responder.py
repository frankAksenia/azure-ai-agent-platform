import logging

logger = logging.getLogger(__name__)


class SimpleIntentResponder:
    def __init__(self, openai_client, slm_deployment_name, config: dict):
        self.openai_client = openai_client
        self.slm_deployment_name = slm_deployment_name
        self.config = config

    def respond(self, user_message: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a concise assistant. Answer briefly, clearly, and directly. "
                    "Do not use tools or ask for unnecessary details."
                ),
            },
            {"role": "user", "content": user_message},
        ]

        response = self.openai_client.responses.create(
            model=self.slm_deployment_name,
            input=messages,
            max_output_tokens=self.config["slm"]["max_tokens"],
            temperature=self.config["slm"]["temperature"],
            top_p=self.config["slm"]["top_p"],
            timeout=self.config["slm"]["timeout_seconds"],
        )
        return response.output_text
