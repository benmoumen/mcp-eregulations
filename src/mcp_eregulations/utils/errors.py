"""
Custom exception classes for MCP eRegulations server.
"""
from typing import Any, Dict, Optional


class MCPError(Exception):
    """Base class for MCP-specific exceptions."""

    def __init__(self, message: str, code: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        """
        Initialize MCP error.
        
        Args:
            message: Error message
            code: Optional error code
            data: Optional error data
        """
        super().__init__(message)
        self.code = code or "UNKNOWN_ERROR"
        self.data = data or {}


class ResourceNotFoundError(MCPError):
    """Error raised when a requested resource is not found."""

    def __init__(self, resource_id: str, message: Optional[str] = None):
        """
        Initialize resource not found error.
        
        Args:
            resource_id: ID of the resource that wasn't found
            message: Optional custom error message
        """
        super().__init__(
            message or f"Resource not found: {resource_id}",
            code="RESOURCE_NOT_FOUND",
            data={"resource_id": resource_id}
        )


class InvalidArgumentError(MCPError):
    """Error raised when an invalid argument is provided."""

    def __init__(self, argument: str, message: Optional[str] = None, value: Any = None):
        """
        Initialize invalid argument error.
        
        Args:
            argument: Name of the invalid argument
            message: Optional custom error message
            value: Optional invalid value that was provided
        """
        super().__init__(
            message or f"Invalid argument: {argument}",
            code="INVALID_ARGUMENT",
            data={
                "argument": argument,
                "value": str(value) if value is not None else None
            }
        )


class AuthenticationError(MCPError):
    """Error raised when authentication fails."""

    def __init__(self, message: Optional[str] = None):
        """Initialize authentication error."""
        super().__init__(
            message or "Authentication failed",
            code="AUTHENTICATION_FAILED"
        )


class AuthorizationError(MCPError):
    """Error raised when a user is not authorized to perform an action."""

    def __init__(self, action: str, message: Optional[str] = None):
        """
        Initialize authorization error.
        
        Args:
            action: The action that was not authorized
            message: Optional custom error message
        """
        super().__init__(
            message or f"Not authorized to perform action: {action}",
            code="AUTHORIZATION_FAILED",
            data={"action": action}
        )


class APIError(MCPError):
    """Error raised when there's a problem with the eRegulations API."""

    def __init__(self, status_code: int, message: Optional[str] = None, endpoint: Optional[str] = None):
        """
        Initialize API error.
        
        Args:
            status_code: HTTP status code from the API
            message: Optional custom error message
            endpoint: Optional API endpoint that failed
        """
        super().__init__(
            message or f"API error: {status_code}",
            code="API_ERROR",
            data={
                "status_code": status_code,
                "endpoint": endpoint
            }
        )


class IndexError(MCPError):
    """Error raised when there's a problem with the search index."""

    def __init__(self, operation: str, message: Optional[str] = None):
        """
        Initialize index error.
        
        Args:
            operation: The indexing operation that failed
            message: Optional custom error message
        """
        super().__init__(
            message or f"Index operation failed: {operation}",
            code="INDEX_ERROR",
            data={"operation": operation}
        )


class RateLimitError(MCPError):
    """Error raised when rate limits are exceeded."""

    def __init__(self, limit: int, reset_after: int, message: Optional[str] = None):
        """
        Initialize rate limit error.
        
        Args:
            limit: The rate limit that was exceeded
            reset_after: Seconds until the limit resets
            message: Optional custom error message
        """
        super().__init__(
            message or f"Rate limit exceeded. Try again in {reset_after} seconds.",
            code="RATE_LIMIT_EXCEEDED",
            data={
                "limit": limit,
                "reset_after": reset_after
            }
        )