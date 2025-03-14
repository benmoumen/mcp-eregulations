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
            "procedure_requirements": r"requirements\s+(?:for|of)\s+procedure\s+(?:with\s+id\s+)?(\d+)",
            "procedure_steps": r"steps\s+(?:for|of)\s+procedure\s+(?:with\s+id\s+)?(\d+)",
            "procedure_costs": r"costs?\s+(?:for|of)\s+procedure\s+(?:with\s+id\s+)?(\d+)",
            "procedure_id": r"procedure(?:\s+with)?\s+id\s+(\d+)",
            "search_keyword": r"search\s+(?:for\s+)?(?:procedures?\s+)?(?:with\s+)?(?:keyword\s+)?['\"]?([^'\"]+)['\"]?",
            "institution_info": r"institution\s+(?:with\s+id\s+)?(\d+)",
        }
        
        # Map pattern types to response types and tools
        self.type_mappings = {
            "procedure_id": ("procedure_info", "get_procedure"),
            "procedure_steps": ("procedure_steps", "get_procedure_steps"),
            "procedure_requirements": ("procedure_requirements", "get_procedure_requirements"),
            "procedure_costs": ("procedure_costs", "get_procedure_costs"),
            "search_keyword": ("search", "search_procedures_by_keyword"),
            "institution_info": ("institution_info", "get_institution_info"),
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
        
        # Check for specific patterns in order of specificity
        for pattern_type, pattern in self.patterns.items():
            match = re.search(pattern, query)
            if match:
                value = match.group(1)
                response_type, tool = self.type_mappings[pattern_type]
                
                # Convert value to int for procedure and institution IDs
                if "procedure" in pattern_type or pattern_type == "institution_info":
                    value = int(value)
                
                # Determine parameter name based on type
                param_name = "procedure_id" if "procedure" in pattern_type else "institution_id" if pattern_type == "institution_info" else "query"
                
                return {
                    "type": response_type,
                    "parameters": {
                        param_name: value,
                        **({"limit": 5} if pattern_type == "search_keyword" else {})
                    },
                    "suggested_tool": tool,
                    "confidence": 0.9 if pattern_type != "search_keyword" else 0.8
                }
        
        # Check for general search terms and business-related keywords
        search_terms = ["how to", "where to", "find a", "search for", "looking for", "information about", "related to"]
        business_terms = ["register", "business", "company", "permit", "license", "trade", "import", "export"]
        
        if (any(term in query for term in search_terms) or 
            any(term in query for term in business_terms)):
            keywords = self._extract_keywords(query)
            if keywords:
                return {
                    "type": "search",
                    "parameters": {"query": " ".join(keywords), "limit": 5},
                    "suggested_tool": "search_procedures_by_keyword",
                    "confidence": 0.6
                }
        
        # If no patterns match, return unknown
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
        # Remove common stop words and question words
        stop_words = {
            "a", "about", "an", "and", "are", "as", "at", "be", "by", "for",
            "from", "how", "i", "in", "is", "it", "of", "on", "or", "that",
            "the", "this", "to", "was", "what", "when", "where", "who", "will",
            "with", "procedure", "procedures", "step", "steps", "requirement",
            "requirements", "cost", "costs", "information", "info", "detail",
            "details", "tell", "me", "show", "get", "find", "search", "looking",
            "which", "why", "can", "could", "would", "should", "do", "does",
            "meaning", "life", "want", "need", "help", "please"
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
