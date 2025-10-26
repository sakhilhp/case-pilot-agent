"""
Configuration module for mortgage processing system.

Handles configuration management for:
- External service credentials
- Environment-specific settings
- Security configurations
- Logging configurations
"""

from .settings import Settings, get_settings
from .credentials import CredentialManager
from .logging import setup_logging

__all__ = [
    "Settings",
    "get_settings",
    "CredentialManager", 
    "setup_logging"
]