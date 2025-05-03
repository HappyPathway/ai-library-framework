"""Tests for AIEngine.

This module contains tests for the AIEngine class to ensure proper functionality
and inheritance support.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Set required environment variables
os.environ['GOOGLE_CLOUD_PROJECT'] = 'mock-project'

# Mock modules that might not be installed
sys.modules['anthropic'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['pydantic_ai'] = MagicMock()
sys.modules['pydantic_ai.exceptions'] = MagicMock()
sys.modules['logfire'] = MagicMock()

# Mock internal modules
mock_secret_manager = MagicMock()
sys.modules['utils.secrets'] = MagicMock()
sys.modules['utils.secrets'].secret_manager = mock_secret_manager

# Now we can import AIEngine
with patch('utils.ai_engine.secret_manager', mock_secret_manager):
    from utils.ai_engine import AIEngine


class TestAIEngine:
    """Test the AIEngine class."""

    @pytest.fixture
    def mock_env_vars(self):
        """Set up environment variables for testing."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "GEMINI_API_KEY": "test-key",
            "ANTHROPIC_API_KEY": "test-key"
        }):
            yield

    @pytest.fixture
    def mock_agent(self):
        """Mock the Agent class."""
        with patch('utils.ai_engine.Agent') as mock:
            mock.return_value = MagicMock()
            yield mock

    def test_init(self, mock_env_vars, mock_agent):
        """Test initialization of AIEngine."""
        engine = AIEngine(feature_name="test_feature")
        assert engine.feature_name == "test_feature"
        assert engine.provider == "openai"
        assert engine.model_name == "openai:gpt-4-turbo"
        assert engine.agent is not None

    def test_get_api_key(self, mock_env_vars):
        """Test _get_api_key method."""
        engine = AIEngine(feature_name="test_feature")
        api_key = engine._get_api_key()
        assert api_key == "test-key"

        # Test with unsupported provider
        engine.provider = "unsupported"
        with pytest.raises(ValueError, match="Unsupported provider"):
            engine._get_api_key()

    def test_create_settings_instance(self, mock_env_vars, mock_agent):
        """Test _create_settings_instance method."""
        engine = AIEngine(feature_name="test_feature")
        default_settings = engine._get_provider_settings()
        settings = engine._create_settings_instance(default_settings)

        assert settings is not None
        assert hasattr(settings, "temperature")
        assert hasattr(settings, "max_tokens")


class CustomAIEngine(AIEngine):
    """Custom AIEngine subclass for testing inheritance."""

    def _setup_instrumentation(self):
        """Override to return a custom instrumentation object."""
        return MagicMock(name="custom_instrumentation")

    def _get_provider_settings(self):
        """Override to customize provider settings."""
        base_settings = super()._get_provider_settings()
        # In a real scenario, we would modify settings here
        return base_settings


def test_inheritance(mock_env_vars, mock_agent):
    """Test inheritance capabilities of AIEngine."""
    custom_engine = CustomAIEngine(feature_name="custom_feature")
    assert custom_engine.feature_name == "custom_feature"

    # Test that _setup_instrumentation was properly overridden
    instrument = custom_engine._setup_instrumentation()
    assert instrument.name == "custom_instrumentation"
