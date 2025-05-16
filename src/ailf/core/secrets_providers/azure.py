"""Azure Key Vault implementation.

This module provides an Azure Key Vault implementation of the BaseSecretsProvider.
"""
from typing import Optional, Dict

from .base import BaseSecretsProvider
from ..logging import setup_logging

logger = setup_logging('azure_secrets')

try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("Azure SDK not installed. Azure Key Vault provider will not be available.")


class AzureSecretsProvider(BaseSecretsProvider):
    """Azure Key Vault implementation.
    
    This provider uses Azure SDK to interact with Azure Key Vault.
    Authentication is handled through DefaultAzureCredential, which tries:
    
    1. Environment variables
    2. Managed Identity
    3. Visual Studio Code
    4. Azure CLI
    5. Azure PowerShell
    """

    def __init__(self, vault_url: str):
        """Initialize Azure Key Vault provider.
        
        Args:
            vault_url: URL of the Azure Key Vault (e.g., "https://myvault.vault.azure.net/")
        """
        if not AZURE_AVAILABLE:
            raise ImportError(
                "Azure SDK not installed. Please install with 'pip install azure-keyvault-secrets azure-identity'")
            
        self._cache: Dict[str, str] = {}
        self._vault_url = vault_url
        self._credential = DefaultAzureCredential()
        self._client = SecretClient(vault_url=self._vault_url, credential=self._credential)
    
    def get_secret(self, secret_name: str, use_cache: bool = True, version: Optional[str] = None, **kwargs) -> Optional[str]:
        """Get a secret value from Azure Key Vault.

        Args:
            secret_name: Name of the secret
            use_cache: Whether to use cached values
            version: Specific version to retrieve
            **kwargs: Not used by this provider

        Returns:
            Secret value as string, or None if not found
        """
        try:
            # Check cache first
            cache_key = f"{secret_name}:{version or 'latest'}"
            if use_cache and cache_key in self._cache:
                return self._cache[cache_key]

            # Get secret from Azure Key Vault
            if version:
                secret = self._client.get_secret(name=secret_name, version=version)
            else:
                secret = self._client.get_secret(name=secret_name)

            secret_value = secret.value

            # Update cache
            if use_cache:
                self._cache[cache_key] = secret_value

            return secret_value

        except Exception as e:
            logger.error(f"Error accessing secret {secret_name}: {str(e)}")
            return None

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()
        
    def supports_rotation(self) -> bool:
        """Check if Azure Key Vault supports rotation.
        
        Returns:
            True as Azure Key Vault supports rotation policies
        """
        return True
    
    @classmethod
    def provider_name(cls) -> str:
        """Get the provider name.
        
        Returns:
            'azure' as the provider name
        """
        return 'azure'
