"""
Main module for the MCP eRegulations server.
"""
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

from mcp_eregulations.config.settings import settings

# Initialize FastMCP server
mcp = FastMCP(settings.MCP_SERVER_NAME)

# Constants
USER_AGENT = "eregulations-mcp-server/1.0"

if __name__ == "__main__":
    mcp.run(port=settings.MCP_SERVER_PORT)
