"""Tests for MCP configuration validation."""
import pytest
from mcp_eregulations.config.validation import (
    validate_mcp_settings,
    get_mcp_environment_warnings,
    apply_mcp_environment_overrides,
    ConfigurationError
)

# Valid test settings
VALID_SETTINGS = {
    "MCP_SERVER_NAME": "test-server",
    "MCP_SERVER_PORT": 8000,
    "MCP_HOST": "localhost",
    "MCP_TRANSPORT": "auto",
    "MCP_LOG_LEVEL": "INFO"
}

def test_validate_valid_settings():
    """Test validation of valid settings."""
    is_valid, errors = validate_mcp_settings(VALID_SETTINGS)
    assert is_valid
    assert errors is None

def test_validate_invalid_server_name():
    """Test validation of invalid server name."""
    settings = VALID_SETTINGS.copy()
    settings["MCP_SERVER_NAME"] = "invalid server!"
    is_valid, errors = validate_mcp_settings(settings)
    assert not is_valid
    assert len(errors) == 1
    assert "MCP_SERVER_NAME" in errors[0]

def test_validate_invalid_port():
    """Test validation of invalid port number."""
    settings = VALID_SETTINGS.copy()
    settings["MCP_SERVER_PORT"] = 80  # Privileged port
    is_valid, errors = validate_mcp_settings(settings)
    assert not is_valid
    assert len(errors) == 1
    assert "must be greater than 1024" in errors[0]

def test_validate_invalid_host():
    """Test validation of invalid host."""
    settings = VALID_SETTINGS.copy()
    settings["MCP_HOST"] = "invalid-host"
    is_valid, errors = validate_mcp_settings(settings)
    assert not is_valid
    assert len(errors) == 1
    assert "MCP_HOST" in errors[0]

def test_validate_invalid_transport():
    """Test validation of invalid transport."""
    settings = VALID_SETTINGS.copy()
    settings["MCP_TRANSPORT"] = "invalid"
    is_valid, errors = validate_mcp_settings(settings)
    assert not is_valid
    assert len(errors) == 1
    assert "MCP_TRANSPORT" in errors[0]

def test_validate_missing_required():
    """Test validation of missing required settings."""
    settings = VALID_SETTINGS.copy()
    del settings["MCP_SERVER_NAME"]
    is_valid, errors = validate_mcp_settings(settings)
    assert not is_valid
    assert len(errors) == 1
    assert "MCP_SERVER_NAME" in errors[0]

def test_environment_warnings():
    """Test environment warning detection."""
    settings = VALID_SETTINGS.copy()
    settings.update({
        "MCP_LOG_LEVEL": "DEBUG",
        "DEBUG": False,
        "MCP_HOST": "0.0.0.0",
        "MCP_MAX_REQUEST_SIZE": 60 * 1024 * 1024,
        "MCP_SUBSCRIPTION_MAX_CLIENTS": 600,
        "MCP_COMPLETION_TIMEOUT": 15,
        "MCP_SUBSCRIPTION_TIMEOUT": 5
    })
    
    warnings = get_mcp_environment_warnings(settings)
    assert len(warnings) == 6
    assert any("DEBUG log level" in w for w in warnings)
    assert any("listen on all interfaces" in w for w in warnings)
    assert any("MAX_REQUEST_SIZE" in w for w in warnings)
    assert any("SUBSCRIPTION_MAX_CLIENTS" in w for w in warnings)
    assert any("COMPLETION_TIMEOUT" in w for w in warnings)
    assert any("SUBSCRIPTION_TIMEOUT" in w for w in warnings)

def test_environment_overrides():
    """Test environment-specific overrides."""
    # Test production overrides
    prod_settings = VALID_SETTINGS.copy()
    prod_settings["DEBUG"] = False
    
    prod_result = apply_mcp_environment_overrides(prod_settings)
    assert prod_result["MCP_LOG_LEVEL"] == "INFO"
    assert prod_result["MCP_MAX_REQUEST_SIZE"] == 10 * 1024 * 1024
    assert prod_result["MCP_COMPLETION_TIMEOUT"] == 5
    assert prod_result["MCP_SUBSCRIPTION_TIMEOUT"] == 30
    
    # Test development overrides
    dev_settings = VALID_SETTINGS.copy()
    dev_settings["DEBUG"] = True
    
    dev_result = apply_mcp_environment_overrides(dev_settings)
    assert dev_result["MCP_LOG_LEVEL"] == "DEBUG"
    assert dev_result["MCP_MAX_REQUEST_SIZE"] == 50 * 1024 * 1024
    assert dev_result["MCP_COMPLETION_TIMEOUT"] == 10
    assert dev_result["MCP_SUBSCRIPTION_TIMEOUT"] == 60