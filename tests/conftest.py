"""Global test configuration fixtures."""
import pytest
import os
from pathlib import Path
from dotenv import load_dotenv

def pytest_configure(config):
    """Configure test settings."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    
    # Load environment variables at the start of testing
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)

@pytest.fixture(scope="session")
def test_env():
    """Set up test environment."""
    # Override any sensitive credentials for testing
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
    os.environ.setdefault("GCS_BUCKET_NAME", "test-bucket")
    
    # Return test configuration
    return {
        "test_dir": Path(__file__).parent,
        "workspace_dir": Path(__file__).parent.parent,
        "is_ci": bool(os.getenv("CI")),
    }

@pytest.fixture(scope="session")
def github_token():
    """Get GitHub token for tests."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("""
        GITHUB_TOKEN environment variable not set.
        Please create a personal access token at https://github.com/settings/tokens
        with the following scopes:
        - repo (Full control of private repositories)
        - read:org (Read org and team membership)
        Then add it to your .env file:
        GITHUB_TOKEN=your_token_here
        """)
    return token

@pytest.fixture(scope="session")
def gcp_credentials():
    """Get Google Cloud credentials for tests."""
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        pytest.skip("""
        GOOGLE_APPLICATION_CREDENTIALS environment variable not set.
        To set up locally, run:
        gcloud auth application-default login
        """)
    return os.getenv("GOOGLE_APPLICATION_CREDENTIALS")