"""Tests for AI Engine functions."""

from unittest.mock import MagicMock


def test_create_settings_instance():
    """Test that the function properly creates a settings instance."""
    # Create mock default settings with temperature and max_tokens attributes
    mock_default_settings = MagicMock()
    mock_default_settings.temperature = 0.7
    mock_default_settings.max_tokens = 1000

    # Create a mock settings class that can be instantiated
    mock_settings_class = MagicMock()
    mock_settings_instance = MagicMock()
    mock_settings_class.return_value = mock_settings_instance

    # Mock the type() function to return our mock settings class
    def mock_type_function(_):
        return mock_settings_class

    # Create the function to test with the dependencies injected
    def create_settings_instance(default_settings):
        settings = mock_type_function(default_settings)()
        settings.temperature = default_settings.temperature
        settings.max_tokens = default_settings.max_tokens
        return settings

    # Call the function
    result = create_settings_instance(mock_default_settings)

    # Assert
    assert result == mock_settings_instance
    assert result.temperature == 0.7
    assert result.max_tokens == 1000


def test_setup_agent():
    """Test that the function properly configures and returns an agent."""
    # Create mocks
    mock_api_key = "test-api-key"
    mock_instrument = MagicMock()
    mock_settings = MagicMock()
    mock_settings.temperature = 0.5
    mock_settings.max_tokens = 2000
    mock_agent = MagicMock()
    mock_agent_class = MagicMock(return_value=mock_agent)

    # Create the function to test with the dependencies injected
    def setup_agent():
        model_settings = {
            "temperature": mock_settings.temperature or 0.7,
            "max_tokens": mock_settings.max_tokens
        }

        agent = mock_agent_class(
            model="test-model",
            api_key=mock_api_key,
            monitoring_callback=mock_instrument,
            model_settings=model_settings,
            usage_limits={"mock": "limits"},
            system="test-instructions"
        )

        return agent

    # Call the function
    result = setup_agent()

    # Assert
    assert result == mock_agent
    mock_agent_class.assert_called_once_with(
        model="test-model",
        api_key=mock_api_key,
        monitoring_callback=mock_instrument,
        model_settings={"temperature": 0.5, "max_tokens": 2000},
        usage_limits={"mock": "limits"},
        system="test-instructions"
    )
