"""Shared test fixtures and configuration."""
import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up test environment variables."""
    # Load environment variables from .env file if it exists
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    # Set default values for test environment if not already set
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
    os.environ.setdefault("GCS_BUCKET_NAME", "test-bucket")
    os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
    os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
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

@pytest.fixture
def mock_secret_manager():
    """Create a mock secret manager."""
    mock_sm = MagicMock()
    mock_sm.get_secret.return_value = "test-api-key"
    
    with patch("utils.secrets.SecretManager", return_value=mock_sm):
        yield mock_sm

@pytest.fixture
def mock_monitoring():
    """Create a mock monitoring client."""
    mock_mon = MagicMock()
    
    with patch("pydantic_ai.monitoring.LogfireMonitoring", return_value=mock_mon):
        yield mock_mon
