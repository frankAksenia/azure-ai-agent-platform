import time
import logging

logger = logging.getLogger(__name__)


class ModelRouter:
    def __init__(
        self,
        client,
        intent_classifier,
        llm_deployment: str,
        slm_deployment: str
    ):
        self.client = client
        self.intent_classifier = intent_classifier
        self.llm_deployment = llm_deployment
        self.slm_deployment = slm_deployment

    def route(self, user_question: str, messages: list[dict], config: dict):
        logger.info(f"Classifying intent for user question.")

        intent = self.intent_classifier.classify(
            user_question,
            config["intent_classifier"]["max_tokens"],
            config["intent_classifier"]["temperature"],
            config["intent_classifier"]["top_p"]
        )

        if intent == "simple":
            model_name = "Phi-4 (SLM)"
            deployment = self.slm_deployment
            model_config = config["slm"]
            logger.info(f"Routing to SLM model: {model_name}.")
        else:
            model_name = "GPT-4.1-Mini (LLM)"
            deployment = self.llm_deployment
            model_config = config["llm"]
            logger.info(
                f"Routing to LLM model: {model_name}.")

        messages = messages[-model_config["max_past_messages"]:]

        start_time = time.time()

        response = self.client.chat.completions.create(
            model=deployment,
            messages=messages,
            max_tokens=model_config["max_tokens"],
            temperature=model_config["temperature"],
            top_p=model_config["top_p"]
        )

        latency_ms = (time.time() - start_time) * 1000
        reply = response.choices[0].message.content

        token_usage = None
        if hasattr(response, "usage") and response.usage:
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

        return reply, latency_ms, token_usage, model_name
