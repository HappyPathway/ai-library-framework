"""Google Secret Manager implementation.

This module provides a Google Cloud Secret Manager implementation of the BaseSecretsProvider.
"""
import os
from typing import Optional, Dict

from google.cloud import secretmanager

from ..logging import setup_logging
from .base import BaseSecretsProvider

logger = setup_logging('gcp_secrets')


class GoogleSecretsProvider(BaseSecretsProvider):
    """Google Secret Manager implementation.
    
    This class uses Application Default Credentials (ADC) for authentication.
    Before using this class, ensure you have:

    1. Installed gcloud SDK
    2. Run 'gcloud auth application-default login'
    3. Set project: 'gcloud config set project YOUR-PROJECT'
    """

    def __init__(self, project_id: Optional[str] = None):
        """Initialize Google Secret Manager provider.
        
        Args:
            project_id: Google Cloud project ID. If None, uses GOOGLE_CLOUD_PROJECT env var.
        """
        self._client = secretmanager.SecretManagerServiceClient()
        self._project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        if not self._project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        
        self._cache: Dict[str, str] = {}
    
    def _get_secret_path(self, secret_name: str) -> str:
        """Get the full path to a secret.

        Args:
            secret_name: Name of the secret

        Returns:
            Full path to the secret in Secret Manager
        """
        return f"projects/{self._project_id}/secrets/{secret_name}/versions/latest"

    def get_secret(self, secret_name: str, use_cache: bool = True, **kwargs) -> Optional[str]:
        """Get a secret value from Google Secret Manager.

        Args:
            secret_name: Name of the secret
            use_cache: Whether to use cached values
            **kwargs: Not used by this provider

        Returns:
            Secret value, or None if not found
        """
        try:
            # Check cache first
            if use_cache and secret_name in self._cache:
                return self._cache[secret_name]

            # Get from Secret Manager
            path = self._get_secret_path(secret_name)
            response = self._client.access_secret_version(request={"name": path})
            secret = response.payload.data.decode("UTF-8")

            # Update cache
            if use_cache:
                self._cache[secret_name] = secret

            return secret

        except Exception as e:
            logger.error(f"Error accessing secret {secret_name}: {str(e)}")
            return None

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()
        
    def supports_rotation(self) -> bool:
        """Check if Google Secret Manager supports rotation.
        
        Returns:
            True as Google Secret Manager supports automatic rotation
        """
        return True
    
    @classmethod
    def provider_name(cls) -> str:
        """Get the provider name.
        
        Returns:
            'google' as the provider name
        """
        return 'google'
