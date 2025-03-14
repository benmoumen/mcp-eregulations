"""
Tests for MCP prompt functionality.
"""
import pytest
from mcp import types
from mcp.server.fastmcp import FastMCP

from mcp_eregulations.main import (
    analyze_procedure,
    compare_procedures,
    debug_error,
    search_eregulations
)


def test_search_eregulations_prompt():
    """Test the search eRegulations prompt."""
    query = "business registration"
    result = search_eregulations(query)
    
    assert isinstance(result, str)
    assert query in result
    assert "search_procedures_by_keyword" in result
    assert "get_procedure" in result
    assert "get_procedure_steps" in result
    assert "get_procedure_requirements" in result
    assert "get_procedure_costs" in result


def test_analyze_procedure_prompt():
    """Test the procedure analysis prompt."""
    procedure_id = 123
    result = analyze_procedure(procedure_id)
    
    assert isinstance(result, str)
    assert str(procedure_id) in result
    assert "get_procedure" in result
    assert "get_procedure_steps" in result
    assert "get_procedure_requirements" in result
    assert "get_procedure_costs" in result
    assert "get_procedure_abc_analysis" in result


def test_compare_procedures_prompt():
    """Test the procedure comparison prompt."""
    procedure_ids = [123, 456, 789]
    result = compare_procedures(procedure_ids)
    
    assert isinstance(result, str)
    # Check all IDs are included
    for pid in procedure_ids:
        assert str(pid) in result
    
    # Check required analysis points
    assert "complexity" in result.lower()
    assert "costs" in result.lower()
    assert "requirements" in result.lower()
    assert "time" in result.lower()


def test_debug_error_prompt():
    """Test the error debugging prompt."""
    error_message = "API Error: 404 Not Found"
    result = debug_error(error_message)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(msg, types.Message) for msg in result)
    
    # Check message sequence
    messages = [msg.content.text for msg in result if isinstance(msg.content, types.TextContent)]
    assert any(error_message in msg for msg in messages)  # Error is shown
    assert any("health_check" in msg for msg in messages)  # Suggests health check
    assert any("auth_tools" in msg for msg in messages)  # Suggests auth check


@pytest.mark.asyncio
async def test_prompt_registration():
    """Test prompt registration with FastMCP server."""
    mcp = FastMCP("test-server")
    
    # Register test prompt
    @mcp.prompt()
    def test_prompt(arg: str) -> str:
        return f"Test prompt with arg: {arg}"
    
    # Get registered prompts
    prompts = await mcp.list_prompts()
    
    # Verify our prompt is registered
    assert any(p.name == "test_prompt" for p in prompts)
    
    # Test prompt execution
    result = test_prompt("test-arg")
    assert isinstance(result, str)
    assert "test-arg" in result


@pytest.mark.asyncio
async def test_prompt_with_context():
    """Test prompts that use MCP context."""
    mcp = FastMCP("test-server")
    
    @mcp.prompt()
    def context_prompt(arg: str, ctx: types.Context = None) -> str:
        assert ctx is not None
        return f"Prompt with context and arg: {arg}"
    
    # Get registered prompts
    prompts = await mcp.list_prompts()
    
    # Verify our prompt is registered with context
    prompt_info = next(p for p in prompts if p.name == "context_prompt")
    assert prompt_info.arguments[0].name == "arg"


@pytest.mark.asyncio
async def test_prompt_chain():
    """Test chaining multiple prompts together."""
    mcp = FastMCP("test-server")
    
    @mcp.prompt()
    def first_prompt(data: str) -> list[types.Message]:
        return [
            types.UserMessage(data),
            types.AssistantMessage("First prompt response")
        ]
    
    @mcp.prompt()
    def second_prompt(previous_response: str) -> list[types.Message]:
        return [
            types.UserMessage(previous_response),
            types.AssistantMessage("Second prompt response")
        ]
    
    # Verify both prompts are registered
    prompts = await mcp.list_prompts()
    prompt_names = {p.name for p in prompts}
    assert "first_prompt" in prompt_names
    assert "second_prompt" in prompt_names
    
    # Test execution chain
    first_result = first_prompt("test-data")
    assert isinstance(first_result, list)
    assert len(first_result) == 2
    
    # Use first result in second prompt
    second_result = second_prompt(first_result[-1].content.text)
    assert isinstance(second_result, list)
    assert len(second_result) == 2