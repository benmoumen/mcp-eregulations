"""
API client for interacting with the eRegulations API.
"""
from typing import Any, Dict, List, Optional
import httpx
import logging
from mcp_eregulations.config.settings import settings

logger = logging.getLogger(__name__)

class ERegulationsClient:
    """Client for interacting with the eRegulations API."""
    
    def __init__(self):
        """Initialize the eRegulations API client."""
        self.base_url = settings.api_base_url
        self.api_key = settings.EREGULATIONS_API_KEY
        self.headers = {
            "User-Agent": "eregulations-mcp-server/1.0",
            "Accept": "application/json"
        }
        
        # Add API key to headers if provided
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Make a request to the eRegulations API.
        
        Args:
            endpoint: The API endpoint to request (without base URL)
            
        Returns:
            The JSON response as a dictionary, or None if the request failed
        """
        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Making request to: {url}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=30.0)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return None
    
    async def get_procedure(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a procedure by ID.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            The procedure data, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}"
        return await self.make_request(endpoint)
    
    async def get_procedure_resume(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a procedure resume by ID.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            The procedure resume data, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/Resume"
        return await self.make_request(endpoint)
    
    async def get_procedure_steps(self, procedure_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get steps for a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            List of steps for the procedure, or None if not found
        """
        # First get the procedure to extract steps
        procedure_data = await self.get_procedure(procedure_id)
        
        if not procedure_data or "blocks" not in procedure_data:
            return None
        
        # Extract steps from all blocks
        steps = []
        for block in procedure_data.get("blocks", []):
            steps.extend(block.get("steps", []))
        
        return steps
    
    async def get_procedure_requirements(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get requirements for a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            Requirements data for the procedure, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/ABC/Requirements"
        return await self.make_request(endpoint)
    
    async def get_procedure_costs(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get costs for a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            Cost data for the procedure, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/Totals"
        return await self.make_request(endpoint)

# Create a global client instance
client = ERegulationsClient()
