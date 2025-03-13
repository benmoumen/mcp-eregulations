"""
Utility functions for formatting and processing eRegulations data.
"""
from typing import Any, Dict, List, Optional


def format_procedure_summary(procedure: Dict[str, Any]) -> str:
    """
    Format a procedure into a human-readable summary.
    
    Args:
        procedure: The procedure data
        
    Returns:
        A formatted string with procedure summary
    """
    if not procedure:
        return "Procedure information not available."
    
    title = procedure.get("title", "Untitled Procedure")
    url = procedure.get("url", "No URL available")
    additional_info = procedure.get("additionalInfo", "No additional information available")
    
    summary = f"Procedure: {title}\n"
    summary += f"URL: {url}\n"
    summary += f"Additional Information: {additional_info}\n"
    
    # Add block and step count if available
    blocks = procedure.get("blocks", [])
    step_count = sum(len(block.get("steps", [])) for block in blocks)
    summary += f"Number of blocks: {len(blocks)}\n"
    summary += f"Total steps: {step_count}\n"
    
    return summary


def format_procedure_steps(steps: List[Dict[str, Any]]) -> str:
    """
    Format procedure steps into a human-readable list.
    
    Args:
        steps: List of procedure steps
        
    Returns:
        A formatted string with procedure steps
    """
    if not steps:
        return "No steps available for this procedure."
    
    result = "Procedure Steps:\n\n"
    
    for i, step in enumerate(steps, 1):
        title = step.get("title", f"Step {i}")
        description = step.get("description", "No description available")
        
        result += f"Step {i}: {title}\n"
        result += f"Description: {description}\n"
        
        # Add online information if available
        online = step.get("online", {})
        if online:
            online_url = online.get("url")
            if online_url:
                result += f"Online: {online_url}\n"
        
        result += "\n"
    
    return result


def format_procedure_requirements(requirements: Dict[str, Any]) -> str:
    """
    Format procedure requirements into a human-readable list.
    
    Args:
        requirements: The requirements data
        
    Returns:
        A formatted string with procedure requirements
    """
    if not requirements:
        return "No requirements information available for this procedure."
    
    result = "Procedure Requirements:\n\n"
    
    # Extract requirements from the API response structure
    # This will need to be adjusted based on the actual API response format
    req_items = requirements.get("items", [])
    if not req_items:
        return "No specific requirements listed for this procedure."
    
    for i, req in enumerate(req_items, 1):
        name = req.get("name", f"Requirement {i}")
        description = req.get("description", "No description available")
        cost = req.get("cost", "Cost not specified")
        
        result += f"{i}. {name}\n"
        result += f"   Description: {description}\n"
        if cost:
            result += f"   Cost: {cost}\n"
        result += "\n"
    
    return result


def format_procedure_costs(costs: Dict[str, Any]) -> str:
    """
    Format procedure costs into a human-readable summary.
    
    Args:
        costs: The costs data
        
    Returns:
        A formatted string with procedure costs
    """
    if not costs:
        return "No cost information available for this procedure."
    
    result = "Procedure Costs:\n\n"
    
    # Extract cost information from the API response structure
    # This will need to be adjusted based on the actual API response format
    total_cost = costs.get("totalCost", "Not specified")
    currency = costs.get("currency", "")
    
    result += f"Total Cost: {total_cost} {currency}\n\n"
    
    # Add breakdown if available
    cost_items = costs.get("items", [])
    if cost_items:
        result += "Cost Breakdown:\n"
        for i, item in enumerate(cost_items, 1):
            name = item.get("name", f"Item {i}")
            amount = item.get("amount", "Amount not specified")
            
            result += f"{i}. {name}: {amount} {currency}\n"
    
    return result


def extract_procedure_id_from_url(url: str) -> Optional[int]:
    """
    Extract procedure ID from a URL.
    
    Args:
        url: The URL that might contain a procedure ID
        
    Returns:
        The procedure ID as an integer, or None if not found
    """
    # This is a simple implementation that assumes URLs like "/procedure/123"
    # Adjust based on actual URL patterns in the eRegulations platform
    try:
        parts = url.strip("/").split("/")
        for i, part in enumerate(parts):
            if part.lower() == "procedure" or part.lower() == "procedures":
                if i + 1 < len(parts) and parts[i + 1].isdigit():
                    return int(parts[i + 1])
        return None
    except Exception:
        return None
