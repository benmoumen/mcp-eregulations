"""
MCP tools for interacting with eRegulations data.
"""
import logging
from typing import List, Optional

from mcp.server.fastmcp import Context, FastMCP

from mcp_eregulations.api.client import client
from mcp_eregulations.utils.formatters import (
    extract_procedure_id_from_url,
    format_procedure_costs,
    format_procedure_requirements,
    format_procedure_steps,
    format_procedure_summary,
)

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP) -> None:
    """Register all procedure tools with the MCP server instance."""
    
    @mcp.tool()
    async def get_procedure(procedure_id: int, ctx: Context) -> str:
        """
        Get detailed information about a specific procedure.
        
        Args:
            procedure_id: The ID of the procedure to retrieve
            ctx: The request context
            
        Returns:
            Formatted procedure details
        """
        logger.debug(f"Getting procedure: {procedure_id}")
        api_client = ctx.request_context.lifespan_context.client
        procedure_data = await api_client.get_procedure(procedure_id)
        
        if not procedure_data:
            return f"Procedure with ID {procedure_id} not found."
        
        return format_procedure_summary(procedure_data)
    
    @mcp.tool()
    async def search_procedures(query: str, limit: int = 5) -> str:
        """
        Search for procedures based on keywords or criteria.
        
        Args:
            query: Search terms or keywords
            limit: Maximum number of results to return (default: 5)
            
        Returns:
            List of matching procedures with summaries
        """
        logger.debug(f"Searching procedures with query: {query}, limit: {limit}")
        # Note: This is a placeholder implementation
        # In a production environment, this would connect to a search endpoint
        # or implement a local search mechanism
        
        # For now, we'll return a message about the limitation
        return (
            f"Search for '{query}' is not implemented in this version. "
            f"Please use get_procedure with a specific procedure ID instead."
        )
    
    @mcp.tool()
    async def get_procedure_steps(procedure_id: int, ctx: Context) -> str:
        """
        Get the steps involved in a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            ctx: The request context
            
        Returns:
            Ordered list of steps with details
        """
        logger.debug(f"Getting procedure steps: {procedure_id}")
        api_client = ctx.request_context.lifespan_context.client
        steps = await api_client.get_procedure_steps(procedure_id)
        
        if not steps:
            return f"No steps found for procedure with ID {procedure_id}."
        
        return format_procedure_steps(steps)
    
    @mcp.tool()
    async def get_procedure_requirements(procedure_id: int, ctx: Context) -> str:
        """
        Get the requirements for a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            ctx: The request context
            
        Returns:
            List of requirements with details
        """
        logger.debug(f"Getting procedure requirements: {procedure_id}")
        api_client = ctx.request_context.lifespan_context.client
        requirements = await api_client.get_procedure_requirements(procedure_id)
        
        if not requirements:
            return f"No requirements found for procedure with ID {procedure_id}."
        
        return format_procedure_requirements(requirements)
    
    @mcp.tool()
    async def get_procedure_costs(procedure_id: int, ctx: Context) -> str:
        """
        Get the costs associated with a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            ctx: The request context
            
        Returns:
            Breakdown of costs
        """
        logger.debug(f"Getting procedure costs: {procedure_id}")
        api_client = ctx.request_context.lifespan_context.client
        costs = await api_client.get_procedure_costs(procedure_id)
        
        if not costs:
            return f"No cost information found for procedure with ID {procedure_id}."
        
        return format_procedure_costs(costs)
    
    @mcp.tool()
    async def get_procedure_from_url(url: str, ctx: Context) -> str:
        """
        Get procedure information from a URL.
        
        Args:
            url: URL of the procedure page
            ctx: The request context
            
        Returns:
            Formatted procedure details
        """
        procedure_id = extract_procedure_id_from_url(url)
        
        if not procedure_id:
            return f"Could not extract procedure ID from URL: {url}"
        
        return await get_procedure(procedure_id, ctx)
