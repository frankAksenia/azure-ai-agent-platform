from backend.app.agents.support_agent.support_agent_prompt import build_system_prompt


class SupportAgent:
    def __init__(self, openai_client, llm_deployment_name: str, available_tools: list[dict] | None = None, config: dict | None = None):
        self.openai_client = openai_client
        self.llm_deployment_name = llm_deployment_name
        self.available_tools = available_tools or None
        self.max_tokens = config["llm"]["max_tokens"] 
        self.temperature = config["llm"]["temperature"]
        self.top_p = config["llm"]["top_p"]

    def get_system_prompt(self, include_tool_rules: bool = True, include_handoff_rules: bool = True, additional_instructions: list[str] | None = None) -> str:
        return build_system_prompt(
            include_tool_rules=include_tool_rules,
            include_handoff_rules=include_handoff_rules,
            additional_instructions=additional_instructions
        )

    def process_message(self, user_message: str, session_state: str | None = None) -> str:
        system_prompt = self.get_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        response = self.openai_client.chat(
            deployment_name=self.llm_deployment_name,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p
        )

        return response    
       