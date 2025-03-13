"""
Query handling and response generation for eRegulations data.
"""
from typing import Dict, List, Optional, Any
import logging
import re

from mcp_eregulations.api.detailed_client import detailed_client
from mcp_eregulations.utils.indexing import index

logger = logging.getLogger(__name__)

class QueryHandler:
    """Class for handling user queries and generating responses."""
    
    def __init__(self):
        """Initialize the query handler."""
        # Define patterns for recognizing different types of queries
        self.patterns = {
            "procedure_id": r"procedure(?:\s+with)?\s+id\s+(\d+)",
            "procedure_steps": r"steps\s+(?:for|of)\s+procedure\s+(?:with\s+id\s+)?(\d+)",
            "procedure_requirements": r"requirements\s+(?:for|of)\s+procedure\s+(?:with\s+id\s+)?(\d+)",
            "procedure_costs": r"costs?\s+(?:for|of)\s+procedure\s+(?:with\s+id\s+)?(\d+)",
            "search_keyword": r"search\s+(?:for\s+)?(?:procedures?\s+)?(?:with\s+)?(?:keyword\s+)?['\"]?([^'\"]+)['\"]?",
            "institution_info": r"institution\s+(?:with\s+id\s+)?(\d+)",
        }
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query and determine the appropriate action.
        
        Args:
            query: The user query
            
        Returns:
            A dictionary with the query type, parameters, and suggested tool
        """
        query = query.lower().strip()
        
        # Check for procedure ID pattern
        match = re.search(self.patterns["procedure_id"], query)
        if match:
            procedure_id = int(match.group(1))
            return {
                "type": "procedure_info",
                "parameters": {"procedure_id": procedure_id},
                "suggested_tool": "get_procedure",
                "confidence": 0.9
            }
        
        # Check for procedure steps pattern
        match = re.search(self.patterns["procedure_steps"], query)
        if match:
            procedure_id = int(match.group(1))
            return {
                "type": "procedure_steps",
                "parameters": {"procedure_id": procedure_id},
                "suggested_tool": "get_procedure_steps",
                "confidence": 0.9
            }
        
        # Check for procedure requirements pattern
        match = re.search(self.patterns["procedure_requirements"], query)
        if match:
            procedure_id = int(match.group(1))
            return {
                "type": "procedure_requirements",
                "parameters": {"procedure_id": procedure_id},
                "suggested_tool": "get_procedure_requirements",
                "confidence": 0.9
            }
        
        # Check for procedure costs pattern
        match = re.search(self.patterns["procedure_costs"], query)
        if match:
            procedure_id = int(match.group(1))
            return {
                "type": "procedure_costs",
                "parameters": {"procedure_id": procedure_id},
                "suggested_tool": "get_procedure_costs",
                "confidence": 0.9
            }
        
        # Check for search keyword pattern
        match = re.search(self.patterns["search_keyword"], query)
        if match:
            keyword = match.group(1).strip()
            return {
                "type": "search",
                "parameters": {"query": keyword, "limit": 5},
                "suggested_tool": "search_procedures_by_keyword",
                "confidence": 0.8
            }
        
        # Check for institution info pattern
        match = re.search(self.patterns["institution_info"], query)
        if match:
            institution_id = int(match.group(1))
            return {
                "type": "institution_info",
                "parameters": {"institution_id": institution_id},
                "suggested_tool": "get_institution_info",
                "confidence": 0.9
            }
        
        # If no specific pattern matches, treat as a general search
        # Extract potential keywords
        keywords = self._extract_keywords(query)
        if keywords:
            return {
                "type": "search",
                "parameters": {"query": " ".join(keywords), "limit": 5},
                "suggested_tool": "search_procedures_by_keyword",
                "confidence": 0.6
            }
        
        # If all else fails, return a fallback response
        return {
            "type": "unknown",
            "parameters": {},
            "suggested_tool": None,
            "confidence": 0.0,
            "message": "I couldn't understand your query. Please try asking about a specific procedure, steps, requirements, costs, or search for procedures using keywords."
        }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract potential keywords from a query.
        
        Args:
            query: The user query
            
        Returns:
            List of potential keywords
        """
        # Remove common stop words
        stop_words = {
            "a", "about", "an", "and", "are", "as", "at", "be", "by", "for",
            "from", "how", "i", "in", "is", "it", "of", "on", "or", "that",
            "the", "this", "to", "was", "what", "when", "where", "who", "will",
            "with", "the", "procedure", "procedures", "step", "steps", "requirement",
            "requirements", "cost", "costs", "information", "info", "detail",
            "details", "tell", "me", "show", "get", "find", "search", "looking"
        }
        
        # Tokenize and filter
        words = query.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords

    async def generate_response(self, query_result: Dict[str, Any]) -> str:
        """
        Generate a response based on the query result.
        
        Args:
            query_result: The result from process_query
            
        Returns:
            A formatted response string
        """
        query_type = query_result.get("type")
        parameters = query_result.get("parameters", {})
        suggested_tool = query_result.get("suggested_tool")
        confidence = query_result.get("confidence", 0.0)
        
        # If confidence is too low, return the fallback message
        if confidence < 0.5:
            return query_result.get("message", "I couldn't understand your query. Please try again.")
        
        # Handle different query types
        if query_type == "procedure_info":
            procedure_id = parameters.get("procedure_id")
            # Try to get from index first
            procedure_data = index.get_procedure(procedure_id)
            if not procedure_data:
                # If not in index, fetch from API
                procedure_data = await detailed_client.get_procedure(procedure_id)
                if procedure_data:
                    # Index for future use
                    index.index_procedure(procedure_id, procedure_data)
            
            if procedure_data:
                title = procedure_data.get("title", f"Procedure {procedure_id}")
                description = procedure_data.get("description", "No description available")
                
                response = f"# {title}\n\n"
                response += f"{description}\n\n"
                
                # Add additional information if available
                additional_info = procedure_data.get("additionalInfo")
                if additional_info:
                    response += f"## Additional Information\n{additional_info}\n\n"
                
                # Add information about steps
                blocks = procedure_data.get("blocks", [])
                step_count = sum(len(block.get("steps", [])) for block in blocks)
                response += f"This procedure consists of {step_count} steps across {len(blocks)} blocks.\n"
                response += "You can get detailed information about the steps using the get_procedure_steps tool.\n\n"
                
                return response
            else:
                return f"I couldn't find information for procedure with ID {procedure_id}."
        
        elif query_type == "search":
            # For search queries, we'll defer to the search tool
            return f"Searching for procedures related to '{parameters.get('query')}'..."
        
        elif query_type == "unknown":
            return "I'm not sure what you're asking for. Could you please rephrase your question or provide more specific details?"
        
        # For other query types, we'll provide a generic response
        return f"I'll help you find information about {query_type.replace('_', ' ')}."

# Create a global query handler instance
query_handler = QueryHandler()
