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
        max_completion_tokens: int,
        temperature: float,
        top_p: float,
        timeout_seconds: float = 15.0,
    ) -> str:
        start_time = time.time()
        logger.info(
            "Starting intent classification: deployment=%s, question_chars=%s, max_completion_tokens=%s, timeout_seconds=%s",
            self.deployment_name,
            len(user_question),
            max_completion_tokens,
            timeout_seconds,
        )

        messages = [
            {
                "role": "user",
                "content": f"""
Classify the following user prompt as exactly one of these labels:

simple
complex

Return only the label. No greeting. No punctuation. No explanation.

simple = greeting, thanks, short factual/support question, or low-risk request.
complex = refund, complaint, account/order-specific issue, multi-step request, policy reasoning, or anything requiring grounded records.

If unsure, return complex.

User prompt:
{user_question}

Label:
"""
            }
        ]

        request_kwargs = {
            "model": self.deployment_name,
            "messages": messages,
            "max_completion_tokens": max_completion_tokens,
            "timeout": timeout_seconds,
        }

        if not self.deployment_name.startswith("gpt-5"):
            request_kwargs["temperature"] = temperature
            request_kwargs["top_p"] = top_p

        response = self.client.chat.completions.create(**request_kwargs)

        raw_classification = response.choices[0].message.content.strip().lower()
        classification = raw_classification.strip("\"'`.,:; ")
        latency_ms = (time.time() - start_time) * 1000

        logger.info(
            "Intent classification completed: deployment=%s, raw_classification=%s, parsed_classification=%s, latency_ms=%s",
            self.deployment_name,
            raw_classification,
            classification,
            round(latency_ms, 2),
        )

        if classification.startswith("simple"):
            return "simple"

        if classification.startswith("complex"):
            return "complex"

        logger.warning("Unexpected classification: %s", raw_classification)
        return "complex"
