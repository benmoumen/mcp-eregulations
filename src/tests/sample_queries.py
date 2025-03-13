"""
Sample queries for validating the MCP eRegulations server functionality.
"""
import os
import sys
import asyncio
import json
from pprint import pprint

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from mcp_eregulations.tools.procedure_tools import (
    get_procedure,
    get_procedure_steps,
    get_procedure_requirements,
    get_procedure_costs
)
from mcp_eregulations.tools.detailed_tools import (
    get_procedure_detailed,
    get_institution_info,
    get_country_info
)
from mcp_eregulations.tools.search_tools import (
    search_procedures_by_keyword
)
from mcp_eregulations.tools.query_tools import (
    process_natural_language_query,
    answer_procedure_question
)
from mcp_eregulations.tools.auth_tools import (
    register_user,
    authenticate_user,
    create_api_key
)


async def run_sample_queries():
    """Run sample queries to validate functionality."""
    print("=== Running Sample Queries for MCP eRegulations Server ===\n")
    
    # Basic procedure information
    print("=== Basic Procedure Information ===")
    procedure_id = 1  # Using a sample procedure ID
    procedure_info = await get_procedure(procedure_id)
    print(f"Procedure {procedure_id} Information:")
    print(procedure_info)
    print("\n" + "-" * 80 + "\n")
    
    # Procedure steps
    print("=== Procedure Steps ===")
    steps_info = await get_procedure_steps(procedure_id)
    print(f"Steps for Procedure {procedure_id}:")
    print(steps_info)
    print("\n" + "-" * 80 + "\n")
    
    # Procedure requirements
    print("=== Procedure Requirements ===")
    requirements_info = await get_procedure_requirements(procedure_id)
    print(f"Requirements for Procedure {procedure_id}:")
    print(requirements_info)
    print("\n" + "-" * 80 + "\n")
    
    # Procedure costs
    print("=== Procedure Costs ===")
    costs_info = await get_procedure_costs(procedure_id)
    print(f"Costs for Procedure {procedure_id}:")
    print(costs_info)
    print("\n" + "-" * 80 + "\n")
    
    # Detailed procedure information
    print("=== Detailed Procedure Information ===")
    detailed_info = await get_procedure_detailed(procedure_id)
    print(f"Detailed Information for Procedure {procedure_id}:")
    print(json.dumps(detailed_info, indent=2) if isinstance(detailed_info, dict) else detailed_info)
    print("\n" + "-" * 80 + "\n")
    
    # Institution information
    print("=== Institution Information ===")
    institution_id = 1  # Using a sample institution ID
    institution_info = await get_institution_info(institution_id)
    print(f"Information for Institution {institution_id}:")
    print(institution_info)
    print("\n" + "-" * 80 + "\n")
    
    # Country information
    print("=== Country Information ===")
    country_id = 1  # Using a sample country ID
    country_info = await get_country_info(country_id)
    print(f"Information for Country {country_id}:")
    print(country_info)
    print("\n" + "-" * 80 + "\n")
    
    # Search procedures
    print("=== Search Procedures ===")
    search_query = "business registration"
    search_results = await search_procedures_by_keyword(search_query)
    print(f"Search Results for '{search_query}':")
    print(search_results)
    print("\n" + "-" * 80 + "\n")
    
    # Natural language query processing
    print("=== Natural Language Query Processing ===")
    nl_queries = [
        "What is procedure 1 about?",
        "Tell me the steps for procedure 1",
        "What are the requirements for procedure 1?",
        "How much does procedure 1 cost?",
        "Search for business registration procedures",
        "Tell me about institution 1",
        "What procedures are related to import licenses?"
    ]
    
    for query in nl_queries:
        print(f"Query: {query}")
        response = await process_natural_language_query(query)
        print(f"Response: {response}")
        print()
    
    print("-" * 80 + "\n")
    
    # Answer specific questions about procedures
    print("=== Answering Specific Questions ===")
    questions = [
        "What documents do I need?",
        "How long does this procedure take?",
        "How much does it cost?",
        "Which institutions are involved?"
    ]
    
    for question in questions:
        print(f"Question about Procedure {procedure_id}: {question}")
        answer = await answer_procedure_question(procedure_id, question)
        print(f"Answer: {answer}")
        print()
    
    print("-" * 80 + "\n")
    
    # Authentication and API key management
    print("=== Authentication and API Key Management ===")
    # Register a test user
    username = "test_user"
    password = "test_password"
    
    print(f"Registering user: {username}")
    register_result = await register_user(username, password)
    print(register_result)
    
    print(f"Authenticating user: {username}")
    auth_result = await authenticate_user(username, password)
    print(auth_result)
    
    # Extract token from auth result
    token = auth_result.split("Token: ")[-1] if "Token: " in auth_result else None
    
    if token:
        print(f"Creating API key for user: {username}")
        api_key_result = await create_api_key(username, api_key=token)
        print(api_key_result)
    
    print("\n" + "-" * 80 + "\n")
    
    print("=== Sample Queries Completed ===")


if __name__ == "__main__":
    asyncio.run(run_sample_queries())
