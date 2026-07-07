import logging
import time

logger = logging.getLogger(__name__)


class IntentClassifier:
    def __init__(self, client, deployment_name: str):
        self.client = client
        self.deployment_name = deployment_name

    def classify(
        self,
        user_question: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        timeout_seconds: float = 15.0,
    ) -> str:
        start_time = time.time()
        logger.info(
            "Starting intent classification: deployment=%s, question_chars=%s, max_tokens=%s, timeout_seconds=%s",
            self.deployment_name,
            len(user_question),
            max_tokens,
            timeout_seconds,
        )

        messages = [
            {
                "role": "system",
                "content": """
            Classify the user prompt as either "simple" or "complex".
            Respond with only one word: simple or complex.
            """
            },
            {
                "role": "user",
                "content": user_question
            }
        ]

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            timeout=timeout_seconds,
        )

        classification = response.choices[0].message.content.strip().lower()
        latency_ms = (time.time() - start_time) * 1000

        logger.info(
            "Intent classification completed: deployment=%s, classification=%s, latency_ms=%s",
            self.deployment_name,
            classification,
            round(latency_ms, 2),
        )

        if classification not in ["simple", "complex"]:
            logger.warning("Unexpected classification: %s", classification)
            return "complex"

        return classification
