"""
Tests for MCP-specific features like subscriptions, completions, and error handling.
"""
import asyncio
import json
from typing import Any, Dict, Optional

import pytest
from mcp import types
from mcp.server.fastmcp import Context, FastMCP

from mcp_eregulations.utils.completion import get_completions
from mcp_eregulations.utils.errors import (
    APIError,
    AuthenticationError,
    InvalidArgumentError,
    ResourceNotFoundError,
)
from mcp_eregulations.utils.subscriptions import SubscriptionManager


class MockContext:
    """Mock MCP context for testing."""
    
    def __init__(self):
        self.notifications = []
        self.client_id = "test-client"
        
    async def notify_resource_changed(
        self,
        resource_id: str,
        content: Any,
        mime_type: Optional[str] = None
    ) -> None:
        """Record resource change notifications."""
        self.notifications.append({
            "resource_id": resource_id,
            "content": content,
            "mime_type": mime_type
        })


@pytest.fixture
async def subscription_manager():
    """Fixture providing a clean subscription manager for each test."""
    manager = SubscriptionManager()
    yield manager


@pytest.fixture
def mock_context():
    """Fixture providing a mock MCP context."""
    return MockContext()


@pytest.mark.asyncio
async def test_subscription_lifecycle(subscription_manager, mock_context):
    """Test the full lifecycle of a resource subscription."""
    pattern = "eregulations://procedure/{id}"
    client_id = mock_context.client_id
    
    # Subscribe
    await subscription_manager.subscribe(pattern, client_id, mock_context)
    
    # Verify subscription was created
    subscriptions = subscription_manager.get_subscriptions(client_id)
    assert pattern in subscriptions
    
    # Test notification
    resource_id = "eregulations://procedure/123"
    test_data = {"id": 123, "title": "Test Procedure"}
    await subscription_manager.notify_update(
        resource_id,
        test_data,
        mime_type="application/json"
    )
    
    # Verify notification was received
    assert len(mock_context.notifications) == 1
    notification = mock_context.notifications[0]
    assert notification["resource_id"] == resource_id
    assert notification["content"] == test_data
    assert notification["mime_type"] == "application/json"
    
    # Unsubscribe
    await subscription_manager.unsubscribe(pattern, client_id)
    
    # Verify subscription was removed
    subscriptions = subscription_manager.get_subscriptions(client_id)
    assert not subscriptions


@pytest.mark.asyncio
async def test_pattern_matching(subscription_manager, mock_context):
    """Test subscription pattern matching."""
    patterns = [
        "eregulations://procedure/{id}",
        "eregulations://procedure/{id}/steps",
        "eregulations://institution/{id}/**"
    ]
    client_id = mock_context.client_id
    
    # Subscribe to all patterns
    for pattern in patterns:
        await subscription_manager.subscribe(pattern, client_id, mock_context)
    
    # Test matches
    test_cases = [
        {
            "resource_id": "eregulations://procedure/123",
            "should_match": ["eregulations://procedure/{id}"]
        },
        {
            "resource_id": "eregulations://procedure/123/steps",
            "should_match": ["eregulations://procedure/{id}/steps"]
        },
        {
            "resource_id": "eregulations://institution/456/details/staff",
            "should_match": ["eregulations://institution/{id}/**"]
        }
    ]
    
    for case in test_cases:
        mock_context.notifications.clear()
        await subscription_manager.notify_update(
            case["resource_id"],
            {"test": "data"}
        )
        assert len(mock_context.notifications) == len(case["should_match"])


@pytest.mark.asyncio
async def test_completion_handlers():
    """Test argument completion handlers."""
    ctx = MockContext()
    
    # Test procedure ID completion
    completions = await get_completions(ctx, "procedure_id", "123")
    assert isinstance(completions, list)
    assert all(isinstance(item, types.CompletionItem) for item in completions)
    
    # Test query completion
    completions = await get_completions(ctx, "query", "business")
    assert isinstance(completions, list)
    assert all(isinstance(item, types.CompletionItem) for item in completions)
    
    # Test invalid argument type
    with pytest.raises(InvalidArgumentError):
        await get_completions(ctx, "invalid_type", "test")


@pytest.mark.asyncio
async def test_error_handling():
    """Test custom error classes."""
    # Test API error
    with pytest.raises(APIError) as exc_info:
        raise APIError(404, "Not found", endpoint="test/endpoint")
    assert exc_info.value.status_code == 404
    assert "test/endpoint" in exc_info.value.data
    
    # Test authentication error
    with pytest.raises(AuthenticationError) as exc_info:
        raise AuthenticationError("Invalid token")
    assert "Invalid token" in str(exc_info.value)
    
    # Test resource not found
    with pytest.raises(ResourceNotFoundError) as exc_info:
        raise ResourceNotFoundError("test://resource")
    assert "test://resource" in exc_info.value.data


@pytest.mark.asyncio
async def test_concurrent_notifications(subscription_manager, mock_context):
    """Test handling concurrent notifications to multiple subscribers."""
    patterns = [f"test://resource/{i}" for i in range(5)]
    contexts = [MockContext() for _ in range(3)]
    
    # Subscribe each context to all patterns
    for ctx in contexts:
        for pattern in patterns:
            await subscription_manager.subscribe(pattern, ctx.client_id, ctx)
    
    # Send concurrent notifications
    async def notify(resource_id: str):
        await subscription_manager.notify_update(
            resource_id,
            {"timestamp": resource_id}
        )
    
    # Create notification tasks
    tasks = [
        notify(f"test://resource/{i}")
        for i in range(5)
    ]
    
    # Run notifications concurrently
    await asyncio.gather(*tasks)
    
    # Verify all contexts received all notifications
    for ctx in contexts:
        assert len(ctx.notifications) == 5
        # Verify no duplicate notifications
        resource_ids = {n["resource_id"] for n in ctx.notifications}
        assert len(resource_ids) == 5