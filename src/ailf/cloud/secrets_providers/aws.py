"""AWS Secrets Manager implementation.

This module provides an AWS Secrets Manager implementation of the BaseSecretsProvider.
"""
from typing import Optional, Dict, Any

from .base import BaseSecretsProvider
from ..logging import setup_logging

logger = setup_logging('aws_secrets')

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logger.warning("boto3 not installed. AWS Secrets Manager provider will not be available.")


class AWSSecretsProvider(BaseSecretsProvider):
    """AWS Secrets Manager implementation.
    
    This provider uses boto3 to interact with AWS Secrets Manager.
    Authentication is handled through the standard AWS credential chain:
    
    1. Environment variables
    2. Shared credential file (~/.aws/credentials)
    3. AWS IAM role for EC2/ECS
    """

    def __init__(self, region_name: Optional[str] = None):
        """Initialize AWS Secrets Manager provider.
        
        Args:
            region_name: AWS region. If None, uses default region from AWS config.
        """
        if not AWS_AVAILABLE:
            raise ImportError("boto3 not installed. Please install with 'pip install boto3'")
            
        self._cache: Dict[str, str] = {}
        self._region_name = region_name
        self._client = boto3.client('secretsmanager', region_name=self._region_name)
    
    def get_secret(self, secret_name: str, use_cache: bool = True, version_id: Optional[str] = None, 
                  version_stage: str = 'AWSCURRENT', **kwargs) -> Optional[str]:
        """Get a secret value from AWS Secrets Manager.

        Args:
            secret_name: Name or ARN of the secret
            use_cache: Whether to use cached values
            version_id: Specific version ID to retrieve
            version_stage: Version stage to retrieve (default: AWSCURRENT)
            **kwargs: Additional parameters to pass to get_secret_value

        Returns:
            Secret value as string, or None if not found
        """
        try:
            # Check cache first
            cache_key = f"{secret_name}:{version_id or version_stage}"
            if use_cache and cache_key in self._cache:
                return self._cache[cache_key]

            # Prepare request parameters
            params: Dict[str, Any] = {'SecretId': secret_name}
            if version_id:
                params['VersionId'] = version_id
            else:
                params['VersionStage'] = version_stage
                
            # Add any additional parameters
            params.update(kwargs)

            # Get from AWS Secrets Manager
            response = self._client.get_secret_value(**params)
            
            # Prefer SecretString, but fall back to SecretBinary if needed
            if 'SecretString' in response:
                secret = response['SecretString']
            else:
                secret = response['SecretBinary'].decode('utf-8')

            # Update cache
            if use_cache:
                self._cache[cache_key] = secret

            return secret

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Error accessing secret {secret_name}: {error_code}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error accessing secret {secret_name}: {str(e)}")
            return None

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()
        
    def supports_rotation(self) -> bool:
        """Check if AWS Secrets Manager supports rotation.
        
        Returns:
            True as AWS Secrets Manager supports automatic rotation
        """
        return True
    
    @classmethod
    def provider_name(cls) -> str:
        """Get the provider name.
        
        Returns:
            'aws' as the provider name
        """
        return 'aws'
