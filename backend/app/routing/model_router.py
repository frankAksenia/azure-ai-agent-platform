import asyncio
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class ModelRouter:
    def __init__(self, client: Any, intent_classifier: Any, tool_registry: Any, mcp_registry: Any, llm_deployment: str, slm_deployment: str,) -> None:
        self.client = client
        self.intent_classifier = intent_classifier
        self.tool_registry = tool_registry
        self.mcp_registry = mcp_registry
        self.llm_deployment = llm_deployment
        self.slm_deployment = slm_deployment

    async def route(self, user_question: str, messages: list[dict], config: dict,) -> tuple[str, float, dict | None, str]:
        """
        Classify the request, select a model, optionally execute tools,
        and return the final model response and metrics.
        """

        logger.info("Classifying intent for user question")

        intent = await asyncio.to_thread(self.intent_classifier.classify, user_question, config["intent_classifier"]["max_tokens"], config["intent_classifier"]
                                         ["temperature"], config["intent_classifier"]["top_p"], config["intent_classifier"].get("timeout_seconds", 15.0),)

        if intent == "simple":
            model_name = "Phi-4 (SLM)"
            deployment = self.slm_deployment
            model_config = config["slm"]

            logger.info("Routing request to SLM", extra={"model_name": model_name, "deployment": deployment,})
        else:
            model_name = "GPT-4.1-Mini (LLM)"
            deployment = self.llm_deployment
            model_config = config["llm"]

            logger.info("Routing request to LLM", extra={ "model_name": model_name, "deployment": deployment})

        messages = self._limit_message_history(messages=messages, max_past_messages=model_config["max_past_messages"])

        timeout_seconds = model_config["timeout_seconds"]
        start_time = time.perf_counter()

        logger.info("Sending chat completion request: deployment=%s, model_name=%s, message_count=%s, max_completion_tokens=%s, timeout_seconds=%s", deployment, model_name, len(messages), model_config["max_tokens"], timeout_seconds)

        if intent == "simple":
            response = await self._call_model_without_tools(
                model_deployment_name=deployment,
                messages=messages,
                max_completion_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"],
                top_p=model_config["top_p"],
                timeout_seconds=timeout_seconds,
            )
        else:
            available_tools = self.get_available_tools()

            response = await self._call_llm_with_tools(
                model_deployment_name=deployment,
                messages=messages,
                max_completion_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"],
                top_p=model_config["top_p"],
                timeout_seconds=timeout_seconds,
                tools=available_tools,
                max_tool_rounds=config["tool_calls"]["max_retries"])

        latency_ms = (time.perf_counter() - start_time) * 1000

        choice = response.choices[0]
        reply = choice.message.content

        if reply is None:
            reply = ""

        logger.info(
            "Chat completion completed: deployment=%s, model_name=%s, finish_reason=%s, reply_chars=%s, latency_ms=%s",
            deployment,
            model_name,
            getattr(choice, "finish_reason", None),
            len(reply),
            round(latency_ms, 2),
        )

        token_usage = self._extract_token_usage(response)

        return reply, latency_ms, token_usage, model_name

    def get_available_tools(self) -> list[dict]:
        """
        Combine local tools and MCP tools into one OpenAI-compatible list.
        """

        local_tools = self.tool_registry.get_available_tools()
        mcp_tools = self.mcp_registry.get_available_tools()

        available_tools = [*local_tools, *mcp_tools]

        logger.info("Collected available tools", extra={"local_tool_count": len(local_tools), "mcp_tool_count": len(mcp_tools), "total_tool_count": len(available_tools)})

        return available_tools

    async def _call_model_without_tools(self, model_deployment_name: str, messages: list[dict], max_completion_tokens: int, temperature: float, top_p: float, timeout_seconds: float,):
        """
        Make a normal model call without tool definitions.
        """

        request_kwargs = self._build_chat_completion_kwargs(
            model_deployment_name=model_deployment_name,
            messages=messages,
            max_completion_tokens=max_completion_tokens,
            temperature=temperature,
            top_p=top_p,
            timeout_seconds=timeout_seconds,
        )

        return await asyncio.to_thread(self.client.chat.completions.create, **request_kwargs)

    async def _call_llm_with_tools(
        self,
        model_deployment_name: str,
        messages: list[dict],
        max_completion_tokens: int,
        temperature: float,
        top_p: float,
        timeout_seconds: float,
        tools: list[dict],
        max_tool_rounds: int = 3,
    ):
        """
        Call the model and execute requested local or MCP tools.

        The loop allows the model to request tools more than once before
        producing its final answer.
        """

        if not tools:
            logger.info("No tools are available; making normal model call", extra={"model": model_deployment_name},)

            return await self._call_model_without_tools(
                model_deployment_name=model_deployment_name,
                messages=messages,
                max_completion_tokens=max_completion_tokens,
                temperature=temperature,
                top_p=top_p,
                timeout_seconds=timeout_seconds,
            )

        logger.info("Calling model with tools", extra={ "model": model_deployment_name, "tool_count": len(tools), "max_tool_rounds": max_tool_rounds,})

        for tool_round in range(1, max_tool_rounds + 1):
            round_start_time = time.perf_counter()

            request_kwargs = self._build_chat_completion_kwargs(
                model_deployment_name=model_deployment_name,
                messages=messages,
                max_completion_tokens=max_completion_tokens,
                temperature=temperature,
                top_p=top_p,
                timeout_seconds=timeout_seconds,
                tools=tools,
                tool_choice="auto",
            )

            response = await asyncio.to_thread(self.client.chat.completions.create, **request_kwargs)

            latency_ms = (time.perf_counter() - round_start_time) * 1000

            assistant_message = response.choices[0].message

            logger.info(
                "Model tool round completed",
                extra={
                    "model": model_deployment_name,
                    "tool_round": tool_round,
                    "finish_reason": getattr(response.choices[0], "finish_reason", None),
                    "reply_chars": len(assistant_message.content or ""),
                    "latency_ms": round(latency_ms, 2),
                },
            )

            if not assistant_message.tool_calls:
                logger.info("Model produced final response without additional tool calls", extra={"tool_round": tool_round},)

                return response

            messages.append(assistant_message)

            logger.info("Model requested tool calls", extra={"tool_round": tool_round, "tool_call_count": len(assistant_message.tool_calls)})

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name

                try:
                    tool_arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as exc:
                    logger.exception("Model returned invalid tool arguments", extra={"tool_name": tool_name, "raw_arguments": (tool_call.function.arguments)})

                    tool_result = ("Tool execution failed because the model "f"provided invalid JSON arguments: {exc}")
                else:
                    tool_result = await self._execute_tool(tool_name=tool_name, arguments=tool_arguments)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

        logger.warning("Maximum number of tool rounds reached",extra={"model": model_deployment_name, "max_tool_rounds": max_tool_rounds}        )

        # Ask for a final response without exposing tools again.
        messages.append(
            {
                "role": "system",
                "content": (
                    "Provide the final answer using the tool results "
                    "already available. Do not request another tool."
                ),
            }
        )

        return await self._call_model_without_tools(
            model_deployment_name=model_deployment_name,
            messages=messages,
            max_completion_tokens=max_completion_tokens,
            temperature=temperature,
            top_p=top_p,
            timeout_seconds=timeout_seconds,
        )

    async def _execute_tool(self, tool_name: str, arguments: dict[str, Any],) -> str:
        """
        Execute either a local tool or an MCP tool.

        No separate dispatcher is required.
        """

        logger.info("Executing tool", extra={"tool_name": tool_name, "argument_names": list(arguments.keys())})

        try:
            if self.tool_registry.has_tool(tool_name):
                # Local tools currently use synchronous requests.
                result = await asyncio.to_thread(self.tool_registry.run_tool, tool_name, arguments)

            elif self.mcp_registry.has_tool(tool_name):
                result = await self.mcp_registry.call_tool(tool_name=tool_name,arguments=arguments)

            else:
                raise ValueError(f"No registered local or MCP tool named "f"'{tool_name}'.")

        except Exception as exc:
            logger.exception("Tool execution failed", extra={"tool_name": tool_name})

            return (f"Tool '{tool_name}' failed with error: "
                f"{type(exc).__name__}: {exc}"
            )

        logger.info("Tool execution completed", extra={"tool_name": tool_name})

        if isinstance(result, str):
            return result

        return json.dumps(result,ensure_ascii=False, default=str,)

    @staticmethod
    def _build_chat_completion_kwargs(
        model_deployment_name: str,
        messages: list[dict],
        max_completion_tokens: int,
        temperature: float,
        top_p: float,
        timeout_seconds: float,
        **extra_kwargs: Any,
    ) -> dict[str, Any]:
        request_kwargs = {
            "model": model_deployment_name,
            "messages": messages,
            "max_completion_tokens": max_completion_tokens,
            "timeout": timeout_seconds,
            **extra_kwargs,
        }

        if not model_deployment_name.startswith("gpt-5"):
            request_kwargs["temperature"] = temperature
            request_kwargs["top_p"] = top_p

        return request_kwargs

    @staticmethod
    def _limit_message_history(messages: list[dict], max_past_messages: int,) -> list[dict]:
        """
        Preserve the system message while limiting conversation history.
        """

        if not messages:
            return []

        if messages[0].get("role") != "system":
            return messages[-max_past_messages:]

        system_message = messages[0]
        conversation_messages = messages[1:]

        return [system_message,*conversation_messages[-max_past_messages:],]

    @staticmethod
    def _extract_token_usage(response) -> dict | None:
        if not getattr(response, "usage", None):
            return None

        return {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
