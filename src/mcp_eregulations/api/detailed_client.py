"""
Detailed API client with enhanced functionality for eRegulations data.
"""
import logging
from typing import Any, Dict, List, Optional

from mcp_eregulations.api.client import ERegulationsClient
from mcp_eregulations.utils import subscriptions
from mcp_eregulations.utils.errors import APIError

logger = logging.getLogger(__name__)


class DetailedERegulationsClient(ERegulationsClient):
    """Enhanced client with additional API functionality."""

    async def get_procedure_detailed(self, procedure_id: int) -> Dict[str, Any]:
        """
        Get comprehensive information about a procedure by combining multiple API calls.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            Combined procedure information
        """
        try:
            # Get basic procedure data
            basic_info = await self.get_procedure(procedure_id)
            if not basic_info:
                return {"error": f"Procedure {procedure_id} not found"}
            
            # Get additional information
            resume = await self.get_procedure_resume(procedure_id)
            costs = await self.get_procedure_costs(procedure_id)
            requirements = await self.get_procedure_requirements(procedure_id)
            
            # Combine all data
            result = {
                "basic_info": basic_info,
                "resume": resume,
                "costs": costs,
                "requirements": requirements
            }
            
            # Notify subscribers about the combined data
            await subscriptions.subscription_manager.notify_update(
                f"eregulations://procedure/{procedure_id}/detailed",
                result,
                mime_type="application/json"
            )
            
            return result
            
        except APIError as e:
            return {"error": str(e)}
    
    async def get_procedure_abc(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get Activity-Based Costing analysis for a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            ABC analysis data or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/ABC"
        try:
            data = await self.make_request(endpoint)
            
            # Notify subscribers if data was fetched
            if data:
                await subscriptions.subscription_manager.notify_update(
                    f"eregulations://procedure/{procedure_id}/abc",
                    data,
                    mime_type="application/json"
                )
            
            return data
        except APIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def get_step_details(
        self, procedure_id: int, step_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific step.
        
        Args:
            procedure_id: The ID of the procedure
            step_id: The ID of the step
            
        Returns:
            Step details or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/Steps/{step_id}"
        try:
            data = await self.make_request(endpoint)
            
            # Notify subscribers if data was fetched
            if data:
                await subscriptions.subscription_manager.notify_update(
                    f"eregulations://procedure/{procedure_id}/step/{step_id}",
                    data,
                    mime_type="application/json"
                )
            
            return data
        except APIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def get_institution_details(self, institution_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information about an institution.
        
        Args:
            institution_id: The ID of the institution
            
        Returns:
            Institution details or None if not found
        """
        endpoint = f"Institutions/{institution_id}"
        try:
            data = await self.make_request(endpoint)
            
            # Notify subscribers if data was fetched
            if data:
                await subscriptions.subscription_manager.notify_update(
                    f"eregulations://institution/{institution_id}",
                    data,
                    mime_type="application/json"
                )
            
            return data
        except APIError as e:
            if e.status_code == 404:
                return None
            raise
    
    async def get_countries(self) -> List[Dict[str, Any]]:
        """
        Get list of countries in the eRegulations system.
        
        Returns:
            List of country information
        """
        endpoint = "Countries"
        try:
            data = await self.make_request(endpoint)
            
            # Notify subscribers about country list updates
            if data:
                await subscriptions.subscription_manager.notify_update(
                    "eregulations://countries",
                    data,
                    mime_type="application/json"
                )
            
            return data or []
        except APIError:
            return []


# Create a global detailed client instance
detailed_client = DetailedERegulationsClient()
