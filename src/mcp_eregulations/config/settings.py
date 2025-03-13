"""
Configuration settings for the MCP eRegulations server.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the MCP eRegulations server."""
    
    # API Configuration
    EREGULATIONS_API_URL: str = os.getenv(
        "EREGULATIONS_API_URL", 
        "https://api-tanzania.tradeportal.org"
    )
    EREGULATIONS_API_VERSION: str = os.getenv("EREGULATIONS_API_VERSION", "v1")
    EREGULATIONS_API_KEY: str = os.getenv("EREGULATIONS_API_KEY", "")
    
    # Server Configuration
    MCP_SERVER_NAME: str = os.getenv("MCP_SERVER_NAME", "eregulations")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
    
    # Cache Configuration
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def api_base_url(self) -> str:
        """Get the full base URL for the eRegulations API."""
        return f"{self.EREGULATIONS_API_URL}"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create a global settings instance
settings = Settings()
