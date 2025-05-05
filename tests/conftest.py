"""
Global pytest configuration for the project.
"""

import os
import sys

import pytest

# Add the project root to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Skip tests that require external services if running in CI without credentials


def pytest_configure(config):
    """Configure pytest."""
    # Register all markers to avoid warnings
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running test")

# Define fixtures that should be available to all tests


@pytest.fixture(scope="session")
def temp_dir(tmpdir_factory):
    """Create a temporary directory for the test session."""
    return tmpdir_factory.mktemp("test_data")


@pytest.fixture(scope="session")
def test_env():
    """Return environment variables needed for tests."""
    return {
        "has_openai": "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"],
        "has_gemini": "GEMINI_API_KEY" in os.environ and os.environ["GEMINI_API_KEY"],
        "has_anthropic": "ANTHROPIC_API_KEY" in os.environ and os.environ["ANTHROPIC_API_KEY"],
        "has_gcp": "GOOGLE_APPLICATION_CREDENTIALS" in os.environ and os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
        "has_github": "GITHUB_TOKEN" in os.environ and os.environ["GITHUB_TOKEN"],
    }
