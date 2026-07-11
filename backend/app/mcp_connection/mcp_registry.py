import logging
from dataclasses import dataclass
from typing import Any

from mcp.types import Tool

from mcp_connection.client import MCPClient
from mcp_connection.tool_adapter import MCPToolAdapter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegisteredMCPTool:
    public_name: str
    original_name: str
    server_name: str
    definition: Tool
    client: MCPClient


class MCPRegistry:
    """Register MCP servers, discover tools, and execute MCP tools."""

    def __init__(self) -> None:
        self._clients: dict[str, MCPClient] = {}
        self._tools: dict[str, RegisteredMCPTool] = {}

    def register_client(self, client: MCPClient) -> None:
        """Register an MCP server client before connecting."""

        if client.name in self._clients:
            raise ValueError(
                f"MCP server '{client.name}' is already registered.")

        self._clients[client.name] = client

        logger.info("Registered MCP server", extra={
                    "server_name": client.name})

    async def connect_all(self) -> None:
        """Connect to every registered server and discover its tools."""

        for client in self._clients.values():
            try:
                await client.connect()
                await self._discover_tools(client)

            except Exception:
                logger.exception("Failed to initialize MCP server", extra={
                                 "server_name": client.name})
                raise

    async def _discover_tools(self, client: MCPClient) -> None:
        tools = await client.list_tools()

        for tool in tools:
            public_name = self._create_public_name(
                server_name=client.name, tool_name=tool.name)

            if public_name in self._tools:
                raise ValueError(
                    f"MCP tool '{public_name}' is already registered.")

            self._tools[public_name] = RegisteredMCPTool(
                public_name=public_name,
                original_name=tool.name,
                server_name=client.name,
                definition=tool,
                client=client,
            )

            logger.info("Registered MCP tool", extra={
                        "server_name": client.name, "original_tool_name": tool.name, "public_tool_name": public_name})

    def get_available_tools(self) -> list[dict[str, Any]]:
        """
        Return all registered MCP tools in OpenAI function-tool format.
        """

        return [
            MCPToolAdapter.to_openai_tool(
                tool=registered_tool.definition, public_name=registered_tool.public_name)
            for registered_tool in self._tools.values()
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """
        Execute an MCP tool using its public prefixed name.

        Example:
            exa__web_search_exa
        """

        registered_tool = self._tools.get(tool_name)

        if registered_tool is None:
            raise ValueError(f"Unknown MCP tool: '{tool_name}'")

        logger.info("Executing registered MCP tool", extra={
                    "server_name": registered_tool.server_name, "public_tool_name": tool_name, "original_tool_name": registered_tool.original_name})

        result = await registered_tool.client.call_tool(tool_name=registered_tool.original_name, arguments=arguments,)

        return MCPToolAdapter.format_result(result)

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self._tools

    def list_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    async def close_all(self) -> None:
        """Close all MCP clients in reverse registration order."""

        clients = list(self._clients.values())

        for client in reversed(clients):
            try:
                await client.close()
            except Exception:
                logger.exception("Failed to close MCP client",
                                 extra={"server_name": client.name})

        self._tools.clear()

    @staticmethod
    def _create_public_name(server_name: str, tool_name: str) -> str:
        """
        Prefix tool names to avoid collisions between MCP servers.

        Example:
            server: exa
            tool: web_search_exa
            result: exa__web_search_exa
        """

        return f"{server_name}__{tool_name}"
