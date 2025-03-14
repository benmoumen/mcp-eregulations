"""
Main module for the MCP eRegulations server.
This module sets up the FastMCP server with proper lifecycle management and typed context.
"""
import logging
import sys
import argparse
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Optional, List

import httpx
from mcp import types
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ServerCapabilities

from mcp_eregulations.api.client import ERegulationsClient
from mcp_eregulations.api.detailed_client import DetailedERegulationsClient
from mcp_eregulations.config.settings import settings
from mcp_eregulations.tools import (
    auth_tools,
    detailed_tools,
    procedure_tools,
    query_tools,
    search_tools,
)
from mcp_eregulations.utils import indexing, subscriptions
from mcp_eregulations.utils.errors import MCPError

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.MCP_LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with initialized resources for lifespan management."""
    client: ERegulationsClient
    detailed_client: DetailedERegulationsClient
    index: indexing.SearchIndex


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Manage application lifecycle with type-safe context.
    This ensures proper startup and shutdown of resources.
    """
    logger.info("Starting MCP eRegulations server lifespan")
    
    # Initialize API clients
    client = ERegulationsClient()
    detailed_client = DetailedERegulationsClient()
    
    # Initialize HTTP clients
    await client.init()
    await detailed_client.init()
    
    # Initialize search index
    index = indexing.SearchIndex()
    await index.init()
    
    # Initialize the application context
    app_context = AppContext(
        client=client,
        detailed_client=detailed_client,
        index=index
    )
    
    try:
        yield app_context
    finally:
        # Perform cleanup when shutting down
        logger.info("Shutting down MCP eRegulations server")
        await client.close()
        await detailed_client.close()
        await index.close()


# Define server capabilities
capabilities = ServerCapabilities(
    prompts=types.PromptsCapability(
        listChanged=True  # Support for prompt list updates
    ),
    resources=types.ResourcesCapability(
        subscribe=True,  # Support for resource subscriptions
        listChanged=True  # Support for resource list updates
    ),
    tools=types.ToolsCapability(
        listChanged=True  # Support for tool list updates
    ),
    logging=types.LoggingCapability(
        levels=["debug", "info", "warning", "error"]  # Supported log levels
    ),
    experimental={}  # No experimental features yet
)

# Initialize FastMCP server with capabilities and dependencies
logger.info(f"Initializing MCP eRegulations server with name: {settings.MCP_SERVER_NAME}")
mcp = FastMCP(
    settings.MCP_SERVER_NAME,
    lifespan=app_lifespan,
    capabilities=capabilities,
    dependencies=[
        "httpx",
        "pydantic",
        "pydantic-settings",
        "aiohttp",
        "aiofiles",
    ]
)


# --- Core Server Tools ---

@mcp.tool()
async def health_check(ctx: Context) -> dict:
    """Health check endpoint."""
    logger.debug("Health check endpoint called")
    return {
        "status": "healthy",
        "api_url": settings.EREGULATIONS_API_URL,
        "api_version": settings.EREGULATIONS_API_VERSION
    }


@mcp.tool()
async def version(ctx: Context) -> dict:
    """Get version information."""
    return {
        "service": settings.MCP_SERVER_NAME,
        "version": "1.0.0",
        "api_url": settings.EREGULATIONS_API_URL,
        "api_version": settings.EREGULATIONS_API_VERSION
    }


# --- API Resources ---

@mcp.resource("eregulations://procedure/{procedure_id}")
async def get_procedure(procedure_id: str, ctx: Context) -> str:
    """
    Get detailed information about a specific procedure.
    
    Args:
        procedure_id: The ID of the procedure to fetch
        ctx: The request context containing the lifespan context
        
    Returns:
        Formatted procedure details as text
    """
    # Access the API client from the lifespan context
    detailed_client = ctx.request_context.lifespan_context.detailed_client
    
    # Convert string ID to integer
    try:
        proc_id = int(procedure_id)
    except ValueError:
        return f"Invalid procedure ID: {procedure_id}. Must be an integer."
    
    # Fetch detailed procedure data
    result = await detailed_client.get_procedure_detailed(proc_id)
    
    if "error" in result:
        return result["error"]
    
    # Format the result as text
    output = "# Detailed Procedure Information\n\n"
    
    # Basic information
    if "basic_info" in result and result["basic_info"]:
        output += "## Basic Information\n\n"
        basic_info = result["basic_info"]
        title = basic_info.get("title", "No title available")
        description = basic_info.get("description", "No description available")
        output += f"### {title}\n\n{description}\n\n"
    
    # Resume information
    if "resume" in result and result["resume"]:
        output += "## Procedure Resume\n\n"
        resume = result["resume"]
        resume_text = resume.get("text", "No resume available")
        output += f"{resume_text}\n\n"
    
    # Costs
    if "costs" in result and result["costs"]:
        output += "## Costs\n\n"
        costs = result["costs"]
        total = costs.get("total", "Not specified")
        output += f"Total Cost: {total}\n\n"
        
        if "items" in costs:
            output += "### Cost Breakdown:\n\n"
            for item in costs["items"]:
                name = item.get("name", "Unnamed cost")
                amount = item.get("amount", "Amount not specified")
                output += f"- {name}: {amount}\n"
            output += "\n"
    
    return output


# --- Register Tool Modules ---

# Register all tools from modules
auth_tools.register_tools(mcp)
detailed_tools.register_tools(mcp)
procedure_tools.register_tools(mcp)
query_tools.register_tools(mcp)
search_tools.register_tools(mcp)

# Register subscription handlers
subscriptions.register_subscription_handlers(mcp)


# --- Prompts ---

@mcp.prompt()
def search_eregulations(query: str) -> str:
    """Create a prompt to search eRegulations data."""
    return f"""Please search the eRegulations database for information about: {query}

You can use the following tools:
- search_procedures_by_keyword to find relevant procedures
- get_procedure to get details about a specific procedure
- get_procedure_steps to see the steps involved
- get_procedure_requirements to view requirements
- get_procedure_costs to check associated costs"""


@mcp.prompt()
def analyze_procedure(procedure_id: int) -> str:
    """Create a prompt to analyze a specific procedure."""
    return f"""Please analyze procedure {procedure_id} and provide a comprehensive breakdown.

You can use these tools to gather information:
1. get_procedure to get basic details
2. get_procedure_steps to understand the process
3. get_procedure_requirements to check requirements
4. get_procedure_costs to analyze costs
5. get_procedure_abc_analysis for Activity-Based Costing details"""


@mcp.prompt()
def compare_procedures(procedure_ids: list[int]) -> str:
    """Create a prompt to compare multiple procedures."""
    procedures_list = ", ".join(map(str, procedure_ids))
    return f"""Please compare the following procedures: {procedures_list}

For each procedure:
1. Get basic details with get_procedure
2. Check requirements with get_procedure_requirements
3. Compare costs with get_procedure_costs
4. Analyze steps with get_procedure_steps

Then provide a comparison focusing on:
- Overall complexity (number of steps)
- Total costs
- Key requirements
- Estimated time to complete"""


@mcp.prompt()
def debug_error(error: str) -> list[types.Message]:
    """Create a prompt to help debug API errors."""
    return [
        types.UserMessage("I'm seeing this error when using the eRegulations API:"),
        types.UserMessage(error),
        types.AssistantMessage("I'll help debug that. First, let's check:"),
        types.UserMessage("1. Is the API endpoint available? (Use health_check tool)"),
        types.UserMessage("2. Do you have proper authentication? (Check auth_tools)"),
        types.UserMessage("3. Is the requested resource valid? (Check API documentation)")
    ]


# Parse command line arguments
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='MCP eRegulations Server')
    parser.add_argument('--api-url', 
                      help='eRegulations API base URL',
                      default=None)
    parser.add_argument('--api-version',
                      help='eRegulations API version (default: v1)',
                      default=None)
    parser.add_argument('--port',
                      type=int,
                      help='Server port (default: 8000)',
                      default=None)
    return parser.parse_args()


# Server entry point
if __name__ == "__main__":
    try:
        # Parse command line arguments and update settings
        args = parse_args()
        
        # Override settings with command line arguments if provided
        if args.api_url:
            settings.EREGULATIONS_API_URL = args.api_url
            logger.info(f"Using custom API URL: {settings.EREGULATIONS_API_URL}")
            
        if args.api_version:
            settings.EREGULATIONS_API_VERSION = args.api_version
            logger.info(f"Using custom API version: {settings.EREGULATIONS_API_VERSION}")
            
        if args.port:
            settings.MCP_SERVER_PORT = args.port
            logger.info(f"Using custom server port: {settings.MCP_SERVER_PORT}")
        
        logger.info(f"Starting MCP eRegulations server on port {settings.MCP_SERVER_PORT}")
        # Run the server with auto-detected transport (stdio or SSE)
        mcp.run()
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)
