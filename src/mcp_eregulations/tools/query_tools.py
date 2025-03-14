"""
MCP tools for handling natural language queries about eRegulations.
"""
import logging
from typing import Any, Dict

from mcp.server.fastmcp import Context, FastMCP

from mcp_eregulations.utils.query_handling import query_handler

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP) -> None:
    """Register all query-related tools with the MCP server instance."""
    
    @mcp.tool()
    async def process_natural_language_query(query: str, ctx: Context) -> str:
        """
        Process a natural language query about eRegulations procedures.
        
        This tool analyzes the query to determine the user's intent and provides
        relevant information from the eRegulations system.
        
        Args:
            query: The natural language query about eRegulations procedures
            ctx: The request context
            
        Returns:
            Response with relevant information based on the query
        """
        logger.debug(f"Processing natural language query: {query}")
        # Process the query to determine intent and parameters
        query_result = await query_handler.process_query(query)
        
        # Get the API client from context
        api_client = ctx.request_context.lifespan_context.client
        
        # Generate a response based on the query analysis
        if query_result["confidence"] >= 0.7:
            # For high-confidence matches, use the suggested tool directly
            suggested_tool = query_result["suggested_tool"]
            parameters = query_result["parameters"]
            
            # Import other tool modules within the function to avoid circular imports
            from mcp_eregulations.tools import (
                detailed_tools,
                procedure_tools,
                search_tools,
            )
            
            # Handle each tool case differently
            if suggested_tool == "get_procedure":
                procedure_id = parameters["procedure_id"]
                procedure_data = await api_client.get_procedure(procedure_id)
                if not procedure_data:
                    return f"Procedure with ID {procedure_id} not found."
                from mcp_eregulations.utils.formatters import format_procedure_summary
                return format_procedure_summary(procedure_data)
                
            elif suggested_tool == "get_procedure_steps":
                procedure_id = parameters["procedure_id"]
                steps = await api_client.get_procedure_steps(procedure_id)
                if not steps:
                    return f"No steps found for procedure with ID {procedure_id}."
                from mcp_eregulations.utils.formatters import format_procedure_steps
                return format_procedure_steps(steps)
                
            elif suggested_tool == "get_procedure_requirements":
                procedure_id = parameters["procedure_id"]
                requirements = await api_client.get_procedure_requirements(procedure_id)
                if not requirements:
                    return f"No requirements found for procedure with ID {procedure_id}."
                from mcp_eregulations.utils.formatters import format_procedure_requirements
                return format_procedure_requirements(requirements)
                
            elif suggested_tool == "get_procedure_costs":
                procedure_id = parameters["procedure_id"]
                costs = await api_client.get_procedure_costs(procedure_id)
                if not costs:
                    return f"No cost information found for procedure with ID {procedure_id}."
                from mcp_eregulations.utils.formatters import format_procedure_costs
                return format_procedure_costs(costs)
                
            elif suggested_tool == "search_procedures_by_keyword":
                # This would be implemented with search functionality
                return f"Search for '{parameters['query']}' is not implemented in this version."
        
        # For lower confidence or unknown queries, generate a general response
        return await query_handler.generate_response(query_result)
    
    @mcp.tool()
    async def answer_procedure_question(procedure_id: int, question: str, ctx: Context) -> str:
        """
        Answer a specific question about a procedure.
        
        This tool retrieves comprehensive information about a procedure and
        attempts to answer a specific question about it.
        
        Args:
            procedure_id: The ID of the procedure
            question: The specific question about the procedure
            ctx: The request context
            
        Returns:
            Answer to the question based on procedure information
        """
        logger.debug(f"Answering question about procedure {procedure_id}: {question}")
        # Get the API client from context
        api_client = ctx.request_context.lifespan_context.client
        
        # Process the question to determine what aspect of the procedure is being asked about
        question_lower = question.lower()
        
        # Get detailed procedure information
        procedure_data = await api_client.get_procedure(procedure_id)
        if not procedure_data:
            return f"Procedure with ID {procedure_id} not found."
        
        from mcp_eregulations.utils.formatters import format_procedure_summary
        procedure_info = format_procedure_summary(procedure_data)
        
        if "step" in question_lower or "how to" in question_lower:
            # Question about steps
            steps = await api_client.get_procedure_steps(procedure_id)
            if not steps:
                return f"No steps found for procedure {procedure_id}."
            
            from mcp_eregulations.utils.formatters import format_procedure_steps
            steps_info = format_procedure_steps(steps)
            return f"Here's information about the steps for procedure {procedure_id}:\n\n{steps_info}"
            
        elif "cost" in question_lower or "fee" in question_lower or "price" in question_lower:
            # Question about costs
            costs = await api_client.get_procedure_costs(procedure_id)
            if not costs:
                return f"No cost information found for procedure {procedure_id}."
            
            from mcp_eregulations.utils.formatters import format_procedure_costs
            costs_info = format_procedure_costs(costs)
            return f"Here's information about the costs for procedure {procedure_id}:\n\n{costs_info}"
            
        elif "require" in question_lower or "document" in question_lower or "need" in question_lower:
            # Question about requirements
            requirements = await api_client.get_procedure_requirements(procedure_id)
            if not requirements:
                return f"No requirements found for procedure {procedure_id}."
            
            from mcp_eregulations.utils.formatters import format_procedure_requirements
            requirements_info = format_procedure_requirements(requirements)
            return f"Here's information about the requirements for procedure {procedure_id}:\n\n{requirements_info}"
            
        elif "time" in question_lower or "duration" in question_lower or "long" in question_lower:
            # Question about timeline
            # This is a simplified implementation
            return f"I don't have specific timeline information for procedure {procedure_id}. Please check the procedure details for any time-related information."
        
        # For general or unrecognized questions, return the detailed procedure information
        return f"Here's detailed information about procedure {procedure_id} that may answer your question:\n\n{procedure_info}"
