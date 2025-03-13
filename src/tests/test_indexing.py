"""
Tests for the MCP eRegulations server indexing functionality.
"""
import pytest
import os
import sys
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from mcp_eregulations.utils.indexing import ProcedureIndex


class TestProcedureIndex:
    """Tests for the ProcedureIndex class."""
    
    @pytest.fixture
    def temp_index_dir(self):
        """Create a temporary directory for index files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def index(self, temp_index_dir):
        """Create an index instance for testing."""
        return ProcedureIndex(index_dir=temp_index_dir)
    
    def test_init(self, index, temp_index_dir):
        """Test that the index is initialized correctly."""
        assert index.index_dir == temp_index_dir
        assert os.path.exists(temp_index_dir)
        assert isinstance(index.procedures_index, dict)
        assert isinstance(index.steps_index, dict)
        assert isinstance(index.requirements_index, dict)
        assert isinstance(index.institutions_index, dict)
    
    def test_index_procedure(self, index):
        """Test indexing a procedure."""
        procedure_data = {
            "id": 123,
            "title": "Test Procedure",
            "description": "Test Description",
            "additionalInfo": "Additional Info",
            "blocks": [
                {
                    "steps": [
                        {
                            "id": 1,
                            "title": "Step 1",
                            "description": "Step 1 Description"
                        },
                        {
                            "id": 2,
                            "title": "Step 2",
                            "description": "Step 2 Description"
                        }
                    ]
                }
            ]
        }
        
        index.index_procedure(123, procedure_data)
        
        # Check that the procedure was indexed
        assert "123" in index.procedures_index
        assert index.procedures_index["123"]["title"] == "Test Procedure"
        assert "test procedure test description additional info" in index.procedures_index["123"]["searchable_text"]
        
        # Check that steps were indexed
        assert "123_1" in index.steps_index
        assert "123_2" in index.steps_index
        assert index.steps_index["123_1"]["title"] == "Step 1"
        assert index.steps_index["123_2"]["title"] == "Step 2"
    
    def test_index_requirements(self, index):
        """Test indexing requirements."""
        requirements_data = {
            "items": [
                {
                    "name": "Requirement 1",
                    "description": "Requirement 1 Description"
                },
                {
                    "name": "Requirement 2",
                    "description": "Requirement 2 Description"
                }
            ]
        }
        
        index.index_requirements(123, requirements_data)
        
        # Check that requirements were indexed
        assert "123" in index.requirements_index
        assert index.requirements_index["123"]["data"] == requirements_data
    
    def test_index_institution(self, index):
        """Test indexing an institution."""
        institution_data = {
            "id": 456,
            "name": "Test Institution",
            "description": "Test Institution Description"
        }
        
        index.index_institution(456, institution_data)
        
        # Check that the institution was indexed
        assert "456" in index.institutions_index
        assert index.institutions_index["456"]["name"] == "Test Institution"
        assert "test institution test institution description" in index.institutions_index["456"]["searchable_text"]
    
    def test_search_procedures(self, index):
        """Test searching for procedures."""
        # Index some procedures
        index.index_procedure(123, {
            "id": 123,
            "title": "Business Registration",
            "description": "Register a new business",
            "additionalInfo": "Required for all new companies"
        })
        
        index.index_procedure(456, {
            "id": 456,
            "title": "Tax Filing",
            "description": "File annual taxes",
            "additionalInfo": "Required for all businesses"
        })
        
        index.index_procedure(789, {
            "id": 789,
            "title": "Import License",
            "description": "Get a license to import goods",
            "additionalInfo": "For international trade"
        })
        
        # Search for procedures
        results = index.search_procedures("business")
        assert len(results) == 2
        assert any(r["id"] == 123 for r in results)
        assert any(r["id"] == 456 for r in results)
        
        results = index.search_procedures("import")
        assert len(results) == 1
        assert results[0]["id"] == 789
        
        results = index.search_procedures("nonexistent")
        assert len(results) == 0
    
    def test_get_procedure(self, index):
        """Test getting a procedure from the index."""
        procedure_data = {"id": 123, "title": "Test Procedure"}
        index.index_procedure(123, procedure_data)
        
        result = index.get_procedure(123)
        assert result == procedure_data
        
        result = index.get_procedure(456)
        assert result is None
    
    def test_get_requirements(self, index):
        """Test getting requirements from the index."""
        requirements_data = {"items": [{"name": "Requirement 1"}]}
        index.index_requirements(123, requirements_data)
        
        result = index.get_requirements(123)
        assert result == requirements_data
        
        result = index.get_requirements(456)
        assert result is None
    
    def test_save_and_load_indices(self, index, temp_index_dir):
        """Test saving and loading indices."""
        # Index some data
        index.index_procedure(123, {"id": 123, "title": "Test Procedure"})
        index.index_requirements(123, {"items": [{"name": "Requirement 1"}]})
        index.index_institution(456, {"id": 456, "name": "Test Institution"})
        
        # Save indices
        index._save_indices()
        
        # Check that index files were created
        assert os.path.exists(os.path.join(temp_index_dir, "procedures.json"))
        assert os.path.exists(os.path.join(temp_index_dir, "requirements.json"))
        assert os.path.exists(os.path.join(temp_index_dir, "institutions.json"))
        
        # Create a new index instance to load the saved data
        new_index = ProcedureIndex(index_dir=temp_index_dir)
        
        # Check that data was loaded correctly
        assert "123" in new_index.procedures_index
        assert new_index.procedures_index["123"]["title"] == "Test Procedure"
        assert "123" in new_index.requirements_index
        assert "456" in new_index.institutions_index
        assert new_index.institutions_index["456"]["name"] == "Test Institution"
