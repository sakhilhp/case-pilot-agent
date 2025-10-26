"""
Credential management for external services.
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from cryptography.fernet import Fernet
import base64


class CredentialManager:
    """
    Manages secure storage and retrieval of external service credentials.
    
    Supports both environment variables and encrypted credential files.
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.logger = logging.getLogger("credential_manager")
        self._encryption_key = encryption_key
        self._fernet = None
        
        if encryption_key:
            try:
                self._fernet = Fernet(encryption_key.encode())
            except Exception as e:
                self.logger.error(f"Invalid encryption key: {str(e)}")
                
    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()
        
    def encrypt_value(self, value: str) -> str:
        """Encrypt a credential value."""
        if not self._fernet:
            raise ValueError("Encryption key not configured")
            
        return self._fernet.encrypt(value.encode()).decode()
        
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a credential value."""
        if not self._fernet:
            raise ValueError("Encryption key not configured")
            
        return self._fernet.decrypt(encrypted_value.encode()).decode()
        
    def get_credential(self, service: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get credential value for a service.
        
        Args:
            service: Service name (e.g., 'azure', 'credit_service')
            key: Credential key (e.g., 'api_key', 'endpoint')
            default: Default value if credential not found
            
        Returns:
            Credential value or default
        """
        # Try environment variable first
        env_var = f"{service.upper()}_{key.upper()}"
        env_value = os.getenv(env_var)
        if env_value:
            return env_value
            
        # Try credential file
        file_value = self._get_from_file(service, key)
        if file_value:
            return file_value
            
        return default
        
    def set_credential(self, service: str, key: str, value: str, encrypt: bool = True) -> None:
        """
        Set credential value for a service.
        
        Args:
            service: Service name
            key: Credential key
            value: Credential value
            encrypt: Whether to encrypt the value
        """
        credentials_file = self._get_credentials_file_path()
        credentials = self._load_credentials_file()
        
        if service not in credentials:
            credentials[service] = {}
            
        if encrypt and self._fernet:
            try:
                credentials[service][key] = {
                    "value": self.encrypt_value(value),
                    "encrypted": True
                }
            except Exception as e:
                self.logger.error(f"Failed to encrypt credential: {str(e)}")
                credentials[service][key] = {
                    "value": value,
                    "encrypted": False
                }
        else:
            credentials[service][key] = {
                "value": value,
                "encrypted": False
            }
            
        self._save_credentials_file(credentials)
        self.logger.info(f"Set credential for {service}.{key}")
        
    def delete_credential(self, service: str, key: str) -> bool:
        """
        Delete a credential.
        
        Args:
            service: Service name
            key: Credential key
            
        Returns:
            True if credential was deleted
        """
        credentials = self._load_credentials_file()
        
        if service in credentials and key in credentials[service]:
            del credentials[service][key]
            
            # Remove service if empty
            if not credentials[service]:
                del credentials[service]
                
            self._save_credentials_file(credentials)
            self.logger.info(f"Deleted credential for {service}.{key}")
            return True
            
        return False
        
    def list_services(self) -> list[str]:
        """List all services with stored credentials."""
        credentials = self._load_credentials_file()
        return list(credentials.keys())
        
    def list_credentials(self, service: str) -> list[str]:
        """List all credential keys for a service."""
        credentials = self._load_credentials_file()
        return list(credentials.get(service, {}).keys())
        
    def validate_credentials(self, service: str, required_keys: list[str]) -> Dict[str, bool]:
        """
        Validate that required credentials exist for a service.
        
        Args:
            service: Service name
            required_keys: List of required credential keys
            
        Returns:
            Dictionary mapping keys to validation status
        """
        validation_results = {}
        
        for key in required_keys:
            value = self.get_credential(service, key)
            validation_results[key] = value is not None and value.strip() != ""
            
        return validation_results
        
    def _get_from_file(self, service: str, key: str) -> Optional[str]:
        """Get credential from file."""
        credentials = self._load_credentials_file()
        
        if service not in credentials or key not in credentials[service]:
            return None
            
        credential_data = credentials[service][key]
        
        if isinstance(credential_data, dict):
            value = credential_data.get("value")
            is_encrypted = credential_data.get("encrypted", False)
            
            if is_encrypted and self._fernet:
                try:
                    return self.decrypt_value(value)
                except Exception as e:
                    self.logger.error(f"Failed to decrypt credential {service}.{key}: {str(e)}")
                    return None
            else:
                return value
        else:
            # Legacy format - plain string
            return credential_data
            
    def _load_credentials_file(self) -> Dict[str, Any]:
        """Load credentials from file."""
        credentials_file = self._get_credentials_file_path()
        
        if not credentials_file.exists():
            return {}
            
        try:
            with open(credentials_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load credentials file: {str(e)}")
            return {}
            
    def _save_credentials_file(self, credentials: Dict[str, Any]) -> None:
        """Save credentials to file."""
        credentials_file = self._get_credentials_file_path()
        credentials_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save credentials file: {str(e)}")
            
    def _get_credentials_file_path(self) -> Path:
        """Get path to credentials file."""
        credentials_dir = os.getenv("MORTGAGE_AI_CREDENTIALS_DIR", "config")
        return Path(credentials_dir) / "credentials.json"
        
    def export_credentials(self, service: str, output_file: str, include_encrypted: bool = False) -> None:
        """
        Export credentials for a service to a file.
        
        Args:
            service: Service name
            output_file: Output file path
            include_encrypted: Whether to include encrypted values
        """
        credentials = self._load_credentials_file()
        
        if service not in credentials:
            self.logger.warning(f"No credentials found for service: {service}")
            return
            
        export_data = {}
        
        for key, credential_data in credentials[service].items():
            if isinstance(credential_data, dict):
                is_encrypted = credential_data.get("encrypted", False)
                
                if is_encrypted and not include_encrypted:
                    export_data[key] = "[ENCRYPTED]"
                else:
                    export_data[key] = credential_data["value"]
            else:
                export_data[key] = credential_data
                
        try:
            with open(output_file, 'w') as f:
                json.dump({service: export_data}, f, indent=2)
                
            self.logger.info(f"Exported credentials for {service} to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export credentials: {str(e)}")
            
    def import_credentials(self, input_file: str, encrypt: bool = True) -> None:
        """
        Import credentials from a file.
        
        Args:
            input_file: Input file path
            encrypt: Whether to encrypt imported values
        """
        try:
            with open(input_file, 'r') as f:
                import_data = json.load(f)
                
            for service, credentials in import_data.items():
                for key, value in credentials.items():
                    if value != "[ENCRYPTED]":  # Skip placeholder values
                        self.set_credential(service, key, value, encrypt)
                        
            self.logger.info(f"Imported credentials from {input_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to import credentials: {str(e)}")