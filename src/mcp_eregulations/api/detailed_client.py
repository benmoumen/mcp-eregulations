"""
Module for handling API integration with the eRegulations platform.
This module extends the basic client with more detailed API interactions.
"""
from typing import Any, Dict, List, Optional
import logging
from mcp_eregulations.api.client import ERegulationsClient, client

logger = logging.getLogger(__name__)

class DetailedERegulationsClient(ERegulationsClient):
    """Extended client for more detailed interactions with the eRegulations API."""
    
    async def get_procedure_detailed(self, procedure_id: int) -> Dict[str, Any]:
        """
        Get comprehensive procedure information by combining multiple API calls.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            A dictionary with comprehensive procedure information
        """
        # Get basic procedure information
        procedure = await self.get_procedure(procedure_id)
        if not procedure:
            return {"error": f"Procedure with ID {procedure_id} not found"}
        
        # Get procedure resume
        resume = await self.get_procedure_resume(procedure_id)
        
        # Get procedure costs
        costs = await self.get_procedure_costs(procedure_id)
        
        # Get procedure requirements
        requirements = await self.get_procedure_requirements(procedure_id)
        
        # Combine all information
        result = {
            "basic_info": procedure,
            "resume": resume,
            "costs": costs,
            "requirements": requirements
        }
        
        return result
    
    async def get_procedure_abc(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the Activity-Based Costing (ABC) information for a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            ABC data for the procedure, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/ABC"
        return await self.make_request(endpoint)
    
    async def get_procedure_abc_full(self, procedure_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the detailed ABC information for a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            
        Returns:
            Detailed ABC data for the procedure, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/ABC/Full"
        return await self.make_request(endpoint)
    
    async def get_step_details(self, procedure_id: int, step_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific step in a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            step_id: The ID of the step
            
        Returns:
            Step details, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/Steps/{step_id}"
        return await self.make_request(endpoint)
    
    async def get_step_abc(self, procedure_id: int, step_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the ABC information for a specific step in a procedure.
        
        Args:
            procedure_id: The ID of the procedure
            step_id: The ID of the step
            
        Returns:
            Step ABC data, or None if not found
        """
        endpoint = f"Procedures/{procedure_id}/Steps/{step_id}/ABC"
        return await self.make_request(endpoint)
    
    async def get_countries(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get the list of countries available in the eRegulations system.
        
        Returns:
            List of countries, or None if the request failed
        """
        endpoint = "Country"
        return await self.make_request(endpoint)
    
    async def get_country_parameters(self, country_id: int) -> Optional[Dict[str, Any]]:
        """
        Get parameters for a specific country.
        
        Args:
            country_id: The ID of the country
            
        Returns:
            Country parameters, or None if not found
        """
        endpoint = f"CountryParameters/{country_id}"
        return await self.make_request(endpoint)
    
    async def get_institutions(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get the list of institutions (units) in the eRegulations system.
        
        Returns:
            List of institutions, or None if the request failed
        """
        endpoint = "Unit"
        return await self.make_request(endpoint)
    
    async def get_institution_details(self, institution_id: int) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific institution.
        
        Args:
            institution_id: The ID of the institution
            
        Returns:
            Institution details, or None if not found
        """
        endpoint = f"Unit/{institution_id}"
        return await self.make_request(endpoint)

# Create a global detailed client instance
detailed_client = DetailedERegulationsClient()
