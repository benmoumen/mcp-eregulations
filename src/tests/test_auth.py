"""
Tests for the MCP eRegulations server authentication functionality.
"""
import pytest
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from mcp_eregulations.utils.auth import AuthManager
from mcp_eregulations.utils.middleware import require_auth, require_admin, log_access


class TestAuthManager:
    """Tests for the AuthManager class."""
    
    @pytest.fixture
    def temp_auth_file(self):
        """Create a temporary file for auth data."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"{}")
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def auth_manager(self, temp_auth_file):
        """Create an auth manager instance for testing."""
        return AuthManager(auth_file=temp_auth_file)
    
    def test_init(self, auth_manager):
        """Test that the auth manager is initialized correctly."""
        assert isinstance(auth_manager.users, dict)
        assert isinstance(auth_manager.api_keys, dict)
        assert isinstance(auth_manager.tokens, dict)
    
    def test_hash_password(self, auth_manager):
        """Test password hashing."""
        password = "test_password"
        hashed = auth_manager._hash_password(password)
        
        # Check that the hash is in the expected format
        assert ":" in hashed
        salt, hash_value = hashed.split(":")
        assert len(salt) > 0
        assert len(hash_value) > 0
        
        # Check that the same password with the same salt produces the same hash
        import hashlib
        hash_obj = hashlib.sha256((password + salt).encode())
        assert hash_obj.hexdigest() == hash_value
    
    def test_verify_password(self, auth_manager):
        """Test password verification."""
        password = "test_password"
        hashed = auth_manager._hash_password(password)
        
        # Correct password should verify
        assert auth_manager._verify_password(hashed, password) is True
        
        # Incorrect password should not verify
        assert auth_manager._verify_password(hashed, "wrong_password") is False
        
        # Invalid hash format should not verify
        assert auth_manager._verify_password("invalid_hash", password) is False
    
    def test_generate_token(self, auth_manager):
        """Test token generation."""
        token = auth_manager._generate_token("test_user")
        
        # Check that the token was stored
        assert token in auth_manager.tokens
        assert auth_manager.tokens[token]["username"] == "test_user"
        assert "expiry" in auth_manager.tokens[token]
    
    def test_generate_api_key(self, auth_manager):
        """Test API key generation."""
        api_key = auth_manager._generate_api_key()
        
        # Check that the API key has the expected format
        assert api_key.startswith("mcp-")
        assert len(api_key) > 20
    
    def test_register_user(self, auth_manager):
        """Test user registration."""
        # Register a new user
        result = auth_manager.register_user("test_user", "test_password")
        
        # Check the result
        assert result["success"] is True
        assert "User registered successfully" in result["message"]
        
        # Check that the user was stored
        assert "test_user" in auth_manager.users
        assert "password_hash" in auth_manager.users["test_user"]
        assert "created_at" in auth_manager.users["test_user"]
        assert "api_keys" in auth_manager.users["test_user"]
        
        # Try to register the same user again
        result = auth_manager.register_user("test_user", "another_password")
        
        # Check that registration failed
        assert result["success"] is False
        assert "Username already exists" in result["message"]
    
    def test_authenticate_user(self, auth_manager):
        """Test user authentication."""
        # Register a user
        auth_manager.register_user("test_user", "test_password")
        
        # Authenticate with correct credentials
        result = auth_manager.authenticate_user("test_user", "test_password")
        
        # Check the result
        assert result["success"] is True
        assert "Authentication successful" in result["message"]
        assert "token" in result
        
        # Authenticate with incorrect password
        result = auth_manager.authenticate_user("test_user", "wrong_password")
        
        # Check that authentication failed
        assert result["success"] is False
        assert "Invalid username or password" in result["message"]
        
        # Authenticate with non-existent user
        result = auth_manager.authenticate_user("nonexistent_user", "test_password")
        
        # Check that authentication failed
        assert result["success"] is False
        assert "Invalid username or password" in result["message"]
    
    def test_verify_token(self, auth_manager):
        """Test token verification."""
        # Register and authenticate a user to get a token
        auth_manager.register_user("test_user", "test_password")
        auth_result = auth_manager.authenticate_user("test_user", "test_password")
        token = auth_result["token"]
        
        # Verify the token
        result = auth_manager.verify_token(token)
        
        # Check the result
        assert result["success"] is True
        assert "Token valid" in result["message"]
        assert result["username"] == "test_user"
        
        # Verify a non-existent token
        result = auth_manager.verify_token("nonexistent_token")
        
        # Check that verification failed
        assert result["success"] is False
        assert "Invalid token" in result["message"]
        
        # Test expired token
        import datetime
        # Manually set token to expired
        auth_manager.tokens[token]["expiry"] = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()
        
        # Verify the expired token
        result = auth_manager.verify_token(token)
        
        # Check that verification failed
        assert result["success"] is False
        assert "Token expired" in result["message"]
        
        # Check that the expired token was removed
        assert token not in auth_manager.tokens
    
    def test_create_api_key(self, auth_manager):
        """Test API key creation."""
        # Register a user
        auth_manager.register_user("test_user", "test_password")
        
        # Create an API key
        result = auth_manager.create_api_key("test_user")
        
        # Check the result
        assert result["success"] is True
        assert "API key created successfully" in result["message"]
        assert "api_key" in result
        
        api_key = result["api_key"]
        
        # Check that the API key was stored
        assert api_key in auth_manager.api_keys
        assert auth_manager.api_keys[api_key]["username"] == "test_user"
        assert api_key in auth_manager.users["test_user"]["api_keys"]
        
        # Try to create an API key for a non-existent user
        result = auth_manager.create_api_key("nonexistent_user")
        
        # Check that creation failed
        assert result["success"] is False
        assert "User not found" in result["message"]
    
    def test_verify_api_key(self, auth_manager):
        """Test API key verification."""
        # Register a user and create an API key
        auth_manager.register_user("test_user", "test_password")
        api_key_result = auth_manager.create_api_key("test_user")
        api_key = api_key_result["api_key"]
        
        # Verify the API key
        result = auth_manager.verify_api_key(api_key)
        
        # Check the result
        assert result["success"] is True
        assert "API key valid" in result["message"]
        assert result["username"] == "test_user"
        
        # Verify a non-existent API key
        result = auth_manager.verify_api_key("nonexistent_api_key")
        
        # Check that verification failed
        assert result["success"] is False
        assert "Invalid API key" in result["message"]
    
    def test_revoke_api_key(self, auth_manager):
        """Test API key revocation."""
        # Register a user and create an API key
        auth_manager.register_user("test_user", "test_password")
        api_key_result = auth_manager.create_api_key("test_user")
        api_key = api_key_result["api_key"]
        
        # Revoke the API key
        result = auth_manager.revoke_api_key("test_user", api_key)
        
        # Check the result
        assert result["success"] is True
        assert "API key revoked successfully" in result["message"]
        
        # Check that the API key was removed
        assert api_key not in auth_manager.api_keys
        assert api_key not in auth_manager.users["test_user"]["api_keys"]
        
        # Try to revoke a non-existent API key
        result = auth_manager.revoke_api_key("test_user", "nonexistent_api_key")
        
        # Check that revocation failed
        assert result["success"] is False
        assert "API key not found" in result["message"]
        
        # Try to revoke an API key for a non-existent user
        result = auth_manager.revoke_api_key("nonexistent_user", api_key)
        
        # Check that revocation failed
        assert result["success"] is False
        assert "User not found" in result["message"]
    
    def test_list_api_keys(self, auth_manager):
        """Test listing API keys."""
        # Register a user and create some API keys
        auth_manager.register_user("test_user", "test_password")
        api_key1 = auth_manager.create_api_key("test_user")["api_key"]
        api_key2 = auth_manager.create_api_key("test_user")["api_key"]
        
        # List the API keys
        result = auth_manager.list_api_keys("test_user")
        
        # Check the result
        assert result["success"] is True
        assert "API keys retrieved successfully" in result["message"]
        assert "api_keys" in result
        assert len(result["api_keys"]) == 2
        assert api_key1 in result["api_keys"]
        assert api_key2 in result["api_keys"]
        
        # Try to list API keys for a non-existent user
        result = auth_manager.list_api_keys("nonexistent_user")
        
        # Check that listing failed
        assert result["success"] is False
        assert "User not found" in result["message"]
    
    def test_save_and_load_auth_data(self, auth_manager, temp_auth_file):
        """Test saving and loading auth data."""
        # Register a user and create an API key
        auth_manager.register_user("test_user", "test_password")
        api_key = auth_manager.create_api_key("test_user")["api_key"]
        
        # Save auth data
        auth_manager._save_auth_data()
        
        # Create a new auth manager to load the saved data
        new_auth_manager = AuthManager(auth_file=temp_auth_file)
        
        # Check that data was loaded correctly
        assert "test_user" in new_auth_manager.users
        assert api_key in new_auth_manager.api_keys
        assert new_auth_manager.api_keys[api_key]["username"] == "test_user"
        
        # Check that tokens were not saved (for security reasons)
        assert len(new_auth_manager.tokens) == 0


class TestMiddleware:
    """Tests for the middleware decorators."""
    
    @pytest.fixture
    def mock_auth_manager(self):
        """Create a mock auth manager for testing."""
        with patch("mcp_eregulations.utils.middleware.auth_manager") as mock:
            yield mock
    
    @pytest.mark.asyncio
    async def test_require_auth_decorator_with_valid_api_key(self, mock_auth_manager):
        """Test require_auth decorator with valid API key."""
        # Setup mock
        mock_auth_manager.verify_api_key.return_value = {
            "success": True,
            "message": "API key valid",
            "username": "test_user"
        }
        
        # Create a decorated function
        @require_auth
        async def test_func(param1, param2, api_key=None):
            return f"Result: {param1}, {param2}"
        
        # Call the function with a valid API key
        result = await test_func("value1", "value2", api_key="valid_api_key")
        
        # Check the result
        assert result == "Result: value1, value2"
        mock_auth_manager.verify_api_key.assert_called_once_with("valid_api_key")
    
    @pytest.mark.asyncio
    async def test_require_auth_decorator_without_api_key(self, mock_auth_manager):
        """Test require_auth decorator without API key."""
        # Create a decorated function
        @require_auth
        async def test_func(param1, param2, api_key=None):
            return f"Result: {param1}, {param2}"
        
        # Call the function without an API key
        result = await test_func("value1", "value2")
        
        # Check the result
        assert "Authentication required" in result
        mock_auth_manager.verify_api_key.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_require_auth_decorator_with_invalid_api_key(self, mock_auth_manager):
        """Test require_auth decorator with invalid API key."""
        # Setup mock
        mock_auth_manager.verify_api_key.return_value = {
            "success": False,
            "message": "Invalid API key"
        }
        
        # Create a decorated function
        @require_auth
        async def test_func(param1, param2, api_key=None):
            return f"Result: {param1}, {param2}"
        
        # Call the function with an invalid API key
        result = await test_func("value1", "value2", api_key="invalid_api_key")
        
        # Check the result
        assert "Authentication failed" in result
        assert "Invalid API key" in result
        mock_auth_manager.verify_api_key.assert_called_once_with("invalid_api_key")
    
    @pytest.mark.asyncio
    async def test_require_admin_decorator(self, mock_auth_manager):
        """Test require_admin decorator."""
        # Setup mock for admin user
        mock_auth_manager.verify_api_key.return_value = {
            "success": True,
            "message": "API key valid",
            "username": "admin"  # This matches the hardcoded admin check in the middleware
        }
        
        # Create a decorated function
        @require_admin
        async def test_func(param1, api_key=None):
            return f"Admin result: {param1}"
        
        # Call the function with an admin API key
        result = await test_func("value1", api_key="admin_api_key")
        
        # Check the result
        assert result == "Admin result: value1"
        mock_auth_manager.verify_api_key.assert_called_once_with("admin_api_key")
        
        # Reset mock
        mock_auth_manager.verify_api_key.reset_mock()
        
        # Setup mock for non-admin user
        mock_auth_manager.verify_api_key.return_value = {
            "success": True,
            "message": "API key valid",
            "username": "regular_user"  # This doesn't match the hardcoded admin check
        }
        
        # Call the function with a non-admin API key
        result = await test_func("value1", api_key="user_api_key")
        
        # Check the result
        assert "Admin privileges required" in result
        mock_auth_manager.verify_api_key.assert_called_once_with("user_api_key")
    
    @pytest.mark.asyncio
    @patch("mcp_eregulations.utils.middleware.logger")
    async def test_log_access_decorator(self, mock_logger, mock_auth_manager):
        """Test log_access decorator."""
        # Setup mock
        mock_auth_manager.verify_api_key.return_value = {
            "success": True,
            "message": "API key valid",
            "username": "test_user"
        }
        
        # Create a decorated function
        @log_access
        async def test_func(param1, api_key=None):
            return f"Logged result: {param1}"
        
        # Call the function with an API key
        result = await test_func("value1", api_key="valid_api_key")
        
        # Check the result
        assert result == "Logged result: value1"
        mock_auth_manager.verify_api_key.assert_called_once_with("valid_api_key")
        mock_logger.info.assert_called_once()
        assert "test_func" in mock_logger.info.call_args[0][0]
        assert "test_user" in mock_logger.info.call_args[0][0]
        
        # Reset mocks
        mock_auth_manager.verify_api_key.reset_mock()
        mock_logger.info.reset_mock()
        
        # Call the function without an API key
        result = await test_func("value1")
        
        # Check the result
        assert result == "Logged result: value1"
        mock_auth_manager.verify_api_key.assert_not_called()
        mock_logger.info.assert_called_once()
        assert "test_func" in mock_logger.info.call_args[0][0]
        assert "anonymous" in mock_logger.info.call_args[0][0]
