import json
from typing import Any

from mcp.types import CallToolResult, TextContent, Tool


class MCPToolAdapter:
    """Convert MCP tools and results into formats used by OpenAI."""

    @staticmethod
    def to_openai_tool(tool: Tool,public_name: str) -> dict[str, Any]:
        """
        Convert an MCP Tool to an OpenAI function-tool definition.

        public_name may include the server prefix, for example:
        exa__web_search_exa
        """

        return {
            "type": "function",
            "function": {
                "name": public_name,
                "description": (
                    tool.description
                    or f"Tool provided by an MCP server: {tool.name}"
                ),
                "parameters": tool.inputSchema,
            },
        }

    @staticmethod
    def format_result(result: CallToolResult) -> str:
        """
        Convert an MCP CallToolResult into text that can be sent
        back to the language model.
        """

        structured_content = getattr(result, "structuredContent", None)

        if structured_content is not None:
            return json.dumps(structured_content, ensure_ascii=False, default=str)

        text_parts: list[str] = []

        for content_item in result.content:
            if isinstance(content_item, TextContent):
                text_parts.append(content_item.text)

        if text_parts:
            formatted_text = "\n".join(text_parts)

            if result.isError:
                return f"MCP tool error: {formatted_text}"

            return formatted_text

        if result.isError:
            return "MCP tool execution failed without an error message."

        return "MCP tool completed without textual output."
