"""Tests for memory schemas.

This module contains tests for the Pydantic models in the ailf.schemas.memory module.
"""
import time
import uuid
import pytest
from pydantic import ValidationError

from ailf.schemas.memory import MemoryItem, UserProfile, KnowledgeFact


class TestMemoryItem:
    """Tests for the MemoryItem schema."""

    def test_create_with_defaults(self):
        """Test creating a memory item with default values."""
        test_id = "test_id"
        test_data = "test_data"
        
        item = MemoryItem(item_id=test_id, data=test_data)
        
        assert item.item_id == test_id
        assert item.data == test_data
        assert isinstance(item.timestamp, float)
        assert item.timestamp <= time.time()  # Should be less than or equal to current time
        assert isinstance(item.metadata, dict)
        assert item.metadata == {}
    
    def test_create_with_custom_values(self):
        """Test creating a memory item with custom values."""
        test_id = "test_id"
        test_data = {"key": "value"}
        test_timestamp = time.time() - 1000  # 1000 seconds ago
        test_metadata = {"source": "user", "confidence": 0.95}
        
        item = MemoryItem(
            item_id=test_id,
            data=test_data,
            timestamp=test_timestamp,
            metadata=test_metadata
        )
        
        assert item.item_id == test_id
        assert item.data == test_data
        assert item.timestamp == test_timestamp
        assert item.metadata == test_metadata
    
    def test_missing_required_fields(self):
        """Test validation fails if required fields are missing."""
        # Missing item_id
        with pytest.raises(ValidationError):
            MemoryItem(data="test_data")
        
        # Missing data
        with pytest.raises(ValidationError):
            MemoryItem(item_id="test_id")
    
    def test_any_data_type_allowed(self):
        """Test that 'data' field accepts any data type."""
        # String data
        item1 = MemoryItem(item_id="id1", data="string data")
        assert item1.data == "string data"
        
        # Dict data
        item2 = MemoryItem(item_id="id2", data={"key": "value"})
        assert item2.data == {"key": "value"}
        
        # List data
        item3 = MemoryItem(item_id="id3", data=[1, 2, 3])
        assert item3.data == [1, 2, 3]
        
        # Custom object data
        class TestObj:
            pass
        test_obj = TestObj()
        item4 = MemoryItem(item_id="id4", data=test_obj)
        assert item4.data is test_obj


class TestUserProfile:
    """Tests for the UserProfile schema."""
    
    def test_create_with_defaults(self):
        """Test creating a user profile with default values."""
        user_id = "user123"
        
        profile = UserProfile(user_id=user_id)
        
        assert profile.user_id == user_id
        assert isinstance(profile.preferences, dict)
        assert profile.preferences == {}
        assert profile.history_summary is None
    
    def test_create_with_custom_values(self):
        """Test creating a user profile with custom values."""
        user_id = "user123"
        preferences = {
            "theme": "dark",
            "language": "en-US",
            "notification_frequency": "daily"
        }
        history_summary = "User has shown interest in AI and machine learning topics."
        
        profile = UserProfile(
            user_id=user_id,
            preferences=preferences,
            history_summary=history_summary
        )
        
        assert profile.user_id == user_id
        assert profile.preferences == preferences
        assert profile.history_summary == history_summary
    
    def test_missing_required_fields(self):
        """Test validation fails if required fields are missing."""
        # Missing user_id
        with pytest.raises(ValidationError):
            UserProfile()


class TestKnowledgeFact:
    """Tests for the KnowledgeFact schema."""
    
    def test_create_with_defaults(self):
        """Test creating a knowledge fact with default values."""
        fact_id = str(uuid.uuid4())
        content = "Python is a high-level programming language."
        
        fact = KnowledgeFact(fact_id=fact_id, content=content)
        
        assert fact.fact_id == fact_id
        assert fact.content == content
        assert fact.source is None
        assert isinstance(fact.tags, list)
        assert fact.tags == []
        assert fact.confidence_score is None
        assert isinstance(fact.created_at, float)
        assert fact.created_at <= time.time()
        assert fact.last_accessed_at is None
    
    def test_create_with_custom_values(self):
        """Test creating a knowledge fact with custom values."""
        fact_id = str(uuid.uuid4())
        content = "Python is a high-level programming language."
        source = "programming_book_12345"
        tags = ["python", "programming", "language"]
        confidence_score = 0.92
        created_at = time.time() - 86400  # 1 day ago
        last_accessed_at = time.time() - 3600  # 1 hour ago
        
        fact = KnowledgeFact(
            fact_id=fact_id,
            content=content,
            source=source,
            tags=tags,
            confidence_score=confidence_score,
            created_at=created_at,
            last_accessed_at=last_accessed_at
        )
        
        assert fact.fact_id == fact_id
        assert fact.content == content
        assert fact.source == source
        assert fact.tags == tags
        assert fact.confidence_score == confidence_score
        assert fact.created_at == created_at
        assert fact.last_accessed_at == last_accessed_at
    
    def test_missing_required_fields(self):
        """Test validation fails if required fields are missing."""
        # Missing fact_id
        with pytest.raises(ValidationError):
            KnowledgeFact(content="Test content")
        
        # Missing content
        with pytest.raises(ValidationError):
            KnowledgeFact(fact_id="test_id")
