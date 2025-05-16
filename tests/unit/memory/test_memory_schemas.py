"""Tests for memory schemas.

This module contains tests for the Pydantic models in the ailf.schemas.memory module.
"""
import time
import uuid
from datetime import datetime
import pytest
from pydantic import ValidationError
from datetime import datetime

from ailf.schemas.memory import MemoryItem, UserProfile, KnowledgeFact, MemoryType


class TestMemoryItem:
    """Tests for the MemoryItem schema."""

    def test_create_with_defaults(self):
        """Test creating a memory item with default values."""
        test_id = "test_id"
        test_content = "test_content"
        
        item = MemoryItem(item_id=test_id, type=MemoryType.OBSERVATION, content=test_content)
        
        assert item.item_id == test_id
        assert item.type == MemoryType.OBSERVATION
        assert item.content == test_content
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.metadata, dict)
        assert item.metadata == {}
    
    def test_create_with_custom_values(self):
        """Test creating a memory item with custom values."""
        test_id = "test_id"
        test_content = {"key": "value"}
        test_metadata = {"source": "user", "confidence": 0.95}
        
        item = MemoryItem(
            item_id=test_id,
            type=MemoryType.ACTION,
            content=test_content,
            importance=0.8,
            metadata=test_metadata
        )
        
        assert item.item_id == test_id
        assert item.type == MemoryType.ACTION
        assert item.content == test_content
        assert item.importance == 0.8
        assert item.metadata == test_metadata
    
    def test_missing_required_fields(self):
        """Test validation fails if required fields are missing."""
        # Missing type
        with pytest.raises(ValidationError):
            MemoryItem(item_id="test_id", content="test_content")
            
        # Missing content
        with pytest.raises(ValidationError):
            MemoryItem(item_id="test_id", type=MemoryType.OBSERVATION)
    
    def test_any_data_type_allowed(self):
        """Test that the content field accepts any data type."""
        # String
        item1 = MemoryItem(type=MemoryType.OBSERVATION, content="string data")
        assert item1.content == "string data"
        
        # Dict
        item2 = MemoryItem(type=MemoryType.OBSERVATION, content={"key": "value"})
        assert item2.content == {"key": "value"}
        
        # List
        item3 = MemoryItem(type=MemoryType.OBSERVATION, content=[1, 2, 3])
        assert item3.content == [1, 2, 3]
        
        # Number
        item4 = MemoryItem(type=MemoryType.OBSERVATION, content=42)
        assert item4.content == 42


class TestUserProfile:
    """Tests for the UserProfile schema."""
    
    def test_create_with_defaults(self):
        """Test creating a user profile with default values."""
        user_id = "user123"
        
        profile = UserProfile(user_id=user_id)
        
        assert profile.user_id == user_id
        assert isinstance(profile.preferences, dict)
        assert profile.preferences == {}
        assert isinstance(profile.history, list)
        assert profile.history == []
        assert isinstance(profile.properties, dict)
        assert profile.properties == {}
    
    def test_create_with_custom_values(self):
        """Test creating a user profile with custom values."""
        user_id = "user123"
        preferences = {
            "theme": "dark",
            "language": "en-US",
            "notification_frequency": "daily"
        }
        properties = {
            "interests": ["AI", "machine learning"],
            "skill_level": "intermediate"
        }
        
        profile = UserProfile(
            user_id=user_id,
            preferences=preferences,
            properties=properties
        )
        
        assert profile.user_id == user_id
        assert profile.preferences == preferences
        assert profile.properties == properties
    
    def test_missing_required_fields(self):
        """Test validation fails if required fields are missing."""
        # Missing user_id
        with pytest.raises(ValidationError):
            UserProfile()


class TestKnowledgeFact:
    """Tests for the KnowledgeFact schema."""
    
    def test_create_with_defaults(self):
        """Test creating a knowledge fact with default values."""
        content = "Python is a high-level programming language."
        
        fact = KnowledgeFact(content=content)
        
        assert fact.content == content
        assert fact.type == MemoryType.OTHER
        assert fact.source is None
        assert fact.confidence == 1.0
        assert isinstance(fact.created_at, datetime)
        assert isinstance(fact.metadata, dict)
        assert fact.metadata == {}
    
    def test_create_with_custom_values(self):
        """Test creating a knowledge fact with custom values."""
        content = "Python is a high-level programming language."
        source = "programming_book_12345"
        confidence = 0.92
        metadata = {"category": "programming", "tags": ["python", "language"]}
        
        fact = KnowledgeFact(
            content=content,
            source=source,
            confidence=confidence,
            metadata=metadata
        )
        
        assert fact.content == content
        assert fact.source == source
        assert fact.confidence == confidence
        assert fact.metadata == metadata
    
    def test_missing_required_fields(self):
        """Test validation fails if required fields are missing."""
        # Content is not required since it inherits from MemoryItem which requires type and content
        # If we explicitly specify type but not content, it should fail
        with pytest.raises(ValidationError):
            KnowledgeFact(type=MemoryType.OTHER)
