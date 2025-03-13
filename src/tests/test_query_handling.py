"""
Tests for the MCP eRegulations server query handling functionality.
"""
import pytest
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from mcp_eregulations.utils.query_handling import QueryHandler


class TestQueryHandler:
    """Tests for the QueryHandler class."""
    
    @pytest.fixture
    def query_handler(self):
        """Create a query handler instance for testing."""
        return QueryHandler()
    
    @pytest.mark.asyncio
    async def test_process_query_procedure_id(self, query_handler):
        """Test processing a query for procedure by ID."""
        query = "I need information about procedure with id 123"
        result = await query_handler.process_query(query)
        
        assert result["type"] == "procedure_info"
        assert result["parameters"]["procedure_id"] == 123
        assert result["suggested_tool"] == "get_procedure"
        assert result["confidence"] >= 0.9
    
    @pytest.mark.asyncio
    async def test_process_query_procedure_steps(self, query_handler):
        """Test processing a query for procedure steps."""
        query = "What are the steps for procedure 456?"
        result = await query_handler.process_query(query)
        
        assert result["type"] == "procedure_steps"
        assert result["parameters"]["procedure_id"] == 456
        assert result["suggested_tool"] == "get_procedure_steps"
        assert result["confidence"] >= 0.9
    
    @pytest.mark.asyncio
    async def test_process_query_procedure_requirements(self, query_handler):
        """Test processing a query for procedure requirements."""
        query = "Tell me the requirements of procedure with id 789"
        result = await query_handler.process_query(query)
        
        assert result["type"] == "procedure_requirements"
        assert result["parameters"]["procedure_id"] == 789
        assert result["suggested_tool"] == "get_procedure_requirements"
        assert result["confidence"] >= 0.9
    
    @pytest.mark.asyncio
    async def test_process_query_procedure_costs(self, query_handler):
        """Test processing a query for procedure costs."""
        query = "What are the costs for procedure 321?"
        result = await query_handler.process_query(query)
        
        assert result["type"] == "procedure_costs"
        assert result["parameters"]["procedure_id"] == 321
        assert result["suggested_tool"] == "get_procedure_costs"
        assert result["confidence"] >= 0.9
    
    @pytest.mark.asyncio
    async def test_process_query_search_keyword(self, query_handler):
        """Test processing a search query with keyword."""
        query = "Search for procedures with keyword 'business registration'"
        result = await query_handler.process_query(query)
        
        assert result["type"] == "search"
        assert result["parameters"]["query"] == "business registration"
        assert result["parameters"]["limit"] == 5
        assert result["suggested_tool"] == "search_procedures_by_keyword"
        assert result["confidence"] >= 0.8
    
    @pytest.mark.asyncio
    async def test_process_query_institution_info(self, query_handler):
        """Test processing a query for institution information."""
        query = "Tell me about institution with id 654"
        result = await query_handler.process_query(query)
        
        assert result["type"] == "institution_info"
        assert result["parameters"]["institution_id"] == 654
        assert result["suggested_tool"] == "get_institution_info"
        assert result["confidence"] >= 0.9
    
    @pytest.mark.asyncio
    async def test_process_query_unknown(self, query_handler):
        """Test processing an unknown query."""
        query = "What is the meaning of life?"
        result = await query_handler.process_query(query)
        
        assert result["type"] == "unknown"
        assert "suggested_tool" in result
        assert result["confidence"] == 0.0
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_process_query_general_search(self, query_handler):
        """Test processing a general query as search."""
        query = "How to register a business in Tanzania"
        result = await query_handler.process_query(query)
        
        assert result["type"] == "search"
        assert "register" in result["parameters"]["query"]
        assert "business" in result["parameters"]["query"]
        assert "tanzania" in result["parameters"]["query"]
        assert result["suggested_tool"] == "search_procedures_by_keyword"
        assert result["confidence"] < 0.8  # Lower confidence for general search
    
    def test_extract_keywords(self, query_handler):
        """Test extracting keywords from a query."""
        query = "How to register a business in Tanzania"
        keywords = query_handler._extract_keywords(query)
        
        assert "register" in keywords
        assert "business" in keywords
        assert "tanzania" in keywords
        assert "how" not in keywords  # Stop word should be removed
        assert "to" not in keywords  # Stop word should be removed
        assert "a" not in keywords  # Stop word should be removed
        assert "in" not in keywords  # Stop word should be removed
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.utils.indexing.index.get_procedure")
    @patch("mcp_eregulations.api.detailed_client.detailed_client.get_procedure")
    async def test_generate_response_procedure_info(self, mock_get_procedure_api, mock_get_procedure_index, query_handler):
        """Test generating a response for procedure info query."""
        # Setup mocks
        mock_get_procedure_index.return_value = None
        mock_get_procedure_api.return_value = {
            "title": "Test Procedure",
            "description": "Test Description",
            "additionalInfo": "Additional Info",
            "blocks": [
                {"steps": [{"title": "Step 1"}, {"title": "Step 2"}]},
                {"steps": [{"title": "Step 3"}]}
            ]
        }
        
        query_result = {
            "type": "procedure_info",
            "parameters": {"procedure_id": 123},
            "suggested_tool": "get_procedure",
            "confidence": 0.9
        }
        
        result = await query_handler.generate_response(query_result)
        
        assert "Test Procedure" in result
        assert "Test Description" in result
        assert "Additional Info" in result
        assert "3 steps" in result
        assert "2 blocks" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_search(self, query_handler):
        """Test generating a response for search query."""
        query_result = {
            "type": "search",
            "parameters": {"query": "business registration", "limit": 5},
            "suggested_tool": "search_procedures_by_keyword",
            "confidence": 0.8
        }
        
        result = await query_handler.generate_response(query_result)
        
        assert "Searching for procedures" in result
        assert "business registration" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_unknown(self, query_handler):
        """Test generating a response for unknown query."""
        query_result = {
            "type": "unknown",
            "parameters": {},
            "suggested_tool": None,
            "confidence": 0.0,
            "message": "I couldn't understand your query."
        }
        
        result = await query_handler.generate_response(query_result)
        
        assert "I couldn't understand your query" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_low_confidence(self, query_handler):
        """Test generating a response for low confidence query."""
        query_result = {
            "type": "procedure_info",
            "parameters": {"procedure_id": 123},
            "suggested_tool": "get_procedure",
            "confidence": 0.4,
            "message": "I'm not sure what you're asking for."
        }
        
        result = await query_handler.generate_response(query_result)
        
        assert "I'm not sure what you're asking for" in result
