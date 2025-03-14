"""
Configuration settings for the MCP eRegulations server.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings model."""
    
    # MCP Server Configuration
    MCP_SERVER_NAME: str = "eregulations"
    MCP_SERVER_PORT: int = 8000
    MCP_HOST: str = "0.0.0.0"
    MCP_TRANSPORT: str = "auto"  # "auto", "stdio", or "sse"
    MCP_LOG_LEVEL: str = "INFO"
    MCP_MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    MCP_COMPLETION_TIMEOUT: int = 5  # seconds
    MCP_SUBSCRIPTION_MAX_CLIENTS: int = 100
    MCP_SUBSCRIPTION_TIMEOUT: int = 30  # seconds
    
    # eRegulations API Configuration
    EREGULATIONS_API_URL: str = "https://api.eregulations.org"
    EREGULATIONS_API_VERSION: str = "v1"
    EREGULATIONS_API_KEY: Optional[str] = None
    
    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_MAX_SIZE: int = 1000  # items
    
    # Search Index Configuration
    INDEX_DIR: str = "data/index"
    INDEX_UPDATE_INTERVAL: int = 300  # 5 minutes
    
    # Authentication Configuration
    AUTH_ENABLED: bool = True
    AUTH_TOKEN_EXPIRY: int = 86400  # 24 hours
    AUTH_DATA_DIR: str = "data/auth"
    
    # Monitoring Configuration
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # 1 minute
    
    # HTTP Client Configuration
    HTTP_TIMEOUT: float = 30.0
    HTTP_MAX_RETRIES: int = 3
    HTTP_KEEPALIVE_TIMEOUT: int = 60
    HTTP_MAX_CONNECTIONS: int = 100
    
    # Resource Configuration
    RESOURCE_MAX_SIZE: int = 5 * 1024 * 1024  # 5MB
    RESOURCE_FORMATS: list[str] = ["text", "json", "markdown"]
    
    # Computed Properties
    @property
    def api_base_url(self) -> str:
        """Get the complete base URL for the eRegulations API."""
        return f"{self.EREGULATIONS_API_URL}/{self.EREGULATIONS_API_VERSION}"
    
    # Configure environment file loading
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create global settings instance
settings = Settings()
