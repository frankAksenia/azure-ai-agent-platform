from core.settings import (
    EXA_MCP_URL,
)
from mcp_connection.client import MCPClient
from mcp_connection.mcp_registry import MCPRegistry


def create_mcp_registry() -> MCPRegistry:
    registry = MCPRegistry()

    registry.register_client(
        MCPClient(name="exa", base_url=EXA_MCP_URL, headers={}))

    return registry