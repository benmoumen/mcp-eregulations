"""
Tools for searching and querying eRegulations data.
"""
import logging
from typing import List, Optional

from mcp.server.fastmcp import Context, FastMCP

from mcp_eregulations.api.detailed_client import detailed_client
from mcp_eregulations.utils.formatters import format_procedure_summary
from mcp_eregulations.utils.indexing import index

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP) -> None:
    """Register all search-related tools with the MCP server instance."""
    
    @mcp.tool()
    async def search_procedures_by_keyword(query: str, limit: int = 5, ctx: Context = None) -> str:
        """
        Search for procedures based on keywords.
        
        Args:
            query: Search terms or keywords
            limit: Maximum number of results to return (default: 5)
            ctx: The request context
            
        Returns:
            List of matching procedures with summaries
        """
        logger.debug(f"Searching procedures with keyword: {query}, limit: {limit}")
        # First check if we have indexed data
        results = index.search_procedures(query, limit)
        
        if results:
            output = f"# Search Results for '{query}'\n\n"
            
            for i, result in enumerate(results, 1):
                proc_id = result["id"]
                title = result["title"]
                
                output += f"## {i}. {title} (ID: {proc_id})\n"
                
                # Get full procedure data from index or API
                proc_data = index.get_procedure(proc_id)
                if not proc_data:
                    # If not in index, fetch from API and index it
                    proc_data = await detailed_client.get_procedure(proc_id)
                    if proc_data:
                        index.index_procedure(proc_id, proc_data)
                
                if proc_data:
                    # Add a brief summary
                    description = proc_data.get("description", "No description available")
                    output += f"{description[:200]}...\n\n"
                    output += f"To get full details, use get_procedure with ID {proc_id}\n\n"
                else:
                    output += "Details not available\n\n"
            
            return output
        else:
            # If no indexed results, try to fetch some procedures and index them
            # This is a simplified implementation for demonstration
            return (
                f"No procedures found matching '{query}'. "
                f"Please try a different search term or use get_procedure with a specific ID."
            )
    
    @mcp.tool()
    async def index_procedure_data(procedure_id: int, ctx: Context = None) -> str:
        """
        Index a procedure and its related data for faster retrieval.
        
        Args:
            procedure_id: The ID of the procedure to index
            ctx: The request context
            
        Returns:
            Status message
        """
        logger.debug(f"Indexing procedure data: {procedure_id}")
        # Fetch procedure data
        procedure_data = await detailed_client.get_procedure(procedure_id)
        if not procedure_data:
            return f"Procedure with ID {procedure_id} not found."
        
        # Index the procedure
        index.index_procedure(procedure_id, procedure_data)
        
        # Fetch and index requirements
        requirements_data = await detailed_client.get_procedure_requirements(procedure_id)
        if requirements_data:
            index.index_requirements(procedure_id, requirements_data)
        
        # Fetch and index related institutions
        # This is a simplified implementation
        # In a real implementation, we would extract institution IDs from the procedure data
        
        return f"Successfully indexed procedure with ID {procedure_id} and related data."
    
    @mcp.tool()
    async def get_indexed_procedure(procedure_id: int, ctx: Context = None) -> str:
        """
        Get a procedure from the index.
        
        Args:
            procedure_id: The ID of the procedure
            ctx: The request context
            
        Returns:
            Formatted procedure details from the index
        """
        logger.debug(f"Getting indexed procedure: {procedure_id}")
        procedure_data = index.get_procedure(procedure_id)
        
        if not procedure_data:
            # If not in index, try to fetch and index it
            procedure_data = await detailed_client.get_procedure(procedure_id)
            if procedure_data:
                index.index_procedure(procedure_id, procedure_data)
            else:
                return f"Procedure with ID {procedure_id} not found."
        
        return format_procedure_summary(procedure_data)
    
    @mcp.tool()
    async def get_indexed_requirements(procedure_id: int, ctx: Context = None) -> str:
        """
        Get requirements for a procedure from the index.
        
        Args:
            procedure_id: The ID of the procedure
            ctx: The request context
            
        Returns:
            Formatted requirements from the index
        """
        logger.debug(f"Getting indexed requirements: {procedure_id}")
        requirements_data = index.get_requirements(procedure_id)
        
        if not requirements_data:
            # If not in index, try to fetch and index it
            requirements_data = await detailed_client.get_procedure_requirements(procedure_id)
            if requirements_data:
                index.index_requirements(procedure_id, requirements_data)
            else:
                return f"Requirements for procedure with ID {procedure_id} not found."
        
        # Format the requirements data
        # This is a simplified implementation
        output = "# Procedure Requirements\n\n"
        
        # Extract requirements from the API response structure
        # This will need to be adjusted based on the actual API response format
        req_items = requirements_data.get("items", [])
        if not req_items:
            return "No specific requirements listed for this procedure."
        
        for i, req in enumerate(req_items, 1):
            name = req.get("name", f"Requirement {i}")
            description = req.get("description", "No description available")
            cost = req.get("cost", "Cost not specified")
            
            output += f"{i}. {name}\n"
            output += f"   Description: {description}\n"
            if cost:
                output += f"   Cost: {cost}\n"
            output += "\n"
        
        return output
