"""DotEnv implementation of BaseSecretsProvider.

This module provides a .env file implementation of the BaseSecretsProvider.
"""
import os
from typing import Optional, Dict, Any
from pathlib import Path

from .base import BaseSecretsProvider
from ailf.core.logging import setup_logging

logger = setup_logging('dotenv_secrets')

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.warning("python-dotenv not installed. DotEnv provider will use os.environ only.")


class DotEnvSecretsProvider(BaseSecretsProvider):
    """Environment variable based secrets provider.
    
    This provider uses environment variables, optionally loading from .env files.
    It's particularly useful for local development and simple deployments.
    """

    def __init__(self, env_path: Optional[str] = None, override: bool = False,
                 prefix: str = "", suffix: str = ""):
        """Initialize DotEnv provider.
        
        Args:
            env_path: Path to .env file(s). Can be a single path or a list of paths.
                     If None, the provider will only use existing environment variables.
            override: Whether to override existing environment variables with values from .env
            prefix: Optional prefix for environment variable names
            suffix: Optional suffix for environment variable names
        """
        self._prefix = prefix
        self._suffix = suffix
        self._loaded = False
        self._cache: Dict[str, str] = {}
        
        # Load .env file(s) if needed and python-dotenv is available
        if env_path and DOTENV_AVAILABLE:
            if isinstance(env_path, (list, tuple)):
                for path in env_path:
                    if os.path.isfile(path):
                        load_dotenv(path, override=override)
                        self._loaded = True
            else:
                if os.path.isfile(env_path):
                    load_dotenv(env_path, override=override)
                    self._loaded = True
                    
        if env_path and not DOTENV_AVAILABLE:
            logger.warning("python-dotenv not installed. Install with 'pip install python-dotenv' to load .env files.")
    
    def get_secret(self, secret_name: str, use_cache: bool = True, default: Optional[str] = None, 
                   **kwargs) -> Optional[str]:
        """Get a secret value from environment variables.

        Args:
            secret_name: Name of the environment variable
            use_cache: Whether to use cached values
            default: Default value if secret is not found
            **kwargs: Not used by this provider

        Returns:
            Secret value, or default/None if not found
        """
        try:
            # Apply prefix/suffix
            env_name = f"{self._prefix}{secret_name}{self._suffix}"
            
            # Check cache first
            if use_cache and env_name in self._cache:
                return self._cache[env_name]

            # Get from environment
            secret = os.environ.get(env_name, default)

            # Update cache
            if secret is not None and use_cache:
                self._cache[env_name] = secret

            return secret

        except Exception as e:
            logger.error(f"Error accessing environment variable {secret_name}: {str(e)}")
            return default

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()
        
    def supports_rotation(self) -> bool:
        """Check if DotEnv provider supports rotation.
        
        Returns:
            False as environment variables do not support automatic rotation
        """
        return False
    
    @classmethod
    def provider_name(cls) -> str:
        """Get the provider name.
        
        Returns:
            'env' as the provider name
        """
        return 'env'
