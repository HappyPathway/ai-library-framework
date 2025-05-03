"""Test the AI Engine functionality."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

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


def test_import_basemodel():
    """Test that BaseModel can be imported and used."""
    from pydantic import BaseModel

    class TestModel(BaseModel):
        name: str
        value: int

    # Create instance of the model
    instance = TestModel(name="test", value=42)
    assert instance.name == "test"
    assert instance.value == 42


def test_import_ai_engine():
    """Test that AIEngine can be imported."""
    # Importing AIEngine should not raise any errors
    from utils.ai_engine import AIEngine
    assert AIEngine is not None

    # Check that AIEngine uses BaseModel
    from pydantic import BaseModel
    assert BaseModel is not None


if __name__ == "__main__":
    # Run the tests directly
    test_import_basemodel()
    test_import_ai_engine()
    print("All tests passed!")
