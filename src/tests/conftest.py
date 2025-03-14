"""
Shared test fixtures and configuration for MCP eRegulations tests.
"""
import asyncio
import os
from typing import Any, AsyncGenerator, Dict, Optional

import pytest
from mcp import types
from mcp.server.fastmcp import Context, FastMCP

from mcp_eregulations.api.client import ERegulationsClient
from mcp_eregulations.api.detailed_client import DetailedERegulationsClient
from mcp_eregulations.config.settings import settings
from mcp_eregulations.utils import indexing


class MockAPIResponse:
    """Mock response for API requests."""
    def __init__(self, status_code: int = 200, json_data: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self._json_data = json_data or {}
    
    def raise_for_status(self):
        """Raise an exception if status code indicates error."""
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")
    
    def json(self):
        """Return JSON data."""
        return self._json_data


class MockAsyncClient:
    """Mock async HTTP client."""
    def __init__(self, responses: Dict[str, MockAPIResponse]):
        self.responses = responses
        self.requests = []
    
    async def get(self, url: str) -> MockAPIResponse:
        """Record request and return mock response."""
        self.requests.append(url)
        return self.responses.get(url, MockAPIResponse(404, {"error": "Not found"}))
    
    async def aclose(self):
        """Mock cleanup."""
        pass


class MockContext:
    """Mock MCP context for testing."""
    def __init__(self):
        self.notifications = []
        self.client_id = "test-client"
        self.request_context = self
        self.lifespan_context = {}
        self.logs = []
    
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
    
    def info(self, message: str):
        """Record info log."""
        self.logs.append(("info", message))
    
    def warning(self, message: str):
        """Record warning log."""
        self.logs.append(("warning", message))
    
    def error(self, message: str):
        """Record error log."""
        self.logs.append(("error", message))


@pytest.fixture
def mock_responses() -> Dict[str, MockAPIResponse]:
    """Fixture providing mock API responses."""
    return {
        f"{settings.api_base_url}/Procedures/123": MockAPIResponse(
            200,
            {
                "id": 123,
                "title": "Test Procedure",
                "description": "A test procedure",
                "blocks": [
                    {
                        "id": 1,
                        "steps": [
                            {"id": 1, "title": "Step 1"},
                            {"id": 2, "title": "Step 2"}
                        ]
                    }
                ]
            }
        ),
        f"{settings.api_base_url}/Procedures/123/Resume": MockAPIResponse(
            200,
            {
                "id": 123,
                "text": "Test procedure resume"
            }
        ),
        f"{settings.api_base_url}/Procedures/123/Totals": MockAPIResponse(
            200,
            {
                "total": 100,
                "items": [
                    {"name": "Fee 1", "amount": 50},
                    {"name": "Fee 2", "amount": 50}
                ]
            }
        )
    }


@pytest.fixture
async def mock_client(mock_responses) -> AsyncGenerator[ERegulationsClient, None]:
    """Fixture providing a mock API client."""
    client = ERegulationsClient()
    client._client = MockAsyncClient(mock_responses)
    yield client
    await client.close()


@pytest.fixture
async def mock_detailed_client(mock_responses) -> AsyncGenerator[DetailedERegulationsClient, None]:
    """Fixture providing a mock detailed API client."""
    client = DetailedERegulationsClient()
    client._client = MockAsyncClient(mock_responses)
    yield client
    await client.close()


@pytest.fixture
def mock_context() -> MockContext:
    """Fixture providing a mock MCP context."""
    return MockContext()


@pytest.fixture
def test_server() -> FastMCP:
    """Fixture providing a test MCP server instance."""
    return FastMCP("test-server")


@pytest.fixture
def temp_index(tmp_path) -> indexing.SearchIndex:
    """Fixture providing a temporary search index."""
    index_dir = tmp_path / "index"
    return indexing.SearchIndex(str(index_dir))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as asynchronous"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring integration setup"
    )
    config.addinivalue_line(
        "markers",
        "subscription: mark test as testing subscription features"
    )
    config.addinivalue_line(
        "markers",
        "completion: mark test as testing completion features"
    )
    config.addinivalue_line(
        "markers",
        "prompt: mark test as testing prompt features"
    )