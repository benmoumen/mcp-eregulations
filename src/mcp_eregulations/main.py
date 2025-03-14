"""
Main module for the MCP eRegulations server.
"""
from typing import Any
import logging
import os
import sys
import httpx
from mcp.server.fastmcp import FastMCP
from mcp_eregulations.config.settings import settings
from mcp_eregulations.api.client import client as api_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set port in environment variable so FastMCP can use it
os.environ["PORT"] = str(settings.MCP_SERVER_PORT)

# Initialize FastMCP server
logger.info(f"Initializing MCP eRegulations server with name: {settings.MCP_SERVER_NAME}")
mcp = FastMCP(settings.MCP_SERVER_NAME)

# Constants
USER_AGENT = "eregulations-mcp-server/1.0"

@mcp.tool()
async def health_check() -> dict:
    """Health check endpoint for Docker."""
    logger.debug("Health check endpoint called")
    return {"status": "healthy"}

@mcp.tool()
async def version() -> dict:
    """Get version information."""
    return {
        "service": settings.MCP_SERVER_NAME,
        "version": "1.0.0"
    }

try:
    if __name__ == "__main__":
        logger.info(f"Starting MCP eRegulations server")
        # Run the server in stdio transport mode as per documentation
        mcp.run(transport='stdio')
except Exception as e:
    logger.error(f"Server error: {str(e)}", exc_info=True)
    sys.exit(1)
