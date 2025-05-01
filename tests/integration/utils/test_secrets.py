"""Integration tests for secrets management utilities."""
import os
import pytest
from utils.secrets import SecretManager

@pytest.fixture
def secret_manager():
    """Create test secret manager instance."""
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        pytest.skip("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    if not os.getenv('GOOGLE_CLOUD_PROJECT'):
        pytest.skip("GOOGLE_CLOUD_PROJECT environment variable not set")
    
    return SecretManager()

def test_secret_operations(secret_manager):
    """Test secret operations."""
    # Get a test secret
    secret = secret_manager.get_secret('TEST_SECRET')
    assert secret is not None
    
    # Test caching
    cached_secret = secret_manager.get_secret('TEST_SECRET')
    assert cached_secret == secret
    
    # Test cache invalidation
    secret_manager.clear_cache()
    fresh_secret = secret_manager.get_secret('TEST_SECRET', use_cache=False)
    assert fresh_secret is not None
    
def test_nonexistent_secret(secret_manager):
    """Test handling of non-existent secrets."""
    secret = secret_manager.get_secret('NONEXISTENT_SECRET')
    assert secret is None
