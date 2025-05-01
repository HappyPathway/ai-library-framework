"""Shared test fixtures and configuration."""
import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up test environment variables."""
    # Set default values for test environment
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
    os.environ.setdefault("GCS_BUCKET_NAME", "test-bucket")
    yield

@pytest.fixture(scope="session")
def test_credentials():
    """Check if test credentials are available."""
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        pytest.skip("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    yield

@pytest.fixture(scope="session")
def github_credentials():
    """Check if GitHub credentials are available."""
    if not os.getenv('GITHUB_TOKEN'):
        pytest.skip("GITHUB_TOKEN environment variable not set")
    yield
