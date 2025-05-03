"""Shared test fixtures and configuration."""
import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from dotenv import load_dotenv

# Load environment variables at module level
env_path = Path(__file__).parent.parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up test environment variables."""
    # Set default test environment variables
    test_vars = {
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "GCS_BUCKET_NAME": "test-bucket",
        "OPENAI_API_KEY": "test-openai-key",
        "GEMINI_API_KEY": "test-google-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key"
    }
    
    # Only set if not already present
    for key, value in test_vars.items():
        os.environ.setdefault(key, value)
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

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables before running tests."""
    load_dotenv()
    # Verify required variables
    if not os.getenv("GITHUB_TOKEN"):
        pytest.skip("GITHUB_TOKEN environment variable not set")

@pytest.fixture(scope="session")
def mock_gcp():
    """Mock Google Cloud Platform services."""
    with patch('google.cloud.storage.Client') as storage_mock, \
         patch('google.cloud.secretmanager.SecretManagerServiceClient') as secret_mock:
        yield {
            'storage': storage_mock,
            'secret_manager': secret_mock
        }

@pytest.fixture(scope="session")
def mock_github():
    """Mock GitHub API for tests that don't need real GitHub access."""
    with patch('github.Github') as github_mock:
        mock_user = MagicMock()
        mock_user.login = "test-user"
        github_mock.return_value.get_user.return_value = mock_user
        yield github_mock

@pytest.fixture(scope="session")
def mock_repository():
    """Create a mock GitHub repository."""
    mock_repo = MagicMock()
    mock_repo.name = "test-repo"
    mock_repo.full_name = "test-user/test-repo"
    return mock_repo
