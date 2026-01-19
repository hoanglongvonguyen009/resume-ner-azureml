"""Configuration utilities for API testing notebooks."""

from typing import TypedDict
import os


class NotebookConfig(TypedDict, total=False):
    """Configuration for API testing notebooks.
    
    Attributes:
        api_base_url: Base URL for the API server (default: "http://localhost:8000")
        api_timeout: Request timeout in seconds (default: 30)
    """
    api_base_url: str
    api_timeout: int


def get_default_config() -> NotebookConfig:
    """Get default notebook configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        "api_base_url": "http://localhost:8000",
        "api_timeout": 30,
    }


def get_config_from_env() -> NotebookConfig:
    """Get configuration from environment variables.
    
    Environment variables:
        API_BASE_URL: Base URL for the API server
        API_TIMEOUT: Request timeout in seconds
    
    Returns:
        Configuration dictionary with values from environment or defaults
    """
    config = get_default_config()
    
    if "API_BASE_URL" in os.environ:
        config["api_base_url"] = os.environ["API_BASE_URL"]
    
    if "API_TIMEOUT" in os.environ:
        try:
            config["api_timeout"] = int(os.environ["API_TIMEOUT"])
        except ValueError:
            pass  # Use default if invalid
    
    return config


