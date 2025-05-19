"""Base interface for secret management providers.

This module defines the abstract base class that all secret providers must implement.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseSecretsProvider(ABC):
    """Abstract base class for secrets management providers.
    
    All secret engine implementations should inherit from this class and
    implement its abstract methods.
    """
    
    @abstractmethod
    def get_secret(self, secret_name: str, use_cache: bool = True, **kwargs) -> Optional[str]:
        """Get a secret value from the provider.
        
        Args:
            secret_name: Name of the secret to retrieve
            use_cache: Whether to use cached values if supported
            **kwargs: Provider-specific optional arguments
            
        Returns:
            Secret value as string, or None if not found
        """
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear the secrets cache if supported by the provider."""
        pass
        
    @abstractmethod
    def supports_rotation(self) -> bool:
        """Check if the provider supports automatic secret rotation.
        
        Returns:
            True if secret rotation is supported, False otherwise
        """
        pass
    
    @classmethod
    def provider_name(cls) -> str:
        """Get the name of this secrets provider.
        
        Returns:
            Provider name as a string
        """
        return cls.__name__
