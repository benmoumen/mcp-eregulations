"""
Argument completion handlers for MCP tools and resources.
"""
import logging
from typing import Any, Dict, List, Optional

from mcp import types
from mcp.server.fastmcp import Context

from mcp_eregulations.utils.errors import InvalidArgumentError

logger = logging.getLogger(__name__)


async def complete_procedure_id(
    ctx: Context,
    current_value: Optional[str] = None,
    limit: int = 5
) -> List[types.Completion]:
    """
    Provide completion suggestions for procedure IDs.
    
    Args:
        ctx: The request context
        current_value: Current partial value if any
        limit: Maximum number of suggestions
        
    Returns:
        List of completion suggestions
    """
    # Get the API client from context
    client = ctx.request_context.lifespan_context.client
    index = ctx.request_context.lifespan_context.index
    
    # If we have a partial value, try to match it
    if current_value:
        try:
            # Check if it's a valid procedure ID first
            proc_id = int(current_value)
            proc = await client.get_procedure(proc_id)
            if proc:
                return [
                    types.Completion(
                        label=str(proc_id),
                        detail=proc.get("title", "Untitled Procedure"),
                        documentation=proc.get("description", "No description available")
                    )
                ]
        except ValueError:
            # If not a valid ID, try searching
            results = index.search_procedures(current_value, limit=limit)
            return [
                types.Completion(
                    label=str(result["id"]),
                    detail=result["title"],
                    documentation=f"Score: {result['score']:.2f}"
                )
                for result in results
            ]
    
    # Otherwise return recently accessed procedures
    recent = index.get_recent_procedures(limit=limit)
    return [
        types.Completion(
            label=str(proc["id"]),
            detail=proc["title"],
            documentation="Recently accessed"
        )
        for proc in recent
    ]


async def complete_step_id(
    ctx: Context,
    procedure_id: int,
    current_value: Optional[str] = None
) -> List[types.Completion]:
    """
    Provide completion suggestions for step IDs within a procedure.
    
    Args:
        ctx: The request context
        procedure_id: The ID of the procedure containing the steps
        current_value: Current partial value if any
        
    Returns:
        List of completion suggestions
    """
    # Get the API client from context
    client = ctx.request_context.lifespan_context.client
    
    # Get procedure steps
    steps = await client.get_procedure_steps(procedure_id)
    if not steps:
        return []
        
    # Filter steps if we have a partial value
    if current_value:
        try:
            step_id = int(current_value)
            steps = [s for s in steps if str(s.get("id", "")).startswith(str(step_id))]
        except ValueError:
            # If not a valid ID, try matching title/description
            current_value = current_value.lower()
            steps = [
                s for s in steps
                if current_value in s.get("title", "").lower()
                or current_value in s.get("description", "").lower()
            ]
    
    # Convert steps to completion items
    return [
        types.Completion(
            label=str(step.get("id")),
            detail=step.get("title", f"Step {step.get('id')}"),
            documentation=step.get("description", "No description available")
        )
        for step in steps
    ]


async def complete_query(
    ctx: Context,
    current_value: Optional[str] = None,
    limit: int = 5
) -> List[types.Completion]:
    """
    Provide completion suggestions for search queries.
    
    Args:
        ctx: The request context
        current_value: Current partial value if any
        limit: Maximum number of suggestions
        
    Returns:
        List of completion suggestions
    """
    # Get the index from context
    index = ctx.request_context.lifespan_context.index
    
    # If we have a partial query, suggest based on indexed content
    if current_value:
        suggestions = index.suggest_queries(current_value, limit=limit)
        return [
            types.Completion(
                label=suggestion["query"],
                detail=f"Found in {suggestion['count']} procedures",
                documentation=f"Suggestion based on {suggestion['source']}"
            )
            for suggestion in suggestions
        ]
    
    # Otherwise return popular/example queries
    return [
        types.Completion(
            label="business registration",
            detail="Find business registration procedures",
            documentation="Popular search query"
        ),
        types.Completion(
            label="import license",
            detail="Find import licensing procedures",
            documentation="Popular search query"
        ),
        types.Completion(
            label="tax registration",
            detail="Find tax registration procedures",
            documentation="Popular search query"
        )
    ]


# Completion handler mapping
COMPLETION_HANDLERS = {
    "procedure_id": complete_procedure_id,
    "step_id": complete_step_id,
    "query": complete_query
}


async def get_completions(
    ctx: Context,
    argument_type: str,
    current_value: Optional[str] = None,
    extra_args: Optional[Dict[str, Any]] = None
) -> List[types.Completion]:
    """
    Get completion suggestions for a given argument type.
    
    Args:
        ctx: The request context
        argument_type: Type of argument to complete
        current_value: Current partial value if any
        extra_args: Additional arguments that may be needed
        
    Returns:
        List of completion suggestions
        
    Raises:
        InvalidArgumentError: If the argument type is not supported
    """
    handler = COMPLETION_HANDLERS.get(argument_type)
    if not handler:
        raise InvalidArgumentError(
            "argument_type",
            f"Completion not supported for argument type: {argument_type}"
        )
    
    try:
        return await handler(ctx, current_value, **(extra_args or {}))
    except Exception as e:
        logger.error(f"Completion error for {argument_type}: {e}")
        return []