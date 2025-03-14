"""
Configuration validation for MCP server settings.
"""
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, validator
from mcp_eregulations.utils.errors import ConfigurationError


class MCPValidationSettings(BaseModel):
    """MCP-specific validation settings."""
    
    # Required MCP settings validation
    MCP_SERVER_NAME: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern="^[a-zA-Z0-9-_]+$"
    )
    
    MCP_SERVER_PORT: int = Field(
        ...,
        ge=1024,
        le=65535
    )
    
    MCP_HOST: str = Field(
        ...,
        pattern="^[0-9.]+$|^localhost$"
    )
    
    MCP_TRANSPORT: str = Field(
        ...,
        pattern="^(auto|stdio|sse)$"
    )
    
    MCP_LOG_LEVEL: str = Field(
        ...,
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
    
    # Optional settings with defaults
    MCP_MAX_REQUEST_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024 * 1024,  # 1MB
        le=100 * 1024 * 1024  # 100MB
    )
    
    MCP_COMPLETION_TIMEOUT: int = Field(
        default=5,
        ge=1,
        le=30
    )
    
    MCP_SUBSCRIPTION_MAX_CLIENTS: int = Field(
        default=100,
        ge=1,
        le=1000
    )
    
    MCP_SUBSCRIPTION_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=300
    )
    
    @validator("MCP_SERVER_NAME")
    def validate_server_name(cls, v: str) -> str:
        """Validate server name format."""
        if not v.strip():
            raise ConfigurationError("MCP_SERVER_NAME cannot be empty")
        return v
    
    @validator("MCP_SERVER_PORT")
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if v < 1024:
            raise ConfigurationError(
                "MCP_SERVER_PORT must be greater than 1024 (non-privileged port)"
            )
        return v
    
    @validator("MCP_HOST")
    def validate_host(cls, v: str) -> str:
        """Validate host format."""
        if v != "localhost" and not all(
            part.isdigit() and 0 <= int(part) <= 255
            for part in v.split(".")
        ):
            raise ConfigurationError(
                "MCP_HOST must be 'localhost' or a valid IPv4 address"
            )
        return v
    
    @validator("MCP_TRANSPORT")
    def validate_transport(cls, v: str) -> str:
        """Validate transport type."""
        valid_transports = {"auto", "stdio", "sse"}
        if v not in valid_transports:
            raise ConfigurationError(
                f"MCP_TRANSPORT must be one of: {', '.join(valid_transports)}"
            )
        return v


def validate_mcp_settings(settings: dict) -> Tuple[bool, Optional[List[str]]]:
    """
    Validate MCP-specific settings.
    
    Args:
        settings: Dictionary of configuration settings
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    try:
        MCPValidationSettings(**settings)
        return True, None
    except ConfigurationError as e:
        return False, [str(e)]
    except Exception as e:
        return False, [f"Validation error: {str(e)}"]


def get_mcp_environment_warnings(settings: Dict) -> List[str]:
    """
    Check for potential issues in MCP environment configuration.
    
    Args:
        settings: Dictionary of configuration settings
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    # Check for development settings in production
    if settings.get("MCP_LOG_LEVEL") == "DEBUG" and not settings.get("DEBUG", False):
        warnings.append(
            "DEBUG log level is set in a non-debug environment"
        )
    
    # Check for potentially insecure settings
    if settings.get("MCP_HOST") == "0.0.0.0":
        warnings.append(
            "MCP server is configured to listen on all interfaces (0.0.0.0)"
        )
    
    # Check for resource limits
    if settings.get("MCP_MAX_REQUEST_SIZE", 0) > 50 * 1024 * 1024:
        warnings.append(
            "MCP_MAX_REQUEST_SIZE is set above 50MB, which may impact performance"
        )
    
    if settings.get("MCP_SUBSCRIPTION_MAX_CLIENTS", 0) > 500:
        warnings.append(
            "High MCP_SUBSCRIPTION_MAX_CLIENTS may impact server performance"
        )
    
    # Check for timeout configurations
    if settings.get("MCP_COMPLETION_TIMEOUT", 0) > 10:
        warnings.append(
            "Long MCP_COMPLETION_TIMEOUT may lead to client timeouts"
        )
    
    if settings.get("MCP_SUBSCRIPTION_TIMEOUT", 0) < 10:
        warnings.append(
            "Short MCP_SUBSCRIPTION_TIMEOUT may cause frequent reconnections"
        )
    
    return warnings


def apply_mcp_environment_overrides(settings: Dict) -> Dict:
    """
    Apply environment-specific overrides to MCP settings.
    
    Args:
        settings: Dictionary of configuration settings
        
    Returns:
        Dictionary of settings with overrides applied
    """
    # Production overrides
    if not settings.get("DEBUG", False):
        settings.update({
            "MCP_LOG_LEVEL": "INFO",
            "MCP_MAX_REQUEST_SIZE": 10 * 1024 * 1024,  # 10MB
            "MCP_COMPLETION_TIMEOUT": 5,
            "MCP_SUBSCRIPTION_TIMEOUT": 30
        })
    
    # Development overrides
    else:
        settings.update({
            "MCP_LOG_LEVEL": "DEBUG",
            "MCP_MAX_REQUEST_SIZE": 50 * 1024 * 1024,  # 50MB
            "MCP_COMPLETION_TIMEOUT": 10,
            "MCP_SUBSCRIPTION_TIMEOUT": 60
        })
    
    return settings