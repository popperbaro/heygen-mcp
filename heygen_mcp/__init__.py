"""HeyGen MCP - API client and MCP server for HeyGen API interaction."""

__version__ = "0.0.3"

from heygen_mcp.api_client import HeyGenApiClient
from heygen_mcp.server import main, mcp

__all__ = ["HeyGenApiClient", "mcp", "main"]
