"""Tests for interaction schemas.

This module contains tests for the Pydantic models in the ailf.schemas.interaction module.
"""
import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from ailf.schemas.interaction import (
    MessageModality,
    StandardMessageHeader,
    TextMessage,
    StructuredDataMessage,
    BinaryMessage,
    MultiModalMessage,
    AnyInteractionMessage,
    TextMessagePayload,
    StructuredDataMessagePayload,
    BinaryMessagePayload,
    MultiModalMessagePayload,
    MultiModalPart,
)


class TestMessageModality:
    """Tests for MessageModality enum."""

    def test_message_modality_values(self):
        """Test the available message modalities."""
        assert MessageModality.TEXT == "text"
        assert MessageModality.STRUCTURED_DATA == "structured_data"
        assert MessageModality.BINARY == "binary"
        assert MessageModality.IMAGE == "image"
        assert MessageModality.AUDIO == "audio"
        assert MessageModality.VIDEO == "video"
        assert MessageModality.MULTI_MODAL_CONTAINER == "multi_modal_container"


class TestStandardMessageHeader:
    """Tests for StandardMessageHeader."""

    def test_create_with_defaults(self):
        """Test creating a header with default values."""
        header = StandardMessageHeader(modality=MessageModality.TEXT)
        assert header.message_id is not None
        assert isinstance(header.message_id, uuid.UUID)
        assert header.correlation_id is None
        assert header.session_id is None
        assert header.user_id is None
        assert header.source_system is None
        assert header.target_system is None
        assert header.timestamp is not None
        assert isinstance(header.timestamp, datetime)
        assert header.timestamp.tzinfo == timezone.utc
        assert header.modality == MessageModality.TEXT
    
    def test_create_with_custom_values(self):
        """Test creating a header with custom values."""
        message_id = uuid.uuid4()
        correlation_id = uuid.uuid4()
        timestamp = datetime.now(timezone.utc)
        
        header = StandardMessageHeader(
            modality=MessageModality.TEXT,
            message_id=message_id,
            correlation_id=correlation_id,
            session_id="test-session",
            user_id="user123",
            source_system="client-app",
            target_system="agent",
            timestamp=timestamp,
        )
        
        assert header.message_id == message_id
        assert header.correlation_id == correlation_id
        assert header.session_id == "test-session"
        assert header.user_id == "user123"
        assert header.source_system == "client-app"
        assert header.target_system == "agent"
        assert header.timestamp == timestamp
    
    def test_serialization(self):
        """Test serialization to and from JSON."""
        original_header = StandardMessageHeader(
            modality=MessageModality.TEXT,
            session_id="test-session",
            user_id="user123",
            source_system="client-app",
            target_system="agent",
        )
        
        # Convert to dict and then create a new instance
        header_dict = original_header.model_dump()
        
        # Convert UUID to string for proper JSON serialization
        header_dict["message_id"] = str(header_dict["message_id"])
        
        # Convert datetime to string for JSON
        header_dict["timestamp"] = header_dict["timestamp"].isoformat()
        
        # Create a new instance from the dict
        new_header = StandardMessageHeader(
            message_id=uuid.UUID(header_dict["message_id"]),
            timestamp=datetime.fromisoformat(header_dict["timestamp"]),
            **{k: v for k, v in header_dict.items() if k not in ["message_id", "timestamp"]}
        )
        
        # Verify key fields match
        assert new_header.session_id == original_header.session_id
        assert new_header.user_id == original_header.user_id
        assert new_header.source_system == original_header.source_system
        assert new_header.target_system == original_header.target_system


class TestTextMessage:
    """Tests for TextMessage."""
    
    def test_create_text_message(self):
        """Test creating a text message."""
        message = TextMessage(payload=TextMessagePayload(text="Hello, world!"))
        
        assert message.header.modality == MessageModality.TEXT
        assert message.payload.text == "Hello, world!"
        assert message.header is not None
        assert isinstance(message.header, StandardMessageHeader)
    
    def test_create_with_custom_header(self):
        """Test creating a text message with a custom header."""
        header = StandardMessageHeader(
            modality=MessageModality.TEXT,
            session_id="test-session",
            user_id="user123",
        )
        
        message = TextMessage(
            payload=TextMessagePayload(text="Hello, world!"),
            header=header,
        )
        
        assert message.header == header
        assert message.header.session_id == "test-session"
        assert message.header.user_id == "user123"
    
    def test_text_message_validation(self):
        """Test validation of text message."""
        # Test with valid parameters
        valid_message = TextMessage(payload=TextMessagePayload(text="Valid text"))
        assert valid_message.payload.text == "Valid text"
        
        # Test that we can't create a message without a payload
        with pytest.raises(ValidationError):
            TextMessage()


class TestStructuredDataMessage:
    """Tests for StructuredDataMessage."""
    
    def test_create_structured_data_message(self):
        """Test creating a structured data message."""
        data = {"name": "Test User", "age": 30, "is_active": True}
        message = StructuredDataMessage(payload=StructuredDataMessagePayload(data=data))
        
        assert message.header.modality == MessageModality.STRUCTURED_DATA
        assert message.payload.data == data
        assert message.header is not None
    
    def test_complex_structured_data(self):
        """Test with complex nested data."""
        data = {
            "user": {
                "name": "Test User",
                "profile": {
                    "interests": ["AI", "Python", "Testing"],
                    "metrics": {
                        "activity_score": 98.6,
                        "login_count": 42
                    }
                }
            },
            "settings": {
                "notifications": True,
                "theme": "dark"
            }
        }
        
        message = StructuredDataMessage(payload=StructuredDataMessagePayload(data=data))
        assert message.payload.data == data
        assert message.payload.data["user"]["profile"]["interests"] == ["AI", "Python", "Testing"]
        assert message.payload.data["settings"]["theme"] == "dark"
    
    def test_structured_data_validation(self):
        """Test validation of structured data message."""
        # None data should fail
        with pytest.raises(ValidationError):
            StructuredDataMessage(data=None)


class TestBinaryMessage:
    """Tests for BinaryMessage."""
    
    def test_create_binary_message(self):
        """Test creating a binary message."""
        content = b"binary data"
        content_type = "application/octet-stream"
        
        message = BinaryMessage(
            payload=BinaryMessagePayload(
                data=content,
                content_type=content_type,
            )
        )
        
        assert message.header.modality == MessageModality.BINARY
        assert message.payload.data == content
        assert message.payload.content_type == content_type
    
    def test_with_filename(self):
        """Test with filename."""
        content = b"binary data"
        content_type = "application/octet-stream"
        filename = "test.bin"
        
        message = BinaryMessage(
            payload=BinaryMessagePayload(
                data=content,
                content_type=content_type,
                filename=filename,
            )
        )
        
        assert message.payload.filename == filename
    
    def test_binary_validation(self):
        """Test validation of binary message."""
        # Missing data should fail
        with pytest.raises(ValidationError):
            BinaryMessage(payload=BinaryMessagePayload(content_type="application/octet-stream"))
        
        # Missing content_type should fail
        with pytest.raises(ValidationError):
            BinaryMessage(payload=BinaryMessagePayload(data=b"binary data"))


class TestMultiModalMessage:
    """Tests for MultiModalMessage."""
    
    def test_create_multi_modal_message(self):
        """Test creating a multi-modal message."""
        text_part = MultiModalPart(
            part_id="text_part",
            modality=MessageModality.TEXT,
            data="Check out this image"
        )
        binary_part = MultiModalPart(
            part_id="image_part",
            modality=MessageModality.IMAGE,
            content_type="image/png",
            data=b"image data",
            metadata={"filename": "image.png"}
        )
        
        message = MultiModalMessage(
            payload=MultiModalMessagePayload(
                parts=[text_part, binary_part],
                primary_focus_part_id="image_part"
            )
        )
        
        assert message.header.modality == MessageModality.MULTI_MODAL_CONTAINER
        assert len(message.payload.parts) == 2
        assert message.payload.parts[0].part_id == "text_part"
        assert message.payload.parts[1].part_id == "image_part"
        assert message.payload.primary_focus_part_id == "image_part"
    
    def test_multi_modal_validation(self):
        """Test validation of multi-modal message."""
        # Test with valid parameters
        text_part = MultiModalPart(
            part_id="text_part",
            modality=MessageModality.TEXT,
            data="Valid text"
        )
        valid_message = MultiModalMessage(
            payload=MultiModalMessagePayload(parts=[text_part])
        )
        assert len(valid_message.payload.parts) == 1
        
        # Test that we can't create a message without a payload
        with pytest.raises(ValidationError):
            MultiModalMessage()


class TestAnyInteractionMessage:
    """Tests for AnyInteractionMessage type."""
    
    def test_text_message_is_valid(self):
        """Test that TextMessage is a valid AnyInteractionMessage."""
        message: AnyInteractionMessage = TextMessage(payload=TextMessagePayload(text="Hello, world!"))
        assert message.header.modality == MessageModality.TEXT
        assert message.payload.text == "Hello, world!"
    
    def test_structured_data_message_is_valid(self):
        """Test that StructuredDataMessage is a valid AnyInteractionMessage."""
        message: AnyInteractionMessage = StructuredDataMessage(
            payload=StructuredDataMessagePayload(data={"key": "value"})
        )
        assert message.header.modality == MessageModality.STRUCTURED_DATA
        assert message.payload.data == {"key": "value"}
    
    def test_binary_message_is_valid(self):
        """Test that BinaryMessage is a valid AnyInteractionMessage."""
        message: AnyInteractionMessage = BinaryMessage(
            payload=BinaryMessagePayload(
                data=b"binary data",
                content_type="application/octet-stream",
            )
        )
        assert message.header.modality == MessageModality.BINARY
        assert message.payload.data == b"binary data"
    
    def test_multi_modal_message_is_valid(self):
        """Test that MultiModalMessage is a valid AnyInteractionMessage."""
        text_part = MultiModalPart(
            part_id="text_part",
            modality=MessageModality.TEXT,
            data="Hello"
        )
        binary_part = MultiModalPart(
            part_id="binary_part",
            modality=MessageModality.BINARY,
            content_type="application/octet-stream",
            data=b"binary data"
        )
        
        message: AnyInteractionMessage = MultiModalMessage(
            payload=MultiModalMessagePayload(
                parts=[text_part, binary_part]
            )
        )
        assert message.header.modality == MessageModality.MULTI_MODAL_CONTAINER
        assert len(message.payload.parts) == 2
