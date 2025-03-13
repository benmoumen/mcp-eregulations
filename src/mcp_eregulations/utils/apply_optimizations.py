"""
Apply performance optimizations to MCP eRegulations tools.
"""
from mcp.server.fastmcp import FastMCP

from mcp_eregulations.utils.optimization import cached, rate_limited, timed
from mcp_eregulations.main import mcp
from mcp_eregulations.tools.procedure_tools import get_procedure, get_procedure_steps, get_procedure_requirements, get_procedure_costs
from mcp_eregulations.tools.detailed_tools import get_procedure_detailed, get_institution_info, get_country_info
from mcp_eregulations.tools.search_tools import search_procedures_by_keyword
from mcp_eregulations.tools.query_tools import process_natural_language_query, answer_procedure_question

# Apply caching to frequently used tools
mcp.tool_registry["get_procedure"] = cached(ttl_seconds=3600)(get_procedure)
mcp.tool_registry["get_procedure_steps"] = cached(ttl_seconds=3600)(get_procedure_steps)
mcp.tool_registry["get_procedure_requirements"] = cached(ttl_seconds=3600)(get_procedure_requirements)
mcp.tool_registry["get_procedure_costs"] = cached(ttl_seconds=3600)(get_procedure_costs)
mcp.tool_registry["get_procedure_detailed"] = cached(ttl_seconds=3600)(get_procedure_detailed)
mcp.tool_registry["get_institution_info"] = cached(ttl_seconds=3600)(get_institution_info)
mcp.tool_registry["get_country_info"] = cached(ttl_seconds=3600)(get_country_info)

# Apply rate limiting to search and query tools
mcp.tool_registry["search_procedures_by_keyword"] = rate_limited(search_procedures_by_keyword)
mcp.tool_registry["process_natural_language_query"] = rate_limited(process_natural_language_query)
mcp.tool_registry["answer_procedure_question"] = rate_limited(answer_procedure_question)

# Apply timing to all tools for performance monitoring
for name, tool in mcp.tool_registry.items():
    mcp.tool_registry[name] = timed(tool)

# Start background tasks for maintenance
from mcp_eregulations.utils.optimization import start_background_tasks
start_background_tasks()
