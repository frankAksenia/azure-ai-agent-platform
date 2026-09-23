import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register_tool(self, tool):
        if tool.name in self.tools:
             logger.warning(f"Tool with name {tool.name} is already registered.")
        self.tools[tool.name] = tool

    def get_available_tools(self) -> list[dict]:
        available_tools = []
        for tool in self.tools.values():
            parameters = tool.parameters.get("function", {}).get("parameters", {})
            available_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": parameters,
                    },
                }
            )
        return available_tools

    def run_tool(self, tool_name: str, arguments: dict):
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        return self.tools[tool_name].run(**arguments)
