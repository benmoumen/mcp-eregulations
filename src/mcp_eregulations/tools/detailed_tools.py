"""
Extended MCP tools for interacting with detailed eRegulations data.
"""
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP

from mcp_eregulations.api.detailed_client import detailed_client
from mcp_eregulations.utils.formatters import (
    format_procedure_summary,
    format_procedure_steps,
    format_procedure_requirements,
    format_procedure_costs
)
from mcp_eregulations.main import mcp


@mcp.tool()
async def get_procedure_detailed(procedure_id: int) -> str:
    """
    Get comprehensive information about a procedure by combining multiple API calls.
    
    Args:
        procedure_id: The ID of the procedure
        
    Returns:
        Comprehensive formatted procedure information
    """
    result = await detailed_client.get_procedure_detailed(procedure_id)
    
    if "error" in result:
        return result["error"]
    
    # Format the combined information
    output = "# Detailed Procedure Information\n\n"
    
    # Basic information
    if "basic_info" in result and result["basic_info"]:
        output += "## Basic Information\n\n"
        output += format_procedure_summary(result["basic_info"]) + "\n\n"
    
    # Resume information
    if "resume" in result and result["resume"]:
        output += "## Procedure Resume\n\n"
        title = result["resume"].get("title", "No title available")
        description = result["resume"].get("description", "No description available")
        output += f"Title: {title}\n"
        output += f"Description: {description}\n\n"
    
    # Cost information
    if "costs" in result and result["costs"]:
        output += "## Costs\n\n"
        output += format_procedure_costs(result["costs"]) + "\n\n"
    
    # Requirements information
    if "requirements" in result and result["requirements"]:
        output += "## Requirements\n\n"
        output += format_procedure_requirements(result["requirements"]) + "\n\n"
    
    return output


@mcp.tool()
async def get_procedure_abc_analysis(procedure_id: int) -> str:
    """
    Get the Activity-Based Costing (ABC) analysis for a procedure.
    
    Args:
        procedure_id: The ID of the procedure
        
    Returns:
        Formatted ABC analysis
    """
    abc_data = await detailed_client.get_procedure_abc(procedure_id)
    
    if not abc_data:
        return f"ABC analysis not available for procedure with ID {procedure_id}."
    
    # Format the ABC data
    output = "# Activity-Based Costing (ABC) Analysis\n\n"
    
    # This formatting will need to be adjusted based on the actual structure of ABC data
    if "summary" in abc_data:
        output += "## Summary\n\n"
        output += f"{abc_data['summary']}\n\n"
    
    if "details" in abc_data:
        output += "## Details\n\n"
        for item in abc_data["details"]:
            name = item.get("name", "Unnamed item")
            cost = item.get("cost", "Cost not specified")
            output += f"- {name}: {cost}\n"
    
    return output


@mcp.tool()
async def get_step_details(procedure_id: int, step_id: int) -> str:
    """
    Get detailed information about a specific step in a procedure.
    
    Args:
        procedure_id: The ID of the procedure
        step_id: The ID of the step
        
    Returns:
        Formatted step details
    """
    step_data = await detailed_client.get_step_details(procedure_id, step_id)
    
    if not step_data:
        return f"Step with ID {step_id} not found for procedure with ID {procedure_id}."
    
    # Format the step data
    output = f"# Step Details for Step {step_id} in Procedure {procedure_id}\n\n"
    
    title = step_data.get("title", f"Step {step_id}")
    description = step_data.get("description", "No description available")
    
    output += f"## Title\n{title}\n\n"
    output += f"## Description\n{description}\n\n"
    
    # Add contact information if available
    contact = step_data.get("contact", {})
    if contact:
        output += "## Contact Information\n\n"
        contact_name = contact.get("name", "Name not specified")
        contact_title = contact.get("title", "Title not specified")
        contact_email = contact.get("email", "Email not specified")
        contact_phone = contact.get("phone", "Phone not specified")
        
        output += f"Name: {contact_name}\n"
        output += f"Title: {contact_title}\n"
        output += f"Email: {contact_email}\n"
        output += f"Phone: {contact_phone}\n\n"
    
    # Add location information if available
    location = step_data.get("location", {})
    if location:
        output += "## Location\n\n"
        address = location.get("address", "Address not specified")
        city = location.get("city", "City not specified")
        
        output += f"Address: {address}\n"
        output += f"City: {city}\n\n"
    
    # Add online information if available
    online = step_data.get("online", {})
    if online:
        output += "## Online Information\n\n"
        online_url = online.get("url", "URL not specified")
        online_type = online.get("type", "Type not specified")
        
        output += f"URL: {online_url}\n"
        output += f"Type: {online_type}\n\n"
    
    return output


@mcp.tool()
async def get_institution_info(institution_id: int) -> str:
    """
    Get information about an institution involved in procedures.
    
    Args:
        institution_id: The ID of the institution
        
    Returns:
        Formatted institution details
    """
    institution_data = await detailed_client.get_institution_details(institution_id)
    
    if not institution_data:
        return f"Institution with ID {institution_id} not found."
    
    # Format the institution data
    output = f"# Institution Information\n\n"
    
    name = institution_data.get("name", "Name not specified")
    description = institution_data.get("description", "No description available")
    
    output += f"## Name\n{name}\n\n"
    output += f"## Description\n{description}\n\n"
    
    # Add contact information if available
    contact = institution_data.get("contact", {})
    if contact:
        output += "## Contact Information\n\n"
        contact_name = contact.get("name", "Name not specified")
        contact_email = contact.get("email", "Email not specified")
        contact_phone = contact.get("phone", "Phone not specified")
        
        output += f"Name: {contact_name}\n"
        output += f"Email: {contact_email}\n"
        output += f"Phone: {contact_phone}\n\n"
    
    # Add location information if available
    location = institution_data.get("location", {})
    if location:
        output += "## Location\n\n"
        address = location.get("address", "Address not specified")
        city = location.get("city", "City not specified")
        
        output += f"Address: {address}\n"
        output += f"City: {city}\n\n"
    
    # Add website if available
    website = institution_data.get("website")
    if website:
        output += f"## Website\n{website}\n\n"
    
    return output


@mcp.tool()
async def list_countries() -> str:
    """
    Get a list of countries available in the eRegulations system.
    
    Returns:
        Formatted list of countries
    """
    countries = await detailed_client.get_countries()
    
    if not countries:
        return "No countries found in the eRegulations system."
    
    output = "# Available Countries in eRegulations\n\n"
    
    for country in countries:
        country_id = country.get("id", "ID not specified")
        name = country.get("name", "Name not specified")
        code = country.get("code", "Code not specified")
        
        output += f"- {name} (ID: {country_id}, Code: {code})\n"
    
    return output
