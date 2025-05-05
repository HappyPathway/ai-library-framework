"""
Test module to verify that all required environment variables are set.
"""

import os

import pytest

# List of required environment variables with descriptions and whether they're critical
ENV_VARS = [
    {"name": "OPENAI_API_KEY", "critical": True, "description": "OpenAI API key for AI functionality"},
    {"name": "GEMINI_API_KEY", "critical": True, "description": "Google Gemini API key for AI functionality"},
    {"name": "ANTHROPIC_API_KEY", "critical": True, "description": "Anthropic API key for Claude models"},
    {"name": "GITHUB_TOKEN", "critical": False, "description": "GitHub token for GitHub API access"},
    {"name": "GOOGLE_CLOUD_PROJECT", "critical": False, "description": "Google Cloud project ID"},
    {"name": "GOOGLE_APPLICATION_CREDENTIALS", "critical": False, "description": "Path to Google Cloud credentials file"},
    {"name": "GCS_BUCKET_NAME", "critical": False, "description": "Google Cloud Storage bucket name"},
    {"name": "ENVIRONMENT", "critical": False, "description": "Environment name (dev, staging, prod)"},
    {"name": "LOGFIRE_API_KEY", "critical": False, "description": "Logfire API key for logging"},
]


def check_env_var(var_name):
    """Check if an environment variable is set and return status message."""
    value = os.environ.get(var_name, "")

    if value:
        # Mask sensitive values in output
        masked_value = f"{value[:2]}...{value[-4:]}" if len(value) > 6 else "***"
        return True, f"✅ {var_name} is set: {masked_value}"
    else:
        return False, f"❌ {var_name} is NOT set"


@pytest.mark.parametrize("env_var", [v for v in ENV_VARS if v["critical"]])
def test_critical_env_vars(env_var):
    """Test that critical environment variables are set."""
    var_name = env_var["name"]
    is_set, _ = check_env_var(var_name)
    assert is_set, f"Critical environment variable {var_name} is not set. {env_var['description']}"


@pytest.mark.parametrize("env_var", [v for v in ENV_VARS if not v["critical"]])
def test_optional_env_vars(env_var):
    """Test optional environment variables and skip if not set."""
    var_name = env_var["name"]
    is_set, _ = check_env_var(var_name)
    if not is_set:
        pytest.skip(f"Optional environment variable {var_name} is not set: {env_var['description']}")
