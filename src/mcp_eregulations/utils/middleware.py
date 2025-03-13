"""
Authentication middleware for the MCP eRegulations server.
"""
from typing import Dict, Optional, Callable, Any
import logging
from functools import wraps

from mcp_eregulations.utils.auth import auth_manager

logger = logging.getLogger(__name__)

def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for MCP tools.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that requires authentication
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract authentication information from context
        # In a real implementation, this would come from the MCP request context
        # For now, we'll use a simplified approach
        
        # Check if API key is provided in the request
        api_key = kwargs.pop("api_key", None)
        
        if not api_key:
            return "Authentication required. Please provide a valid API key."
        
        # Verify the API key
        result = auth_manager.verify_api_key(api_key)
        
        if not result["success"]:
            return f"Authentication failed: {result['message']}"
        
        # Authentication successful, proceed with the function call
        return await func(*args, **kwargs)
    
    return wrapper

def require_admin(func: Callable) -> Callable:
    """
    Decorator to require admin privileges for MCP tools.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that requires admin privileges
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract authentication information from context
        api_key = kwargs.pop("api_key", None)
        
        if not api_key:
            return "Authentication required. Please provide a valid API key."
        
        # Verify the API key
        result = auth_manager.verify_api_key(api_key)
        
        if not result["success"]:
            return f"Authentication failed: {result['message']}"
        
        # Check if the user has admin privileges
        # In a real implementation, this would check against a list of admin users
        # For now, we'll use a simplified approach
        username = result["username"]
        
        # Placeholder for admin check
        is_admin = username == "admin"  # This should be replaced with a proper check
        
        if not is_admin:
            return "Admin privileges required for this operation."
        
        # Authentication and authorization successful, proceed with the function call
        return await func(*args, **kwargs)
    
    return wrapper

def log_access(func: Callable) -> Callable:
    """
    Decorator to log access to MCP tools.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that logs access
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract authentication information from context
        api_key = kwargs.get("api_key")
        
        if api_key:
            result = auth_manager.verify_api_key(api_key)
            username = result.get("username", "unknown") if result.get("success") else "unknown"
        else:
            username = "anonymous"
        
        # Log the access
        logger.info(f"Access to {func.__name__} by {username}")
        
        # Proceed with the function call
        return await func(*args, **kwargs)
    
    return wrapper
