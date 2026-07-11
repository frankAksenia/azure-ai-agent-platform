import logging
from contextlib import AsyncExitStack
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult, Tool

logger = logging.getLogger(__name__)


class MCPClient:
    """Client connection for one remote MCP server."""

    def __init__(self, name: str, base_url: str, headers: dict[str, str] | None = None) -> None:
        self.name = name
        self.base_url = base_url
        self.headers = headers | {}

        self._exit_stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._http_client: httpx.AsyncClient | None = None

    @property
    def is_connected(self) -> bool:
        return self._session is not None

    async def connect(self) -> None:
        """Connect to the MCP server and initialize the session."""

        if self.is_connected:
            logger.warning("MCP client already connected",
                           extra={"server_name": self.name})
            return

        logger.info("Connecting to MCP server", extra={
                    "server_name": self.name, "base_url": self.base_url})

        self._exit_stack = AsyncExitStack()

        try:
            read_stream, write_stream, _ = (await self._exit_stack.enter_async_context(streamable_http_client(url=self.base_url, http_client=self._http_client,)))

            self._session = await self._exit_stack.enter_async_context(ClientSession(read_stream, write_stream))

            await self._session.initialize()

        except Exception:
            logger.exception("Failed to connect to MCP server",
                             extra={"server_name": self.name})

            await self.close()
            raise

        logger.info("Connected to MCP server",
                    extra={"server_name": self.name})

    async def list_tools(self) -> list[Tool]:
        """Return all tools exposed by this MCP server."""

        session = self._require_session()
        result = await session.list_tools()

        logger.info("Listed MCP tools", extra={
                    "server_name": self.name, "tool_count": len(result.tools)})

        return result.tools

    async def call_tool(self, tool_name: str, arguments: dict[str, Any],) -> CallToolResult:
        """Call one tool exposed by this MCP server."""

        session = self._require_session()

        logger.info("Calling MCP tool", extra={
                    "server_name": self.name, "tool_name": tool_name})

        return await session.call_tool(name=tool_name, arguments=arguments)

    async def close(self) -> None:
        """Close the MCP session and HTTP transport."""

        if self._exit_stack is not None:
            logger.info("Closing MCP connection", extra={
                        "server_name": self.name})

            await self._exit_stack.aclose()

        self._session = None
        self._exit_stack = None

    def _require_session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError(
                f"MCP client '{self.name}' is not connected. Call connect() before using it.")

        return self._session
