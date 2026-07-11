import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register_tool(self, tool):
        if tool.name in self.tools:
            logger.warning(
                f"Tool with name {tool.name} is already registered.")
        self.tools[tool.name] = tool

    def get_available_tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            }
            for tool in self.tools.values()
        ]

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self.tools

    def list_tool_names(self) -> list[str]:
        return list(self.tools.keys())

    def run_tool(self, tool_name: str, arguments: dict):
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        return self.tools[tool_name].run(**arguments)
