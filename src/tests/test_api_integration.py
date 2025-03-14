"""
Integration tests for MCP eRegulations API functionality.
Tests the interaction between API clients, resources, and MCP features.
"""
import asyncio
import json
from typing import List

import pytest
from mcp import types
from mcp.server.fastmcp import FastMCP

from mcp_eregulations.api.client import ERegulationsClient
from mcp_eregulations.api.detailed_client import DetailedERegulationsClient
from mcp_eregulations.utils import subscriptions
from mcp_eregulations.utils.errors import APIError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_procedure_resource_flow(
    mock_client: ERegulationsClient,
    mock_detailed_client: DetailedERegulationsClient,
    mock_context,
    test_server: FastMCP
):
    """Test the complete flow of fetching and exposing procedure data via MCP."""
    
    # Initialize resource handler
    @test_server.resource("eregulations://procedure/{procedure_id}")
    async def get_procedure(procedure_id: str, ctx: types.Context) -> str:
        # Set mock clients in context
        ctx.request_context.lifespan_context = {
            "client": mock_client,
            "detailed_client": mock_detailed_client
        }
        
        # Convert ID to integer
        proc_id = int(procedure_id)
        
        # Get procedure data
        result = await mock_detailed_client.get_procedure_detailed(proc_id)
        
        if "error" in result:
            return result["error"]
        
        # Format as markdown
        return format_procedure_markdown(result)
    
    # Test procedure resource
    result = await get_procedure("123", mock_context)
    
    # Verify markdown formatting
    assert "# Test Procedure" in result
    assert "## Basic Information" in result
    assert "A test procedure" in result
    assert "## Steps" in result
    assert "Step 1" in result
    assert "Step 2" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_subscription_notification_flow(
    mock_client: ERegulationsClient,
    mock_context,
    test_server: FastMCP
):
    """Test subscription and notification flow for procedure updates."""
    # Subscribe to procedure updates
    pattern = "eregulations://procedure/{id}"
    await subscriptions.subscription_manager.subscribe(
        pattern,
        mock_context.client_id,
        mock_context
    )
    
    # Simulate procedure update through client
    await mock_client.get_procedure(123)
    
    # Verify notification was sent
    assert len(mock_context.notifications) == 1
    notification = mock_context.notifications[0]
    assert notification["resource_id"] == "eregulations://procedure/123"
    assert notification["content"]["title"] == "Test Procedure"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling_flow(
    mock_client: ERegulationsClient,
    mock_context,
    test_server: FastMCP
):
    """Test error handling across API and MCP layers."""
    # Set up error handler
    @test_server.resource("eregulations://error-test/{status}")
    async def trigger_error(status: str, ctx: types.Context) -> str:
        ctx.request_context.lifespan_context = {"client": mock_client}
        status_code = int(status)
        
        try:
            # This will raise an APIError
            await mock_client.make_request(f"error/{status_code}")
            return "This should not happen"
        except APIError as e:
            # Verify error is properly propagated
            assert e.status_code == status_code
            return f"Error {status_code}: {str(e)}"
    
    # Test with different error scenarios
    error_codes = [400, 401, 403, 404, 500]
    for code in error_codes:
        result = await trigger_error(str(code), mock_context)
        assert f"Error {code}" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_resource_access(
    mock_client: ERegulationsClient,
    mock_detailed_client: DetailedERegulationsClient,
    mock_context,
    test_server: FastMCP
):
    """Test concurrent access to MCP resources."""
    # Initialize resource
    @test_server.resource("eregulations://concurrent-test/{id}")
    async def concurrent_resource(id: str, ctx: types.Context) -> str:
        ctx.request_context.lifespan_context = {
            "client": mock_client,
            "detailed_client": mock_detailed_client
        }
        
        # Simulate some async work
        await asyncio.sleep(0.1)
        return f"Resource {id} processed"
    
    # Test concurrent access
    ids = list(range(5))
    tasks = [
        concurrent_resource(str(id), mock_context)
        for id in ids
    ]
    
    # Execute concurrently
    results = await asyncio.gather(*tasks)
    
    # Verify all requests completed
    assert len(results) == len(ids)
    for id, result in zip(ids, results):
        assert f"Resource {id} processed" in result


def format_procedure_markdown(data: dict) -> str:
    """Helper function to format procedure data as markdown."""
    output = []
    
    # Title
    if "basic_info" in data:
        basic = data["basic_info"]
        output.append(f"# {basic.get('title', 'Untitled Procedure')}\n")
        output.append("## Basic Information\n")
        output.append(basic.get("description", "No description available") + "\n")
    
    # Resume
    if "resume" in data and data["resume"]:
        output.append("## Resume\n")
        output.append(data["resume"].get("text", "No resume available") + "\n")
    
    # Steps
    if "basic_info" in data and "blocks" in data["basic_info"]:
        output.append("## Steps\n")
        for block in data["basic_info"]["blocks"]:
            for step in block.get("steps", []):
                output.append(f"### Step {step.get('id')}: {step.get('title')}\n")
                if "description" in step:
                    output.append(step["description"] + "\n")
    
    # Costs
    if "costs" in data and data["costs"]:
        output.append("## Costs\n")
        costs = data["costs"]
        output.append(f"Total: {costs.get('total', 'Not specified')}\n")
        
        if "items" in costs:
            output.append("### Breakdown:\n")
            for item in costs["items"]:
                output.append(f"- {item.get('name')}: {item.get('amount')}\n")
    
    return "\n".join(output)
