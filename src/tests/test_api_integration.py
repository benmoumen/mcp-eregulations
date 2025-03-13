"""
Tests for the MCP eRegulations server API integration.
"""
import pytest
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from mcp_eregulations.api.detailed_client import DetailedERegulationsClient


class TestDetailedERegulationsClient:
    """Tests for the DetailedERegulationsClient class."""
    
    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return DetailedERegulationsClient()
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.api.detailed_client.ERegulationsClient.get_procedure")
    @patch("mcp_eregulations.api.detailed_client.ERegulationsClient.get_procedure_resume")
    @patch("mcp_eregulations.api.detailed_client.ERegulationsClient.get_procedure_costs")
    @patch("mcp_eregulations.api.detailed_client.ERegulationsClient.get_procedure_requirements")
    async def test_get_procedure_detailed(
        self, mock_get_requirements, mock_get_costs, 
        mock_get_resume, mock_get_procedure, client
    ):
        """Test get_procedure_detailed method."""
        # Setup mocks
        mock_get_procedure.return_value = {"id": 123, "title": "Test Procedure"}
        mock_get_resume.return_value = {"title": "Resume Title", "description": "Resume Description"}
        mock_get_costs.return_value = {"totalCost": 100, "currency": "USD"}
        mock_get_requirements.return_value = {"items": [{"name": "Requirement 1"}]}
        
        # Call the method
        result = await client.get_procedure_detailed(123)
        
        # Assertions
        assert result["basic_info"] == {"id": 123, "title": "Test Procedure"}
        assert result["resume"] == {"title": "Resume Title", "description": "Resume Description"}
        assert result["costs"] == {"totalCost": 100, "currency": "USD"}
        assert result["requirements"] == {"items": [{"name": "Requirement 1"}]}
        
        # Verify method calls
        mock_get_procedure.assert_called_once_with(123)
        mock_get_resume.assert_called_once_with(123)
        mock_get_costs.assert_called_once_with(123)
        mock_get_requirements.assert_called_once_with(123)
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.api.detailed_client.ERegulationsClient.get_procedure")
    async def test_get_procedure_detailed_not_found(self, mock_get_procedure, client):
        """Test get_procedure_detailed method when procedure is not found."""
        # Setup mock
        mock_get_procedure.return_value = None
        
        # Call the method
        result = await client.get_procedure_detailed(123)
        
        # Assertions
        assert "error" in result
        assert "not found" in result["error"]
        
        # Verify method call
        mock_get_procedure.assert_called_once_with(123)
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.api.detailed_client.ERegulationsClient.make_request")
    async def test_get_procedure_abc(self, mock_make_request, client):
        """Test get_procedure_abc method."""
        # Setup mock
        mock_make_request.return_value = {"abc_data": "test"}
        
        # Call the method
        result = await client.get_procedure_abc(123)
        
        # Assertions
        assert result == {"abc_data": "test"}
        mock_make_request.assert_called_once_with("Procedures/123/ABC")
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.api.detailed_client.ERegulationsClient.make_request")
    async def test_get_step_details(self, mock_make_request, client):
        """Test get_step_details method."""
        # Setup mock
        mock_make_request.return_value = {"step_data": "test"}
        
        # Call the method
        result = await client.get_step_details(123, 456)
        
        # Assertions
        assert result == {"step_data": "test"}
        mock_make_request.assert_called_once_with("Procedures/123/Steps/456")
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.api.detailed_client.ERegulationsClient.make_request")
    async def test_get_countries(self, mock_make_request, client):
        """Test get_countries method."""
        # Setup mock
        mock_make_request.return_value = [{"id": 1, "name": "Country 1"}, {"id": 2, "name": "Country 2"}]
        
        # Call the method
        result = await client.get_countries()
        
        # Assertions
        assert len(result) == 2
        assert result[0]["name"] == "Country 1"
        assert result[1]["name"] == "Country 2"
        mock_make_request.assert_called_once_with("Country")
