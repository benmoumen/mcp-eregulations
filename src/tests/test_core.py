"""
Tests for the MCP eRegulations server core components.
"""
import pytest
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from mcp_eregulations.config.settings import Settings
from mcp_eregulations.api.client import ERegulationsClient
from mcp_eregulations.utils.formatters import (
    format_procedure_summary,
    format_procedure_steps,
    extract_procedure_id_from_url
)


class TestSettings:
    """Tests for the Settings class."""
    
    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        settings = Settings()
        assert settings.EREGULATIONS_API_URL == "https://api-tanzania.tradeportal.org"
        assert settings.EREGULATIONS_API_VERSION == "v1"
        assert settings.MCP_SERVER_NAME == "eregulations"
        assert settings.MCP_SERVER_PORT == 8000
        assert settings.CACHE_ENABLED is True
        assert settings.CACHE_TTL == 3600
        assert settings.LOG_LEVEL == "INFO"
    
    def test_api_base_url(self):
        """Test that api_base_url property returns the correct URL."""
        settings = Settings()
        assert settings.api_base_url == "https://api-tanzania.tradeportal.org"


class TestERegulationsClient:
    """Tests for the ERegulationsClient class."""
    
    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return ERegulationsClient()
    
    def test_init(self, client):
        """Test that the client is initialized correctly."""
        assert client.base_url == "https://api-tanzania.tradeportal.org"
        assert "User-Agent" in client.headers
        assert "Accept" in client.headers
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.api.client.httpx.AsyncClient")
    async def test_make_request_success(self, mock_client, client):
        """Test successful API request."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json.return_value = {"key": "value"}
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Call the method
        result = await client.make_request("test/endpoint")
        
        # Assertions
        assert result == {"key": "value"}
        mock_client_instance.get.assert_called_once_with(
            "https://api-tanzania.tradeportal.org/test/endpoint",
            headers=client.headers,
            timeout=30.0
        )
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.api.client.httpx.AsyncClient")
    async def test_make_request_http_error(self, mock_client, client):
        """Test API request with HTTP error."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Call the method
        result = await client.make_request("test/endpoint")
        
        # Assertions
        assert result is None
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.api.client.ERegulationsClient.make_request")
    async def test_get_procedure(self, mock_make_request, client):
        """Test get_procedure method."""
        # Setup mock
        mock_make_request.return_value = {"id": 123, "title": "Test Procedure"}
        
        # Call the method
        result = await client.get_procedure(123)
        
        # Assertions
        assert result == {"id": 123, "title": "Test Procedure"}
        mock_make_request.assert_called_once_with("Procedures/123")


class TestFormatters:
    """Tests for the formatter utility functions."""
    
    def test_format_procedure_summary(self):
        """Test format_procedure_summary function."""
        procedure = {
            "title": "Test Procedure",
            "url": "https://example.com/procedure/123",
            "additionalInfo": "Additional information",
            "blocks": [
                {"steps": [{"title": "Step 1"}, {"title": "Step 2"}]},
                {"steps": [{"title": "Step 3"}]}
            ]
        }
        
        result = format_procedure_summary(procedure)
        
        assert "Test Procedure" in result
        assert "https://example.com/procedure/123" in result
        assert "Additional information" in result
        assert "Number of blocks: 2" in result
        assert "Total steps: 3" in result
    
    def test_format_procedure_summary_empty(self):
        """Test format_procedure_summary function with empty input."""
        result = format_procedure_summary(None)
        assert "Procedure information not available" in result
    
    def test_format_procedure_steps(self):
        """Test format_procedure_steps function."""
        steps = [
            {
                "title": "Step 1",
                "description": "Description 1",
                "online": {"url": "https://example.com/step1"}
            },
            {
                "title": "Step 2",
                "description": "Description 2"
            }
        ]
        
        result = format_procedure_steps(steps)
        
        assert "Step 1: Step 1" in result
        assert "Description: Description 1" in result
        assert "Online: https://example.com/step1" in result
        assert "Step 2: Step 2" in result
        assert "Description: Description 2" in result
    
    def test_format_procedure_steps_empty(self):
        """Test format_procedure_steps function with empty input."""
        result = format_procedure_steps([])
        assert "No steps available" in result
    
    def test_extract_procedure_id_from_url(self):
        """Test extract_procedure_id_from_url function."""
        # Test valid URLs
        assert extract_procedure_id_from_url("https://example.com/procedure/123") == 123
        assert extract_procedure_id_from_url("/procedures/456") == 456
        assert extract_procedure_id_from_url("procedure/789/") == 789
        
        # Test invalid URLs
        assert extract_procedure_id_from_url("https://example.com/not-a-procedure") is None
        assert extract_procedure_id_from_url("") is None
        assert extract_procedure_id_from_url("procedure/abc") is None
