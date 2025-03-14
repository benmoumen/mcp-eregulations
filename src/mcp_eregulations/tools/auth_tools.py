"""
Secure MCP tools for managing authentication and API keys.
"""
import logging
from typing import Any, Dict, Optional

from mcp.server.fastmcp import Context, FastMCP

from mcp_eregulations.utils.auth import auth_manager
from mcp_eregulations.utils.middleware import log_access, require_admin, require_auth

logger = logging.getLogger(__name__)


def register_tools(mcp: FastMCP) -> None:
    """Register all authentication tools with the MCP server instance."""
    
    @mcp.tool()
    @log_access
    async def register_user(username: str, password: str) -> str:
        """
        Register a new user for the MCP eRegulations server.
        
        Args:
            username: The username for the new user
            password: The password for the new user
            
        Returns:
            Result of the registration
        """
        logger.debug(f"Registering new user: {username}")
        result = auth_manager.register_user(username, password)
        
        if result["success"]:
            return f"User '{username}' registered successfully."
        else:
            return f"Registration failed: {result['message']}"
    
    @mcp.tool()
    @log_access
    async def authenticate_user(username: str, password: str) -> str:
        """
        Authenticate a user and get an authentication token.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            Authentication result with token if successful
        """
        logger.debug(f"Authenticating user: {username}")
        result = auth_manager.authenticate_user(username, password)
        
        if result["success"]:
            return f"Authentication successful. Token: {result['token']}"
        else:
            return f"Authentication failed: {result['message']}"
    
    @mcp.tool()
    @require_auth
    @log_access
    async def create_api_key(username: str, api_key: Optional[str] = None) -> str:
        """
        Create a new API key for a user.
        
        Args:
            username: The username
            api_key: The API key for authentication (required)
            
        Returns:
            Result with API key if successful
        """
        logger.debug(f"Creating API key for user: {username}")
        result = auth_manager.create_api_key(username)
        
        if result["success"]:
            return f"API key created successfully: {result['api_key']}"
        else:
            return f"API key creation failed: {result['message']}"
    
    @mcp.tool()
    @require_auth
    @log_access
    async def list_api_keys(username: str, api_key: Optional[str] = None) -> str:
        """
        List API keys for a user.
        
        Args:
            username: The username
            api_key: The API key for authentication (required)
            
        Returns:
            List of API keys
        """
        logger.debug(f"Listing API keys for user: {username}")
        result = auth_manager.list_api_keys(username)
        
        if result["success"]:
            api_keys = result["api_keys"]
            if api_keys:
                output = f"API keys for user '{username}':\n\n"
                for i, key in enumerate(api_keys, 1):
                    output += f"{i}. {key}\n"
                return output
            else:
                return f"No API keys found for user '{username}'."
        else:
            return f"Failed to list API keys: {result['message']}"
    
    @mcp.tool()
    @require_auth
    @log_access
    async def revoke_api_key(username: str, target_api_key: str, api_key: Optional[str] = None) -> str:
        """
        Revoke an API key.
        
        Args:
            username: The username
            target_api_key: The API key to revoke
            api_key: The API key for authentication (required)
            
        Returns:
            Result of the revocation
        """
        logger.debug(f"Revoking API key for user: {username}")
        result = auth_manager.revoke_api_key(username, target_api_key)
        
        if result["success"]:
            return f"API key revoked successfully."
        else:
            return f"Failed to revoke API key: {result['message']}"
    
    @mcp.tool()
    @require_admin
    @log_access
    async def admin_list_users(api_key: Optional[str] = None) -> str:
        """
        List all users (admin only).
        
        Args:
            api_key: The API key for authentication (required)
            
        Returns:
            List of users
        """
        logger.debug("Admin listing all users")
        users = auth_manager.users
        
        if users:
            output = "Registered users:\n\n"
            for i, (username, user_data) in enumerate(users.items(), 1):
                created_at = user_data.get("created_at", "Unknown")
                api_key_count = len(user_data.get("api_keys", []))
                output += f"{i}. {username}\n"
                output += f"   Created: {created_at}\n"
                output += f"   API Keys: {api_key_count}\n\n"
            return output
        else:
            return "No users registered."
