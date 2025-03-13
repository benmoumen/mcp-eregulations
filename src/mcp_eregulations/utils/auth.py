"""
Authentication and security for the MCP eRegulations server.
"""
from typing import Dict, Optional, List, Any
import os
import json
import logging
import time
import hashlib
import secrets
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AuthManager:
    """Class for managing authentication and security."""
    
    def __init__(self, auth_file: str = "/home/ubuntu/mcp-eregulations/data/auth/auth.json"):
        """
        Initialize the authentication manager.
        
        Args:
            auth_file: Path to the authentication file
        """
        self.auth_file = auth_file
        self.users = {}
        self.api_keys = {}
        self.tokens = {}
        
        # Create auth directory if it doesn't exist
        os.makedirs(os.path.dirname(self.auth_file), exist_ok=True)
        
        # Load existing auth data if available
        self._load_auth_data()
    
    def _load_auth_data(self):
        """Load authentication data from file."""
        try:
            if os.path.exists(self.auth_file):
                with open(self.auth_file, "r") as f:
                    data = json.load(f)
                    self.users = data.get("users", {})
                    self.api_keys = data.get("api_keys", {})
                    # Don't load tokens from file for security reasons
                    logger.info("Loaded authentication data from file")
        except Exception as e:
            logger.error(f"Error loading authentication data: {e}")
    
    def _save_auth_data(self):
        """Save authentication data to file."""
        try:
            data = {
                "users": self.users,
                "api_keys": self.api_keys
                # Don't save tokens to file for security reasons
            }
            
            with open(self.auth_file, "w") as f:
                json.dump(data, f, indent=2)
                
            logger.info("Saved authentication data to file")
        except Exception as e:
            logger.error(f"Error saving authentication data: {e}")
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password using a secure algorithm.
        
        Args:
            password: The password to hash
            
        Returns:
            The hashed password
        """
        # In a production environment, use a proper password hashing library
        # like bcrypt or Argon2. This is a simplified implementation.
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((password + salt).encode())
        return f"{salt}:{hash_obj.hexdigest()}"
    
    def _verify_password(self, stored_hash: str, password: str) -> bool:
        """
        Verify a password against a stored hash.
        
        Args:
            stored_hash: The stored password hash
            password: The password to verify
            
        Returns:
            True if the password matches, False otherwise
        """
        try:
            salt, hash_value = stored_hash.split(":")
            hash_obj = hashlib.sha256((password + salt).encode())
            return hash_obj.hexdigest() == hash_value
        except Exception:
            return False
    
    def _generate_token(self, username: str) -> str:
        """
        Generate an authentication token for a user.
        
        Args:
            username: The username
            
        Returns:
            The authentication token
        """
        token = secrets.token_hex(32)
        expiry = datetime.now() + timedelta(hours=24)
        
        self.tokens[token] = {
            "username": username,
            "expiry": expiry.isoformat()
        }
        
        return token
    
    def _generate_api_key(self) -> str:
        """
        Generate a new API key.
        
        Returns:
            The API key
        """
        return f"mcp-{secrets.token_hex(16)}"
    
    def register_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            Result of the registration
        """
        if username in self.users:
            return {"success": False, "message": "Username already exists"}
        
        # Hash the password
        password_hash = self._hash_password(password)
        
        # Create the user
        self.users[username] = {
            "password_hash": password_hash,
            "created_at": datetime.now().isoformat(),
            "api_keys": []
        }
        
        # Save the updated auth data
        self._save_auth_data()
        
        return {"success": True, "message": "User registered successfully"}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            Authentication result with token if successful
        """
        if username not in self.users:
            return {"success": False, "message": "Invalid username or password"}
        
        user = self.users[username]
        
        if not self._verify_password(user["password_hash"], password):
            return {"success": False, "message": "Invalid username or password"}
        
        # Generate a token
        token = self._generate_token(username)
        
        return {
            "success": True,
            "message": "Authentication successful",
            "token": token
        }
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify an authentication token.
        
        Args:
            token: The authentication token
            
        Returns:
            Verification result with username if successful
        """
        if token not in self.tokens:
            return {"success": False, "message": "Invalid token"}
        
        token_data = self.tokens[token]
        expiry = datetime.fromisoformat(token_data["expiry"])
        
        if datetime.now() > expiry:
            # Token has expired, remove it
            del self.tokens[token]
            return {"success": False, "message": "Token expired"}
        
        return {
            "success": True,
            "message": "Token valid",
            "username": token_data["username"]
        }
    
    def create_api_key(self, username: str) -> Dict[str, Any]:
        """
        Create a new API key for a user.
        
        Args:
            username: The username
            
        Returns:
            Result with API key if successful
        """
        if username not in self.users:
            return {"success": False, "message": "User not found"}
        
        # Generate a new API key
        api_key = self._generate_api_key()
        
        # Store the API key
        self.api_keys[api_key] = {
            "username": username,
            "created_at": datetime.now().isoformat()
        }
        
        # Add the API key to the user's list
        self.users[username]["api_keys"].append(api_key)
        
        # Save the updated auth data
        self._save_auth_data()
        
        return {
            "success": True,
            "message": "API key created successfully",
            "api_key": api_key
        }
    
    def verify_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Verify an API key.
        
        Args:
            api_key: The API key
            
        Returns:
            Verification result with username if successful
        """
        if api_key not in self.api_keys:
            return {"success": False, "message": "Invalid API key"}
        
        api_key_data = self.api_keys[api_key]
        
        return {
            "success": True,
            "message": "API key valid",
            "username": api_key_data["username"]
        }
    
    def revoke_api_key(self, username: str, api_key: str) -> Dict[str, Any]:
        """
        Revoke an API key.
        
        Args:
            username: The username
            api_key: The API key to revoke
            
        Returns:
            Result of the revocation
        """
        if username not in self.users:
            return {"success": False, "message": "User not found"}
        
        if api_key not in self.api_keys:
            return {"success": False, "message": "API key not found"}
        
        api_key_data = self.api_keys[api_key]
        
        if api_key_data["username"] != username:
            return {"success": False, "message": "API key does not belong to user"}
        
        # Remove the API key
        del self.api_keys[api_key]
        
        # Remove the API key from the user's list
        self.users[username]["api_keys"].remove(api_key)
        
        # Save the updated auth data
        self._save_auth_data()
        
        return {"success": True, "message": "API key revoked successfully"}
    
    def list_api_keys(self, username: str) -> Dict[str, Any]:
        """
        List API keys for a user.
        
        Args:
            username: The username
            
        Returns:
            List of API keys
        """
        if username not in self.users:
            return {"success": False, "message": "User not found"}
        
        api_keys = self.users[username]["api_keys"]
        
        return {
            "success": True,
            "message": "API keys retrieved successfully",
            "api_keys": api_keys
        }

# Create a global auth manager instance
auth_manager = AuthManager()
