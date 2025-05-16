"""Tests for the interaction manager.

This module contains tests for the InteractionManager class in the ailf.interaction.manager module.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Optional, Any

from ailf.interaction.manager import InteractionManager, MessageHandler
from ailf.interaction.adapters import BaseInputAdapter, BaseOutputAdapter
from ailf.schemas.interaction import (
    TextMessage,
    StructuredDataMessage,
    BinaryMessage,
    AnyInteractionMessage,
    TextMessagePayload,
    StructuredDataMessagePayload,
    BinaryMessagePayload,
)


class MockInputAdapter(BaseInputAdapter[str]):
    """Mock input adapter for testing."""
    
    async def parse(self, raw_input: str) -> AnyInteractionMessage:
        """Mock implementation that returns a TextMessage."""
        return TextMessage(payload=TextMessagePayload(text=raw_input))


class MockInputAdapterWithError(BaseInputAdapter[str]):
    """Mock input adapter that raises an error."""
    
    async def parse(self, raw_input: str) -> AnyInteractionMessage:
        """Mock implementation that raises a ValueError."""
        raise ValueError("Invalid input")


class MockOutputAdapter(BaseOutputAdapter[str]):
    """Mock output adapter for testing."""
    
    async def format(self, message: AnyInteractionMessage) -> str:
        """Mock implementation that returns a string."""
        if isinstance(message, TextMessage):
            return f"formatted: {message.payload.text}"
        elif isinstance(message, StructuredDataMessage):
            return f"formatted data: {message.payload.data}"
        else:
            return "formatted: unknown message type"


class MockOutputAdapterWithError(BaseOutputAdapter[str]):
    """Mock output adapter that raises an error."""
    
    async def format(self, message: AnyInteractionMessage) -> str:
        """Mock implementation that raises a ValueError."""
        raise ValueError("Cannot format message")


async def mock_handler(message: AnyInteractionMessage) -> Optional[AnyInteractionMessage]:
    """Mock message handler that returns a TextMessage."""
    response_text = f"Response to: {message.payload.text}" if isinstance(message, TextMessage) else "Response"
    return TextMessage(payload=TextMessagePayload(text=response_text))


async def mock_handler_none_response(message: AnyInteractionMessage) -> Optional[AnyInteractionMessage]:
    """Mock message handler that returns None."""
    return None


async def mock_handler_invalid_response(message: AnyInteractionMessage) -> Any:
    """Mock message handler that returns an invalid response."""
    return "not a valid message object"


async def mock_handler_with_error(message: AnyInteractionMessage) -> Optional[AnyInteractionMessage]:
    """Mock message handler that raises an exception."""
    raise RuntimeError("Handler error")


class TestInteractionManager:
    """Tests for the InteractionManager class."""
    
    def test_init_valid(self):
        """Test initializing with valid parameters."""
        input_adapter = MockInputAdapter()
        output_adapter = MockOutputAdapter()
        handler = mock_handler
        
        manager = InteractionManager(
            input_adapter=input_adapter,
            output_adapter=output_adapter,
            message_handler=handler,
        )
        
        assert manager.input_adapter == input_adapter
        assert manager.output_adapter == output_adapter
        assert manager.message_handler == handler
    
    def test_init_invalid_input_adapter(self):
        """Test initializing with an invalid input adapter."""
        with pytest.raises(TypeError, match="input_adapter must be an instance of BaseInputAdapter"):
            InteractionManager(
                input_adapter="not an adapter",  # type: ignore
                output_adapter=MockOutputAdapter(),
                message_handler=mock_handler,
            )
    
    def test_init_invalid_output_adapter(self):
        """Test initializing with an invalid output adapter."""
        with pytest.raises(TypeError, match="output_adapter must be an instance of BaseOutputAdapter"):
            InteractionManager(
                input_adapter=MockInputAdapter(),
                output_adapter="not an adapter",  # type: ignore
                message_handler=mock_handler,
            )
    
    def test_init_invalid_handler(self):
        """Test initializing with an invalid message handler."""
        with pytest.raises(TypeError, match="message_handler must be a callable awaitable function"):
            InteractionManager(
                input_adapter=MockInputAdapter(),
                output_adapter=MockOutputAdapter(),
                message_handler="not a handler",  # type: ignore
            )
    
    @pytest.mark.asyncio
    async def test_handle_raw_input_success(self):
        """Test successful handling of raw input."""
        manager = InteractionManager(
            input_adapter=MockInputAdapter(),
            output_adapter=MockOutputAdapter(),
            message_handler=mock_handler,
        )
        
        result = await manager.handle_raw_input("Hello, world!")
        
        assert result == "formatted: Response to: Hello, world!"
    
    @pytest.mark.asyncio
    async def test_handle_raw_input_none_response(self):
        """Test handling when the message handler returns None."""
        manager = InteractionManager(
            input_adapter=MockInputAdapter(),
            output_adapter=MockOutputAdapter(),
            message_handler=mock_handler_none_response,
        )
        
        result = await manager.handle_raw_input("Hello, world!")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_raw_input_parsing_error(self):
        """Test handling when input parsing fails."""
        manager = InteractionManager(
            input_adapter=MockInputAdapterWithError(),
            output_adapter=MockOutputAdapter(),
            message_handler=mock_handler,
        )
        
        with pytest.raises(ValueError, match="Invalid input"):
            await manager.handle_raw_input("Hello, world!")
    
    @pytest.mark.asyncio
    async def test_handle_raw_input_formatting_error(self):
        """Test handling when output formatting fails."""
        manager = InteractionManager(
            input_adapter=MockInputAdapter(),
            output_adapter=MockOutputAdapterWithError(),
            message_handler=mock_handler,
        )
        
        with pytest.raises(ValueError, match="Cannot format message"):
            await manager.handle_raw_input("Hello, world!")
    
    @pytest.mark.asyncio
    async def test_handle_raw_input_handler_error(self):
        """Test handling when the message handler raises an exception."""
        manager = InteractionManager(
            input_adapter=MockInputAdapter(),
            output_adapter=MockOutputAdapter(),
            message_handler=mock_handler_with_error,
        )
        
        with pytest.raises(RuntimeError, match="Handler error"):
            await manager.handle_raw_input("Hello, world!")
    
    @pytest.mark.asyncio
    async def test_handle_raw_input_invalid_response(self):
        """Test handling when the message handler returns an invalid response."""
        manager = InteractionManager(
            input_adapter=MockInputAdapter(),
            output_adapter=MockOutputAdapter(),
            message_handler=mock_handler_invalid_response,
        )
        
        with pytest.raises(ValueError, match="Message handler returned an invalid type"):
            await manager.handle_raw_input("Hello, world!")


class TestInteractionManagerIntegration:
    """Integration tests for InteractionManager with mock components."""
    
    @pytest.mark.asyncio
    async def test_text_flow(self):
        """Test the complete flow from raw input to raw output for text messages."""
        # Create mock adapters
        input_adapter = MockInputAdapter()
        output_adapter = MockOutputAdapter()
        
        # Create a mock handler that transforms text
        async def handler(message: AnyInteractionMessage) -> AnyInteractionMessage:
            if isinstance(message, TextMessage):
                return TextMessage(payload=TextMessagePayload(text=message.payload.text.upper()))
            return message
        
        # Create manager
        manager = InteractionManager(
            input_adapter=input_adapter,
            output_adapter=output_adapter,
            message_handler=handler,
        )
        
        # Process raw input
        result = await manager.handle_raw_input("hello world")
        
        # Verify result
        assert result == "formatted: HELLO WORLD"
    
    @pytest.mark.asyncio
    async def test_structured_data_flow(self):
        """Test handling structured data through the complete flow."""
        # Create specialized adapters for this test
        class JsonInputAdapter(BaseInputAdapter[str]):
            async def parse(self, raw_input: str) -> AnyInteractionMessage:
                import json
                return StructuredDataMessage(payload=StructuredDataMessagePayload(data=json.loads(raw_input)))
        
        class JsonOutputAdapter(BaseOutputAdapter[str]):
            async def format(self, message: AnyInteractionMessage) -> str:
                import json
                if isinstance(message, StructuredDataMessage):
                    return json.dumps(message.payload.data)
                return "{}"
        
        # Create a handler that transforms data
        async def handler(message: AnyInteractionMessage) -> AnyInteractionMessage:
            if isinstance(message, StructuredDataMessage):
                data = message.payload.data.copy()
                if "name" in data:
                    data["greeting"] = f"Hello, {data['name']}!"
                return StructuredDataMessage(payload=StructuredDataMessagePayload(data=data))
            return message
        
        # Create manager
        manager = InteractionManager(
            input_adapter=JsonInputAdapter(),
            output_adapter=JsonOutputAdapter(),
            message_handler=handler,
        )
        
        # Process JSON input
        result = await manager.handle_raw_input('{"name": "Alice", "age": 30}')
        
        # Verify result
        import json
        parsed = json.loads(result)
        assert "greeting" in parsed
        assert parsed["greeting"] == "Hello, Alice!"
        assert parsed["name"] == "Alice"
        assert parsed["age"] == 30
