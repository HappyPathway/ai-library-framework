"""Unified secrets management system.

DEPRECATED: This module has been moved to ailf.cloud.secrets.
Please update your imports to: from ailf.cloud.secrets import get_secret, SecretManager

This module provides a unified interface to access secrets from various providers.
"""
import os
import warnings
from typing import Optional, Dict, Any, List, Type

warnings.warn(
    "The utils.cloud.secrets module is deprecated. Use ailf.cloud.secrets instead.",
    DeprecationWarning,
    stacklevel=2
)

from .logging import setup_logging
from .secrets_providers import BaseSecretsProvider, DotEnvSecretsProvider

logger = setup_logging('secrets')

# Try to import optional providers
AVAILABLE_PROVIDERS = {}

# Always register DotEnv provider
AVAILABLE_PROVIDERS['env'] = DotEnvSecretsProvider

# Try to import and register Google provider
try:
    from .secrets_providers import GoogleSecretsProvider
    AVAILABLE_PROVIDERS['google'] = GoogleSecretsProvider
except ImportError:
    pass

# Try to import and register AWS provider
try:
    from .secrets_providers import AWSSecretsProvider
    AVAILABLE_PROVIDERS['aws'] = AWSSecretsProvider
except ImportError:
    pass

# Try to import and register Azure provider
try:
    from .secrets_providers import AzureSecretsProvider
    AVAILABLE_PROVIDERS['azure'] = AzureSecretsProvider
except ImportError:
    pass

# Try to import and register Vault provider
try:
    from .secrets_providers import VaultSecretsProvider
    AVAILABLE_PROVIDERS['vault'] = VaultSecretsProvider
except ImportError:
    pass


class SecretManager:
    """Unified secrets management across multiple providers.
    
    This class provides a consistent interface to access secrets from various
    providers like Google Secret Manager, AWS Secrets Manager, Azure Key Vault,
    HashiCorp Vault, and environment variables.
    
    Example:
        >>> from utils.cloud.secrets import secret_manager
        >>> 
        >>> # Get a secret (automatically selects provider)
        >>> api_key = secret_manager.get_secret('API_KEY')
        >>> 
        >>> # Specify a provider
        >>> db_password = secret_manager.get_secret('DB_PASSWORD', provider='aws')
        >>> 
        >>> # List available providers
        >>> providers = secret_manager.list_providers()
    """

    def __init__(self):
        """Initialize the SecretManager with default providers."""
        self._providers: Dict[str, BaseSecretsProvider] = {}
        self._provider_configs: Dict[str, Dict[str, Any]] = {}
        self._default_provider = os.environ.get('AILF_DEFAULT_SECRET_PROVIDER', 'env')
        
        # Always initialize DotEnv provider by default
        self.register_provider('env', DotEnvSecretsProvider())

    def register_provider(self, name: str, provider: BaseSecretsProvider) -> None:
        """Register a secret provider.
        
        Args:
            name: Name to identify this provider instance
            provider: Provider instance
        """
        if not isinstance(provider, BaseSecretsProvider):
            raise TypeError(f"Provider must be a BaseSecretsProvider instance, got {type(provider)}")
        
        self._providers[name] = provider
        logger.info(f"Registered secret provider: {name}")
        
    def configure_provider(self, provider_type: str, name: Optional[str] = None, **config) -> None:
        """Configure and register a new provider instance.
        
        Args:
            provider_type: Type of provider (google, aws, azure, vault, env)
            name: Optional name for this provider instance (defaults to provider_type)
            **config: Configuration parameters for the provider
        """
        if provider_type not in AVAILABLE_PROVIDERS:
            raise ValueError(f"Unknown provider type: {provider_type}. Available: {list(AVAILABLE_PROVIDERS.keys())}")
        
        provider_cls = AVAILABLE_PROVIDERS[provider_type]
        provider_name = name or provider_type
        
        # Store configuration
        self._provider_configs[provider_name] = config
        
        # Create provider instance
        try:
            provider = provider_cls(**config)
            self.register_provider(provider_name, provider)
        except Exception as e:
            logger.error(f"Failed to initialize {provider_type} provider: {str(e)}")
            raise

    def get_secret(self, secret_name: str, provider: Optional[str] = None, use_cache: bool = True,
                   **kwargs) -> Optional[str]:
        """Get a secret from the specified or default provider.
        
        Args:
            secret_name: Name of the secret to retrieve
            provider: Provider to use (if None, uses default provider)
            use_cache: Whether to use cached values if supported by provider
            **kwargs: Provider-specific arguments
            
        Returns:
            Secret value as string, or None if not found
        """
        # Determine which provider to use
        selected_provider = provider or self._default_provider
        
        # Check if provider exists
        if selected_provider not in self._providers:
            if selected_provider in AVAILABLE_PROVIDERS:
                # Auto-initialize with default settings
                try:
                    self.configure_provider(selected_provider)
                except Exception as e:
                    logger.error(f"Failed to auto-initialize provider {selected_provider}: {str(e)}")
                    return None
            else:
                logger.error(f"Provider {selected_provider} not registered")
                return None
                
        # Get secret from provider
        try:
            return self._providers[selected_provider].get_secret(
                secret_name=secret_name, 
                use_cache=use_cache,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error getting secret {secret_name} from provider {selected_provider}: {str(e)}")
            return None
    
    def clear_cache(self, provider: Optional[str] = None) -> None:
        """Clear the secret cache for one or all providers.
        
        Args:
            provider: Provider name to clear cache for. If None, clears all caches.
        """
        if provider:
            if provider in self._providers:
                self._providers[provider].clear_cache()
        else:
            for p in self._providers.values():
                p.clear_cache()
    
    def set_default_provider(self, provider: str) -> None:
        """Set the default provider.
        
        Args:
            provider: Provider name to use as default
        """
        if provider not in self._providers and provider not in AVAILABLE_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")
            
        self._default_provider = provider
    
    def list_providers(self) -> List[str]:
        """Get a list of registered provider names.
        
        Returns:
            List of provider names
        """
        return list(self._providers.keys())
    
    def list_available_provider_types(self) -> List[str]:
        """Get a list of available provider types.
        
        Returns:
            List of provider types that can be configured
        """
        return list(AVAILABLE_PROVIDERS.keys())
    
    def get_provider_config(self, name: str) -> Dict[str, Any]:
        """Get the configuration for a provider.
        
        Args:
            name: Provider name
            
        Returns:
            Provider configuration dictionary (copy)
        """
        if name not in self._provider_configs:
            return {}
        
        # Return copy to prevent modification
        return dict(self._provider_configs[name])


# Global instance
secret_manager = SecretManager()

# Re-export from the new module location at the end of the file
from ailf.cloud.secrets import *
