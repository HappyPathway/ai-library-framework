"""Tests for input adapters.

This module contains tests for the input adapters in the ailf.interaction.adapters module.
"""
import json
import pytest
from typing import Any, Dict
from unittest.mock import AsyncMock

from ailf.interaction.adapters import BaseInputAdapter
from ailf.schemas.interaction import (
    AnyInteractionMessage,
    TextMessage,
    StructuredDataMessage,
    BinaryMessage,
    TextMessagePayload,
    StructuredDataMessagePayload,
    BinaryMessagePayload,
    MessageModality,
)


class TestBaseInputAdapter:
    """Tests for the BaseInputAdapter abstract class."""
    
    def test_abstract_class(self):
        """Test that BaseInputAdapter is an abstract class that cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseInputAdapter()


class MockTextInputAdapter(BaseInputAdapter[str]):
    """Mock text input adapter for testing."""
    
    async def parse(self, raw_input: str) -> AnyInteractionMessage:
        """Parse raw text input."""
        return TextMessage(payload=TextMessagePayload(text=raw_input))


class MockJsonInputAdapter(BaseInputAdapter[str]):
    """Mock JSON input adapter for testing."""
    
    async def parse(self, raw_input: str) -> AnyInteractionMessage:
        """Parse raw JSON input."""
        try:
            data = json.loads(raw_input)
            return StructuredDataMessage(payload=StructuredDataMessagePayload(data=data))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON input")


class MockBinaryInputAdapter(BaseInputAdapter[bytes]):
    """Mock binary input adapter for testing."""
    
    async def parse(self, raw_input: bytes) -> AnyInteractionMessage:
        """Parse raw binary input."""
        return BinaryMessage(
            payload=BinaryMessagePayload(
                data=raw_input,
                content_type="application/octet-stream",
            )
        )


class TestTextInputAdapter:
    """Tests for text input adapter implementation."""
    
    @pytest.mark.asyncio
    async def test_parse_text(self):
        """Test parsing text input."""
        adapter = MockTextInputAdapter()
        result = await adapter.parse("Hello, world!")
        
        assert isinstance(result, TextMessage)
        assert result.payload.text == "Hello, world!"
        assert result.header.modality == MessageModality.TEXT
    
    @pytest.mark.asyncio
    async def test_empty_text(self):
        """Test parsing empty text."""
        adapter = MockTextInputAdapter()
        
        # Empty text should still work with the adapter
        result = await adapter.parse("")
        assert result.payload.text == ""


class TestJsonInputAdapter:
    """Tests for JSON input adapter implementation."""
    
    @pytest.mark.asyncio
    async def test_parse_valid_json(self):
        """Test parsing valid JSON input."""
        adapter = MockJsonInputAdapter()
        json_str = '{"name": "Test User", "age": 30}'
        
        result = await adapter.parse(json_str)
        
        assert isinstance(result, StructuredDataMessage)
        assert result.payload.data == {"name": "Test User", "age": 30}
        assert result.header.modality == MessageModality.STRUCTURED_DATA
    
    @pytest.mark.asyncio
    async def test_parse_nested_json(self):
        """Test parsing nested JSON input."""
        adapter = MockJsonInputAdapter()
        json_str = '''
        {
            "user": {
                "name": "Test User",
                "profile": {
                    "interests": ["AI", "Python", "Testing"]
                }
            },
            "settings": {
                "theme": "dark"
            }
        }
        '''
        
        result = await adapter.parse(json_str)
        
        assert isinstance(result, StructuredDataMessage)
        assert result.payload.data["user"]["name"] == "Test User"
        assert result.payload.data["user"]["profile"]["interests"] == ["AI", "Python", "Testing"]
        assert result.payload.data["settings"]["theme"] == "dark"
    
    @pytest.mark.asyncio
    async def test_invalid_json(self):
        """Test parsing invalid JSON input."""
        adapter = MockJsonInputAdapter()
        invalid_json = '{name: "Test User", age: 30}'  # Missing quotes around keys
        
        with pytest.raises(ValueError, match="Invalid JSON input"):
            await adapter.parse(invalid_json)


class TestBinaryInputAdapter:
    """Tests for binary input adapter implementation."""
    
    @pytest.mark.asyncio
    async def test_parse_binary(self):
        """Test parsing binary input."""
        adapter = MockBinaryInputAdapter()
        binary_data = b'\x00\x01\x02\x03\x04'
        
        result = await adapter.parse(binary_data)
        
        assert isinstance(result, BinaryMessage)
        assert result.payload.data == binary_data
        assert result.payload.content_type == "application/octet-stream"
        assert result.header.modality == MessageModality.BINARY


class TestCustomInputAdapter(BaseInputAdapter[Dict[str, Any]]):
    """Test implementation for custom complex input adapter."""
    
    def __init__(self):
        """Initialize the adapter."""
        self.validate_input = AsyncMock(return_value=True)
        self.preprocess_input = AsyncMock(return_value={"processed": True, "data": "test"})
    
    async def parse(self, raw_input: Dict[str, Any]) -> AnyInteractionMessage:
        """Parse raw dictionary input."""
        # Call the mocked validation and preprocessing methods
        valid = await self.validate_input(raw_input)
        if not valid:
            raise ValueError("Invalid input")
        
        processed = await self.preprocess_input(raw_input)
        return StructuredDataMessage(payload=StructuredDataMessagePayload(data=processed))


class TestComplexAdapterImplementation:
    """Tests for a more complex adapter implementation."""
    
    @pytest.mark.asyncio
    async def test_adapter_flow(self):
        """Test the full flow of a custom adapter with validation and preprocessing."""
        adapter = TestCustomInputAdapter()
        
        # Configure mocks
        adapter.validate_input.return_value = True
        adapter.preprocess_input.return_value = {"processed": True, "key": "value"}
        
        # Call parse
        raw_input = {"type": "test", "content": "example"}
        result = await adapter.parse(raw_input)
        
        # Verify mocks were called with correct arguments
        adapter.validate_input.assert_called_once_with(raw_input)
        adapter.preprocess_input.assert_called_once_with(raw_input)
        
        # Verify result
        assert isinstance(result, StructuredDataMessage)
        assert result.payload.data == {"processed": True, "key": "value"}
    
    @pytest.mark.asyncio
    async def test_validation_failure(self):
        """Test adapter behavior when validation fails."""
        adapter = TestCustomInputAdapter()
        
        # Configure validation to fail
        adapter.validate_input.return_value = False
        
        # Call parse with invalid input
        with pytest.raises(ValueError, match="Invalid input"):
            await adapter.parse({"invalid": "input"})
        
        # Verify validate was called but preprocess was not
        adapter.validate_input.assert_called_once()
        adapter.preprocess_input.assert_not_called()
