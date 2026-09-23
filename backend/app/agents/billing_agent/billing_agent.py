import json

from backend.app.agents.billing_agent.billing_agent_prompt import build_system_prompt


class BillingAgent:
    def __init__(self, openai_client, llm_deployment_name: str, config: dict):
        self.openai_client = openai_client
        self.llm_deployment_name = llm_deployment_name
        self.max_tokens = config["llm"]["max_tokens"]
        self.temperature = config["llm"]["temperature"]
        self.top_p = config["llm"]["top_p"]

    def get_system_prompt(self, include_tool_rules: bool = True, include_handoff_rules: bool = True, additional_instructions: list[str] | None = None) -> str:
        return build_system_prompt(
            include_tool_rules=include_tool_rules,
            include_handoff_rules=include_handoff_rules,
            additional_instructions=additional_instructions
        )

    def get_handoff_tool(self):
        return {
            "type": "function",
            "function": {
                "name": "handoff_to_support",
                "description": "Transfer the conversation to the Support Agent.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why the conversation needs the support agent.",
                        }
                    },
                    "required": ["reason"],
                },
            },
        }

    def process_message(self, user_message: str, session_state: str | None = None):
        history_messages = []
        if session_state:
            try:
                session_data = json.loads(session_state)
                history_messages = session_data.get("messages", [])
            except (TypeError, ValueError):
                history_messages = []

        system_prompt = self.get_system_prompt()
        messages = [{"role": "system", "content": system_prompt}] + history_messages + [{"role": "user", "content": user_message}]

        response = self.openai_client.chat.completions.create(
            model=self.llm_deployment_name,
            messages=messages,
            tools=[self.get_handoff_tool()],
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                if tool_call.function.name == "handoff_to_support":
                    arguments = json.loads(tool_call.function.arguments)
                    reason = arguments["reason"]
                    updated_history = history_messages + [
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": f"Transferring you to support because {reason}"},
                    ]
                    return None, {
                        "handoff_to": "SupportAgent",
                        "reason": reason,
                        "conversation_history": updated_history,
                    }

        return assistant_message.content, None
       