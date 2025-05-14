"""Vault implementation of BaseSecretsProvider.

This module provides a HashiCorp Vault implementation of the BaseSecretsProvider.
"""
from typing import Optional, Dict, Any
import os

from .base import BaseSecretsProvider
from ..logging import setup_logging

logger = setup_logging('vault_secrets')

try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    logger.warning("hvac not installed. HashiCorp Vault provider will not be available.")


class VaultSecretsProvider(BaseSecretsProvider):
    """HashiCorp Vault implementation.
    
    This provider uses hvac to interact with HashiCorp Vault.
    Authentication is flexible with multiple supported methods.
    """

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None, 
                 auth_method: Optional[str] = None, **auth_kwargs):
        """Initialize HashiCorp Vault provider.
        
        Args:
            url: Vault server URL (default: VAULT_ADDR env var)
            token: Vault token (default: VAULT_TOKEN env var)
            auth_method: Authentication method if not using token
            **auth_kwargs: Arguments for the chosen auth method
        """
        if not VAULT_AVAILABLE:
            raise ImportError("hvac not installed. Please install with 'pip install hvac'")
            
        self._cache: Dict[str, str] = {}
        self._url = url or os.environ.get('VAULT_ADDR')
        
        if not self._url:
            raise ValueError("Vault URL must be provided or set in VAULT_ADDR environment variable")
        
        # Create client
        self._client = hvac.Client(url=self._url)
        
        # Handle authentication
        if token:
            self._client.token = token
        elif os.environ.get('VAULT_TOKEN'):
            self._client.token = os.environ.get('VAULT_TOKEN')
        elif auth_method:
            self._authenticate(auth_method, **auth_kwargs)
        else:
            logger.warning("No authentication provided for Vault. Some operations may fail.")
    
    def _authenticate(self, method: str, **kwargs) -> None:
        """Authenticate to Vault using the specified method.
        
        Args:
            method: Authentication method name
            **kwargs: Arguments for the auth method
        """
        try:
            if method == 'ldap':
                self._client.auth.ldap.login(**kwargs)
            elif method == 'approle':
                self._client.auth.approle.login(**kwargs)
            elif method == 'userpass':
                self._client.auth.userpass.login(**kwargs)
            elif method == 'kubernetes':
                self._client.auth.kubernetes.login(**kwargs)
            else:
                raise ValueError(f"Unsupported authentication method: {method}")
        except Exception as e:
            logger.error(f"Vault authentication failed: {str(e)}")
            raise
    
    def get_secret(self, secret_name: str, use_cache: bool = True, mount_point: str = 'secret', 
                   version: Optional[int] = None, **kwargs) -> Optional[str]:
        """Get a secret value from HashiCorp Vault.

        Args:
            secret_name: Path to the secret in Vault
            use_cache: Whether to use cached values
            mount_point: Secret engine mount point
            version: Secret version (for KV v2)
            **kwargs: Additional keyword arguments for read_secret

        Returns:
            Secret value, or None if not found
        """
        try:
            # Check if authenticated
            if not self._client.is_authenticated():
                logger.error("Not authenticated to Vault")
                return None
                
            # Check cache first
            cache_key = f"{mount_point}:{secret_name}:{version or 'latest'}"
            if use_cache and cache_key in self._cache:
                return self._cache[cache_key]

            # Determine if we're using KV v1 or v2
            mount_config = self._client.sys.read_mount_configuration(mount_point)
            is_v2 = mount_config['data'].get('options', {}).get('version') == '2'

            # Get secret using appropriate method
            if is_v2:
                # KV v2 engine
                params = {'path': secret_name, 'mount_point': mount_point}
                if version is not None:
                    params['version'] = version
                secret = self._client.secrets.kv.v2.read_secret_version(**params)
                secret_value = secret['data']['data'].get(secret_name.split('/')[-1])
            else:
                # KV v1 engine
                secret = self._client.secrets.kv.read_secret(path=secret_name, mount_point=mount_point)
                secret_value = secret['data'].get(secret_name.split('/')[-1])
            
            # Update cache
            if secret_value is not None and use_cache:
                self._cache[cache_key] = secret_value

            return secret_value

        except Exception as e:
            logger.error(f"Error accessing Vault secret {secret_name}: {str(e)}")
            return None

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()
        
    def supports_rotation(self) -> bool:
        """Check if HashiCorp Vault supports rotation.
        
        Returns:
            True as HashiCorp Vault supports dynamic secrets and rotation
        """
        return True
    
    @classmethod
    def provider_name(cls) -> str:
        """Get the provider name.
        
        Returns:
            'vault' as the provider name
        """
        return 'vault'
