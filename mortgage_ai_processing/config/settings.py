"""
Configuration settings for mortgage processing system.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import os
import json
import logging


@dataclass
class AzureConfig:
    """Azure Document Intelligence configuration."""
    endpoint: str = ""
    api_key: str = ""
    api_version: str = "2023-07-31"
    timeout: int = 30


@dataclass
class CreditServiceConfig:
    """Credit service configuration."""
    provider: str = "experian"  # experian, equifax, transunion
    endpoint: str = ""
    api_key: str = ""
    timeout: int = 30


@dataclass
class PropertyServiceConfig:
    """Property valuation service configuration."""
    provider: str = "zillow"  # zillow, redfin, corelogic
    endpoint: str = ""
    api_key: str = ""
    timeout: int = 30


@dataclass
class PEPSanctionsConfig:
    """PEP and sanctions screening configuration."""
    provider: str = "worldcheck"  # worldcheck, dow_jones, refinitiv
    endpoint: str = ""
    api_key: str = ""
    timeout: int = 30


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "mortgage_processing"
    username: str = ""
    password: str = ""
    ssl_mode: str = "prefer"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class MCPConfig:
    """MCP server configuration."""
    server_name: str = "mortgage-ai-processing"
    host: str = "localhost"
    port: int = 8000
    version: str = "1.0.0"
    enable_logging: bool = True


@dataclass
class SecurityConfig:
    """Security configuration."""
    encryption_key: str = ""
    jwt_secret: str = ""
    jwt_expiration: int = 3600  # 1 hour
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # 1 minute


@dataclass
class Settings:
    """Main configuration settings."""
    environment: str = "development"
    debug: bool = False
    
    # Service configurations
    azure: AzureConfig = field(default_factory=AzureConfig)
    credit_service: CreditServiceConfig = field(default_factory=CreditServiceConfig)
    property_service: PropertyServiceConfig = field(default_factory=PropertyServiceConfig)
    pep_sanctions: PEPSanctionsConfig = field(default_factory=PEPSanctionsConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
    # System configurations
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Processing configurations
    max_concurrent_applications: int = 10
    processing_timeout: int = 300  # 5 minutes
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds
    
    @classmethod
    def from_file(cls, config_path: str) -> "Settings":
        """Load settings from JSON configuration file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            logging.warning(f"Configuration file not found: {config_path}")
            return cls()
            
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                
            return cls.from_dict(config_data)
            
        except Exception as e:
            logging.error(f"Error loading configuration: {str(e)}")
            return cls()
            
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Settings":
        """Create settings from dictionary."""
        settings = cls()
        
        # Update main settings
        for key, value in config_dict.items():
            if hasattr(settings, key) and not isinstance(getattr(settings, key), (AzureConfig, CreditServiceConfig, PropertyServiceConfig, PEPSanctionsConfig, DatabaseConfig, LoggingConfig, MCPConfig, SecurityConfig)):
                setattr(settings, key, value)
                
        # Update nested configurations
        if "azure" in config_dict:
            settings.azure = AzureConfig(**config_dict["azure"])
            
        if "credit_service" in config_dict:
            settings.credit_service = CreditServiceConfig(**config_dict["credit_service"])
            
        if "property_service" in config_dict:
            settings.property_service = PropertyServiceConfig(**config_dict["property_service"])
            
        if "pep_sanctions" in config_dict:
            settings.pep_sanctions = PEPSanctionsConfig(**config_dict["pep_sanctions"])
            
        if "database" in config_dict:
            settings.database = DatabaseConfig(**config_dict["database"])
            
        if "logging" in config_dict:
            settings.logging = LoggingConfig(**config_dict["logging"])
            
        if "mcp" in config_dict:
            settings.mcp = MCPConfig(**config_dict["mcp"])
            
        if "security" in config_dict:
            settings.security = SecurityConfig(**config_dict["security"])
            
        return settings
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "azure": {
                "endpoint": self.azure.endpoint,
                "api_key": self.azure.api_key,
                "api_version": self.azure.api_version,
                "timeout": self.azure.timeout
            },
            "credit_service": {
                "provider": self.credit_service.provider,
                "endpoint": self.credit_service.endpoint,
                "api_key": self.credit_service.api_key,
                "timeout": self.credit_service.timeout
            },
            "property_service": {
                "provider": self.property_service.provider,
                "endpoint": self.property_service.endpoint,
                "api_key": self.property_service.api_key,
                "timeout": self.property_service.timeout
            },
            "pep_sanctions": {
                "provider": self.pep_sanctions.provider,
                "endpoint": self.pep_sanctions.endpoint,
                "api_key": self.pep_sanctions.api_key,
                "timeout": self.pep_sanctions.timeout
            },
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "username": self.database.username,
                "password": self.database.password,
                "ssl_mode": self.database.ssl_mode
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "file_path": self.logging.file_path,
                "max_file_size": self.logging.max_file_size,
                "backup_count": self.logging.backup_count
            },
            "mcp": {
                "server_name": self.mcp.server_name,
                "host": self.mcp.host,
                "port": self.mcp.port,
                "version": self.mcp.version,
                "enable_logging": self.mcp.enable_logging
            },
            "security": {
                "encryption_key": self.security.encryption_key,
                "jwt_secret": self.security.jwt_secret,
                "jwt_expiration": self.security.jwt_expiration,
                "rate_limit_requests": self.security.rate_limit_requests,
                "rate_limit_window": self.security.rate_limit_window
            },
            "max_concurrent_applications": self.max_concurrent_applications,
            "processing_timeout": self.processing_timeout,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay
        }
        
    def save_to_file(self, config_path: str) -> None:
        """Save settings to JSON configuration file."""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    
    if _settings is None:
        # Try to load from environment variable or default location
        config_path = os.getenv("MORTGAGE_AI_CONFIG", "config/settings.json")
        _settings = Settings.from_file(config_path)
        
        # Override with environment variables
        _settings = _load_from_environment(_settings)
        
    return _settings


def _load_from_environment(settings: Settings) -> Settings:
    """Load configuration overrides from environment variables."""
    
    # Azure configuration
    if os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"):
        settings.azure.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    if os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY"):
        settings.azure.api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
    # Database configuration
    if os.getenv("DATABASE_HOST"):
        settings.database.host = os.getenv("DATABASE_HOST")
    if os.getenv("DATABASE_PORT"):
        settings.database.port = int(os.getenv("DATABASE_PORT"))
    if os.getenv("DATABASE_NAME"):
        settings.database.database = os.getenv("DATABASE_NAME")
    if os.getenv("DATABASE_USERNAME"):
        settings.database.username = os.getenv("DATABASE_USERNAME")
    if os.getenv("DATABASE_PASSWORD"):
        settings.database.password = os.getenv("DATABASE_PASSWORD")
        
    # Security configuration
    if os.getenv("ENCRYPTION_KEY"):
        settings.security.encryption_key = os.getenv("ENCRYPTION_KEY")
    if os.getenv("JWT_SECRET"):
        settings.security.jwt_secret = os.getenv("JWT_SECRET")
        
    # Environment and debug
    if os.getenv("ENVIRONMENT"):
        settings.environment = os.getenv("ENVIRONMENT")
    if os.getenv("DEBUG"):
        settings.debug = os.getenv("DEBUG").lower() == "true"
        
    return settings


def reset_settings() -> None:
    """Reset global settings instance (useful for testing)."""
    global _settings
    _settings = None