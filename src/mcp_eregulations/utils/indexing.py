"""
Data processing and indexing functionality for eRegulations data.
"""
from typing import Any, Dict, List, Optional
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ProcedureIndex:
    """Class for indexing and retrieving procedure data."""
    
    def __init__(self, index_dir: str = "/home/ubuntu/mcp-eregulations/data/index"):
        """
        Initialize the procedure index.
        
        Args:
            index_dir: Directory to store index files
        """
        self.index_dir = index_dir
        self.procedures_index = {}
        self.steps_index = {}
        self.requirements_index = {}
        self.institutions_index = {}
        
        # Create index directory if it doesn't exist
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Load existing indices if available
        self._load_indices()
    
    def _load_indices(self):
        """Load existing indices from disk."""
        try:
            procedures_path = os.path.join(self.index_dir, "procedures.json")
            if os.path.exists(procedures_path):
                with open(procedures_path, "r") as f:
                    self.procedures_index = json.load(f)
            
            steps_path = os.path.join(self.index_dir, "steps.json")
            if os.path.exists(steps_path):
                with open(steps_path, "r") as f:
                    self.steps_index = json.load(f)
            
            requirements_path = os.path.join(self.index_dir, "requirements.json")
            if os.path.exists(requirements_path):
                with open(requirements_path, "r") as f:
                    self.requirements_index = json.load(f)
            
            institutions_path = os.path.join(self.index_dir, "institutions.json")
            if os.path.exists(institutions_path):
                with open(institutions_path, "r") as f:
                    self.institutions_index = json.load(f)
                    
            logger.info("Loaded existing indices from disk")
        except Exception as e:
            logger.error(f"Error loading indices: {e}")
    
    def _save_indices(self):
        """Save indices to disk."""
        try:
            procedures_path = os.path.join(self.index_dir, "procedures.json")
            with open(procedures_path, "w") as f:
                json.dump(self.procedures_index, f)
            
            steps_path = os.path.join(self.index_dir, "steps.json")
            with open(steps_path, "w") as f:
                json.dump(self.steps_index, f)
            
            requirements_path = os.path.join(self.index_dir, "requirements.json")
            with open(requirements_path, "w") as f:
                json.dump(self.requirements_index, f)
            
            institutions_path = os.path.join(self.index_dir, "institutions.json")
            with open(institutions_path, "w") as f:
                json.dump(self.institutions_index, f)
                
            logger.info("Saved indices to disk")
        except Exception as e:
            logger.error(f"Error saving indices: {e}")
    
    def index_procedure(self, procedure_id: int, procedure_data: Dict[str, Any]):
        """
        Index a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            procedure_data: The procedure data to index
        """
        # Extract searchable fields
        title = procedure_data.get("title", "")
        description = procedure_data.get("description", "")
        additional_info = procedure_data.get("additionalInfo", "")
        
        # Create searchable text
        searchable_text = f"{title} {description} {additional_info}".lower()
        
        # Store in index with metadata
        self.procedures_index[str(procedure_id)] = {
            "id": procedure_id,
            "title": title,
            "searchable_text": searchable_text,
            "last_updated": datetime.now().isoformat(),
            "data": procedure_data
        }
        
        # Index steps if available
        blocks = procedure_data.get("blocks", [])
        for block in blocks:
            steps = block.get("steps", [])
            for step in steps:
                step_id = step.get("id")
                if step_id:
                    self.index_step(procedure_id, step_id, step)
        
        # Save indices
        self._save_indices()
    
    def index_step(self, procedure_id: int, step_id: int, step_data: Dict[str, Any]):
        """
        Index a step.
        
        Args:
            procedure_id: The ID of the procedure
            step_id: The ID of the step
            step_data: The step data to index
        """
        # Extract searchable fields
        title = step_data.get("title", "")
        description = step_data.get("description", "")
        
        # Create searchable text
        searchable_text = f"{title} {description}".lower()
        
        # Store in index with metadata
        key = f"{procedure_id}_{step_id}"
        self.steps_index[key] = {
            "procedure_id": procedure_id,
            "step_id": step_id,
            "title": title,
            "searchable_text": searchable_text,
            "last_updated": datetime.now().isoformat(),
            "data": step_data
        }
    
    def index_requirements(self, procedure_id: int, requirements_data: Dict[str, Any]):
        """
        Index requirements for a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            requirements_data: The requirements data to index
        """
        # Store in index with metadata
        self.requirements_index[str(procedure_id)] = {
            "procedure_id": procedure_id,
            "last_updated": datetime.now().isoformat(),
            "data": requirements_data
        }
        
        # Save indices
        self._save_indices()
    
    def index_institution(self, institution_id: int, institution_data: Dict[str, Any]):
        """
        Index an institution.
        
        Args:
            institution_id: The ID of the institution
            institution_data: The institution data to index
        """
        # Extract searchable fields
        name = institution_data.get("name", "")
        description = institution_data.get("description", "")
        
        # Create searchable text
        searchable_text = f"{name} {description}".lower()
        
        # Store in index with metadata
        self.institutions_index[str(institution_id)] = {
            "id": institution_id,
            "name": name,
            "searchable_text": searchable_text,
            "last_updated": datetime.now().isoformat(),
            "data": institution_data
        }
        
        # Save indices
        self._save_indices()
    
    def search_procedures(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for procedures matching a query.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching procedures
        """
        query = query.lower()
        results = []
        
        # Simple search implementation
        for proc_id, proc_data in self.procedures_index.items():
            if query in proc_data["searchable_text"]:
                results.append({
                    "id": proc_data["id"],
                    "title": proc_data["title"],
                    "score": 1.0  # Simple scoring for now
                })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def get_procedure(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a procedure from the index.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            The procedure data, or None if not found
        """
        proc_data = self.procedures_index.get(str(procedure_id))
        if proc_data:
            return proc_data["data"]
        return None
    
    def get_step(self, procedure_id: int, step_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a step from the index.
        
        Args:
            procedure_id: The ID of the procedure
            step_id: The ID of the step
            
        Returns:
            The step data, or None if not found
        """
        key = f"{procedure_id}_{step_id}"
        step_data = self.steps_index.get(key)
        if step_data:
            return step_data["data"]
        return None
    
    def get_requirements(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get requirements for a procedure from the index.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            The requirements data, or None if not found
        """
        req_data = self.requirements_index.get(str(procedure_id))
        if req_data:
            return req_data["data"]
        return None
    
    def get_institution(self, institution_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an institution from the index.
        
        Args:
            institution_id: The ID of the institution
            
        Returns:
            The institution data, or None if not found
        """
        inst_data = self.institutions_index.get(str(institution_id))
        if inst_data:
            return inst_data["data"]
        return None

# Create a global index instance
index = ProcedureIndex()
