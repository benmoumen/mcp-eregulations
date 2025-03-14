"""
API client for interacting with the eRegulations API.
"""
from typing import Any, Dict, List, Optional
import httpx
import logging
from mcp_eregulations.config.settings import settings
from mcp_eregulations.utils import subscriptions
from mcp_eregulations.utils.errors import APIError

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
        
        # Initialize HTTP client with connection pooling
        self._client: Optional[httpx.AsyncClient] = None
    
    async def init(self) -> None:
        """Initialize the HTTP client."""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers=self.headers,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Make a request to the eRegulations API.
        
        Args:
            endpoint: The API endpoint to request (without base URL)
            
        Returns:
            The JSON response as a dictionary, or None if the request failed
            
        Raises:
            APIError: If the API request fails
        """
        if not self._client:
            await self.init()
        
        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Making request to: {url}")
        
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise APIError(
                e.response.status_code,
                str(e),
                endpoint=endpoint
            )
        except httpx.RequestError as e:
            raise APIError(
                500,
                f"Request error: {str(e)}",
                endpoint=endpoint
            )
        except Exception as e:
            raise APIError(
                500,
                f"Unexpected error: {str(e)}",
                endpoint=endpoint
            )
    
    async def get_procedure(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a procedure by ID.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            The procedure data, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}"
        try:
            data = await self.make_request(endpoint)
            
            # Notify subscribers if data was fetched successfully
            if data:
                await subscriptions.subscription_manager.notify_update(
                    f"eregulations://procedure/{procedure_id}",
                    data,
                    mime_type="application/json"
                )
            
            return data
        except APIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def get_procedure_resume(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a procedure resume by ID.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            The procedure resume data, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/Resume"
        try:
            data = await self.make_request(endpoint)
            
            # Notify subscribers if data was fetched successfully
            if data:
                await subscriptions.subscription_manager.notify_update(
                    f"eregulations://procedure/{procedure_id}/resume",
                    data,
                    mime_type="application/json"
                )
            
            return data
        except APIError as e:
            if e.status_code == 404:
                return None
            raise
    
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
        
        # Notify subscribers about steps data
        if steps:
            await subscriptions.subscription_manager.notify_update(
                f"eregulations://procedure/{procedure_id}/steps",
                steps,
                mime_type="application/json"
            )
        
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
        try:
            data = await self.make_request(endpoint)
            
            # Notify subscribers if data was fetched successfully
            if data:
                await subscriptions.subscription_manager.notify_update(
                    f"eregulations://procedure/{procedure_id}/requirements",
                    data,
                    mime_type="application/json"
                )
            
            return data
        except APIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def get_procedure_costs(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get costs for a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            Cost data for the procedure, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/Totals"
        try:
            data = await self.make_request(endpoint)
            
            # Notify subscribers if data was fetched successfully
            if data:
                await subscriptions.subscription_manager.notify_update(
                    f"eregulations://procedure/{procedure_id}/costs",
                    data,
                    mime_type="application/json"
                )
            
            return data
        except APIError as e:
            if e.status_code == 404:
                return None
            raise


# Create a global client instance
client = ERegulationsClient()
