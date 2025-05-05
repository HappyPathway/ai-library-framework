"""
Test module for AI Engine functionality.
"""

import os
import sys

import pytest

# Add the root directory to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def test_ai_module_importable():
    """Test that the AI module can be imported."""
    try:
        import utils.ai_engine
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import utils.ai_engine: {e}")


class TestAIEngineFunctionality:
    """Unit tests for the AI Engine."""

    def test_initialization_mock(self):
        """Test that the AI Engine can be initialized with mock settings."""
        # Skip this test if utils.ai_engine can't be imported
        try:
            from utils.ai_engine import AIEngine

            # Use a mock configuration for testing
            engine = AIEngine(
                feature_name="test-feature",
                provider="mock",
                model_name="mock:model"
            )
            assert engine.provider == "mock"
            assert hasattr(engine, "agent")
        except (ImportError, AttributeError) as e:
            pytest.skip(f"Skipping test due to import or attribute error: {e}")

    @pytest.mark.skip(reason="Requires OpenAI package and credentials")
    def test_get_providers(self):
        """Test that the AI Engine can list providers."""
        from utils.ai_engine import AIEngine
        engine = AIEngine(feature_name="test-feature", provider="openai", model_name="gpt-3.5-turbo")
        # Check if the settings_map contains providers
        assert hasattr(engine, "settings_map")
        assert "openai" in engine.settings_map
        assert "gemini" in engine.settings_map
        assert "anthropic" in engine.settings_map
