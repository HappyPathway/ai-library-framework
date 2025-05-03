"""Integration tests for secrets management utilities."""
import os

import pytest

from utils.secrets import SecretManager


@pytest.fixture
def secret_manager():
    """Create test secret manager instance."""
    try:
        credentials, project_id = google.auth.default()
        if not project_id:
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            if not project_id:
                pytest.skip(
                    "No Google Cloud project configured. Run 'gcloud config set project PROJECT_ID'")
        return SecretManager()
    except Exception as e:
        pytest.skip(
            f"Google Cloud authentication failed. Run 'gcloud auth application-default login'. Error: {e}")


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
    # Test non-existent secret
    secret = secret_manager.get_secret('NONEXISTENT_SECRET')
    assert secret is None


def test_secret_version_handling(secret_manager):
    """Test secret version handling."""
    # Test with latest version (default)
    latest = secret_manager.get_secret('TEST_SECRET')
    assert latest is not None

    # Test with explicit version
    version1 = secret_manager.get_secret('TEST_SECRET', version_id='1')
    assert version1 is not None


def test_secret_caching(secret_manager):
    """Test secret caching behavior."""
    # Get initial value
    first_call = secret_manager.get_secret('TEST_SECRET', use_cache=True)
    assert first_call is not None

    # Cached value should be returned (faster)
    second_call = secret_manager.get_secret('TEST_SECRET', use_cache=True)
    assert second_call == first_call

    # Clear cache and get fresh value
    secret_manager.clear_cache()
    fresh_call = secret_manager.get_secret('TEST_SECRET', use_cache=False)
    assert fresh_call is not None
