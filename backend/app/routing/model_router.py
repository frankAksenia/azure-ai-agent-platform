import json
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

    def route(self, user_question: str, messages: list[dict], tools: list[dict], config: dict):
        logger.info("Classifying intent for user question.")

        intent = self.intent_classifier.classify(
            user_question,
            config["intent_classifier"]["max_tokens"],
            config["intent_classifier"]["temperature"],
            config["intent_classifier"]["top_p"],
            config["intent_classifier"].get("timeout_seconds", 15.0)
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

        timeout_seconds = model_config.get("timeout_seconds", 30.0)
        start_time = time.time()

        logger.info(
            "Sending chat completion request: deployment=%s, model_name=%s, message_count=%s, max_tokens=%s, timeout_seconds=%s",
            deployment,
            model_name,
            len(messages),
            model_config["max_tokens"],
            timeout_seconds,
        )

        if intent == "simple":
            response = self.client.chat.completions.create(
                model=deployment,
                messages=messages,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"],
                top_p=model_config["top_p"],
                timeout=timeout_seconds,
            )
        else:
            response = self._call_llm_with_tools(
                model_deployment_name=deployment,
                messages=messages,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"],
                top_p=model_config["top_p"],
                tools=tools,
            )

        latency_ms = (time.time() - start_time) * 1000
        reply = response.choices[0].message.content

        logger.info(
            "Chat completion completed: deployment=%s, model_name=%s, latency_ms=%s",
            deployment,
            model_name,
            round(latency_ms, 2),
        )

        token_usage = None
        if hasattr(response, "usage") and response.usage:
            token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }

        return reply, latency_ms, token_usage, model_name

    def _call_llm_with_tools(
        self,
        model_deployment_name: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
        top_p: float,
        tools: list[dict],
    ):
        logger.info("Calling model with tools", extra={
                    "model": model_deployment_name, "tool_count": len(tools)},)

        start_time = time.time()

        response = self.openai_client.chat.completions.create(
            model=model_deployment_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            tools=tools,
            tool_choice="auto",  # optional, can be "auto" or "manual"
        )

        latency_ms = (time.time() - start_time) * 1000
        reply = response.choices[0].message

        logger.info("Model call completed", extra={
                    "model": model_deployment_name, "latency_ms": latency_ms},)

        if not reply.tool_calls:
            logger.info("Model responded without tool calls")
            return response

        logger.info("Model requested tool calls", extra={
                    "tool_call_count": len(reply.tool_calls)},)

        messages.append(reply)

        for tool_call in reply.tool_calls:
            tool_name = tool_call.function.name
            tool_arguments = json.loads(tool_call.function.arguments)

            tool_result = self.tool_registry.run_tool(
                tool_name=tool_name,
                arguments=tool_arguments,
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result),
                }
            )

            logger.info("Tool executed", extra={"tool_name": tool_name})

        final_response = self.openai_client.chat.completions.create(
            model=model_deployment_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        logger.info("Model generated final answer after tool execution")

        return final_response
