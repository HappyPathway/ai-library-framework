"""Test for the generate_text method in AIEngine."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock modules that might not be installed
sys.modules['anthropic'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['pydantic_ai'] = MagicMock()
sys.modules['pydantic_ai.exceptions'] = MagicMock()
sys.modules['logfire'] = MagicMock()

# Set required environment variables

os.environ['GOOGLE_CLOUD_PROJECT'] = 'mock-project'
os.environ['OPENAI_API_KEY'] = 'test-api-key'
os.environ['GEMINI_API_KEY'] = 'test-api-key'
os.environ['ANTHROPIC_API_KEY'] = 'test-api-key'

# Mock internal modules
mock_secret_manager = MagicMock()
sys.modules['utils.secrets'] = MagicMock()
sys.modules['utils.secrets'].secret_manager = mock_secret_manager


@pytest.mark.asyncio
@patch("utils.ai_engine.Agent")
async def test_generate_text_with_max_length(mock_agent_class):
    """Test generating text with max_length parameter."""
    # Set up mocks
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock()
    mock_result = MagicMock()
    mock_result.text = "Generated text response"
    mock_agent.run.return_value = mock_result
    mock_agent_class.return_value = mock_agent

    # Import here to use the patched agent
    from utils.ai_engine import AIEngine

    # Create engine with mocked dependencies
    engine = AIEngine(
        feature_name="test_text_generator",
        model_name="test_model",
        provider="openai"
    )

    # Mock the API key retrieval
    engine._get_api_key = MagicMock(return_value="test-key")

    # Call the generate_text method with max_length
    result = await engine.generate_text(
        prompt="Generate a short story",
        max_length=100
    )

    # Assert the result
    assert result == "Generated text response"

    # Check that the system prompt was correctly constructed with max_length
    call_args = mock_agent.run.call_args[1]
    assert "Keep your response under 100 characters" in call_args["system"]


@pytest.mark.asyncio
@patch("utils.ai_engine.Agent")
async def test_generate_text_with_error(mock_agent_class):
    """Test generate_text error handling."""
    # Set up mocks
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(side_effect=Exception("Test error"))
    mock_agent_class.return_value = mock_agent

    # Import here to use the patched agent
    from utils.ai_engine import AIEngine

    # Create engine with mocked dependencies
    engine = AIEngine(
        feature_name="test_text_generator",
        model_name="test_model",
        provider="openai"
    )

    # Mock the API key retrieval
    engine._get_api_key = MagicMock(return_value="test-key")

    # Call the method that should handle the error
    result = await engine.generate_text(prompt="Generate a short story")

    # Assert that None is returned when an error occurs
    assert result is None
