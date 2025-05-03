"""Test for the classify method in AIEngine."""

from unittest.mock import AsyncMock, MagicMock, patch


@patch("utils.ai_engine.Agent")
async def test_classify_single_label(mock_agent_class):
    """Test classifying content into a single category."""
    # Set up mocks
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock()
    mock_result = MagicMock()
    mock_result.text = "positive"
    mock_agent.run.return_value = mock_result
    mock_agent_class.return_value = mock_agent

    # Import here to use the patched agent
    from utils.ai_engine import AIEngine

    # Create engine with mocked dependencies
    engine = AIEngine(
        feature_name="test_classifier",
        model_name="test_model",
        provider="openai"
    )

    # Mock the API key retrieval
    engine._get_api_key = MagicMock(return_value="test-key")

    # Call the classify method
    result = await engine.classify(
        content="I love this product!",
        categories=["positive", "negative", "neutral"]
    )

    # Assert the result and function calls
    assert result == "positive"
    mock_agent.run.assert_called_once()

    # Check that the system prompt was correctly constructed
    call_args = mock_agent.run.call_args[1]
    assert "You are a text classifier" in call_args["system"]
    assert "Classify the following text into one of these categories" in call_args[
        "system"]
    assert "positive, negative, neutral" in call_args["system"]
    # Check that temperature is set for deterministic output
    assert call_args["temperature"] == 0.1


@patch("utils.ai_engine.Agent")
async def test_classify_multi_label(mock_agent_class):
    """Test classifying content into multiple categories."""
    # Set up mocks
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock()
    mock_result = MagicMock()
    mock_result.text = "informative, technical, educational"
    mock_agent.run.return_value = mock_result
    mock_agent_class.return_value = mock_agent

    # Import here to use the patched agent
    from utils.ai_engine import AIEngine

    # Create engine with mocked dependencies
    engine = AIEngine(
        feature_name="test_classifier",
        model_name="test_model",
        provider="openai"
    )

    # Mock the API key retrieval
    engine._get_api_key = MagicMock(return_value="test-key")

    # Call the classify method with multi_label=True
    result = await engine.classify(
        content="This article explains machine learning algorithms...",
        categories=["informative", "technical",
                    "educational", "opinion", "news"],
        multi_label=True
    )

    # Assert the result and function calls
    assert result == ["informative", "technical", "educational"]
    mock_agent.run.assert_called_once()

    # Check that the system prompt was correctly constructed
    call_args = mock_agent.run.call_args[1]
    assert "one or more of" in call_args["system"]
    assert "Return the categories as a comma-separated list" in call_args["system"]
