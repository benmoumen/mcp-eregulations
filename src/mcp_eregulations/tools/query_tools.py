"""
MCP tools for handling natural language queries about eRegulations.
"""
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from mcp_eregulations.utils.query_handling import query_handler
from mcp_eregulations.main import mcp


@mcp.tool()
async def process_natural_language_query(query: str) -> str:
    """
    Process a natural language query about eRegulations procedures.
    
    This tool analyzes the query to determine the user's intent and provides
    relevant information from the eRegulations system.
    
    Args:
        query: The natural language query about eRegulations procedures
        
    Returns:
        Response with relevant information based on the query
    """
    # Process the query to determine intent and parameters
    query_result = await query_handler.process_query(query)
    
    # Generate a response based on the query analysis
    if query_result["confidence"] >= 0.7:
        # For high-confidence matches, use the suggested tool directly
        suggested_tool = query_result["suggested_tool"]
        parameters = query_result["parameters"]
        
        if suggested_tool == "get_procedure":
            from mcp_eregulations.tools.procedure_tools import get_procedure
            return await get_procedure(parameters["procedure_id"])
            
        elif suggested_tool == "get_procedure_steps":
            from mcp_eregulations.tools.procedure_tools import get_procedure_steps
            return await get_procedure_steps(parameters["procedure_id"])
            
        elif suggested_tool == "get_procedure_requirements":
            from mcp_eregulations.tools.procedure_tools import get_procedure_requirements
            return await get_procedure_requirements(parameters["procedure_id"])
            
        elif suggested_tool == "get_procedure_costs":
            from mcp_eregulations.tools.procedure_tools import get_procedure_costs
            return await get_procedure_costs(parameters["procedure_id"])
            
        elif suggested_tool == "search_procedures_by_keyword":
            from mcp_eregulations.tools.search_tools import search_procedures_by_keyword
            return await search_procedures_by_keyword(parameters["query"], parameters.get("limit", 5))
            
        elif suggested_tool == "get_institution_info":
            from mcp_eregulations.tools.detailed_tools import get_institution_info
            return await get_institution_info(parameters["institution_id"])
    
    # For lower confidence or unknown queries, generate a general response
    return await query_handler.generate_response(query_result)


@mcp.tool()
async def answer_procedure_question(procedure_id: int, question: str) -> str:
    """
    Answer a specific question about a procedure.
    
    This tool retrieves comprehensive information about a procedure and
    attempts to answer a specific question about it.
    
    Args:
        procedure_id: The ID of the procedure
        question: The specific question about the procedure
        
    Returns:
        Answer to the question based on procedure information
    """
    # Get detailed procedure information
    from mcp_eregulations.tools.detailed_tools import get_procedure_detailed
    procedure_info = await get_procedure_detailed(procedure_id)
    
    # Process the question to determine what aspect of the procedure is being asked about
    question_lower = question.lower()
    
    if "step" in question_lower or "how to" in question_lower:
        # Question about steps
        from mcp_eregulations.tools.procedure_tools import get_procedure_steps
        steps_info = await get_procedure_steps(procedure_id)
        
        return f"Here's information about the steps for procedure {procedure_id}:\n\n{steps_info}"
        
    elif "cost" in question_lower or "fee" in question_lower or "price" in question_lower:
        # Question about costs
        from mcp_eregulations.tools.procedure_tools import get_procedure_costs
        costs_info = await get_procedure_costs(procedure_id)
        
        return f"Here's information about the costs for procedure {procedure_id}:\n\n{costs_info}"
        
    elif "require" in question_lower or "document" in question_lower or "need" in question_lower:
        # Question about requirements
        from mcp_eregulations.tools.procedure_tools import get_procedure_requirements
        requirements_info = await get_procedure_requirements(procedure_id)
        
        return f"Here's information about the requirements for procedure {procedure_id}:\n\n{requirements_info}"
        
    elif "time" in question_lower or "duration" in question_lower or "long" in question_lower:
        # Question about timeline
        # This is a simplified implementation
        return f"I don't have specific timeline information for procedure {procedure_id}. Please check the procedure details for any time-related information."
    
    # For general or unrecognized questions, return the detailed procedure information
    return f"Here's detailed information about procedure {procedure_id} that may answer your question:\n\n{procedure_info}"
