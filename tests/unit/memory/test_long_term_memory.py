"""Tests for long-term memory.

This module contains tests for the LongTermMemory class.
"""
import os
import json
import shutil
import tempfile
import uuid
import pytest
from pathlib import Path

from ailf.memory.long_term import LongTermMemory
from ailf.schemas.memory import UserProfile, KnowledgeFact


class TestLongTermMemory:
    """Tests for LongTermMemory class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for storing memory files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after tests
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory_store(self, temp_dir):
        """Create a long-term memory store for testing."""
        return LongTermMemory(base_storage_path=temp_dir)
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_user_profile(self, memory_store):
        """Test storing and retrieving a user profile."""
        user_id = "test_user_1"
        test_profile = UserProfile(
            user_id=user_id,
            preferences={"theme": "dark", "notifications": "hourly"},
            history_summary="Test user history"
        )
        
        # Store the profile
        await memory_store.store_item(test_profile)
        
        # Retrieve the profile
        retrieved_profile = await memory_store.retrieve_item(UserProfile, user_id)
        
        # Validate retrieved profile
        assert retrieved_profile is not None
        assert retrieved_profile.user_id == user_id
        assert retrieved_profile.preferences == {"theme": "dark", "notifications": "hourly"}
        assert retrieved_profile.history_summary == "Test user history"
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_knowledge_fact(self, memory_store):
        """Test storing and retrieving a knowledge fact."""
        fact_id = str(uuid.uuid4())
        test_fact = KnowledgeFact(
            fact_id=fact_id,
            content="The Earth rotates on its axis.",
            source="Science textbook",
            tags=["earth", "science", "rotation"],
            confidence_score=0.95
        )
        
        # Store the fact
        await memory_store.store_item(test_fact)
        
        # Retrieve the fact
        retrieved_fact = await memory_store.retrieve_item(KnowledgeFact, fact_id)
        
        # Validate retrieved fact
        assert retrieved_fact is not None
        assert retrieved_fact.fact_id == fact_id
        assert retrieved_fact.content == "The Earth rotates on its axis."
        assert retrieved_fact.source == "Science textbook"
        assert retrieved_fact.tags == ["earth", "science", "rotation"]
        assert retrieved_fact.confidence_score == 0.95
    
    @pytest.mark.asyncio
    async def test_file_storage_structure(self, memory_store, temp_dir):
        """Test that files are stored in the correct directory structure."""
        # Store a user profile
        user_id = "test_user_structure"
        test_profile = UserProfile(user_id=user_id, preferences={"theme": "light"})
        await memory_store.store_item(test_profile)
        
        # Store a knowledge fact
        fact_id = "test_fact_structure"
        test_fact = KnowledgeFact(fact_id=fact_id, content="Test fact content")
        await memory_store.store_item(test_fact)
        
        # Check directory structure
        user_profile_path = Path(temp_dir) / "userprofile" / f"{user_id}.json"
        knowledge_fact_path = Path(temp_dir) / "knowledgefact" / f"{fact_id}.json"
        
        assert user_profile_path.exists(), f"User profile file not found at {user_profile_path}"
        assert knowledge_fact_path.exists(), f"Knowledge fact file not found at {knowledge_fact_path}"
        
        # Check file content
        with open(user_profile_path, 'r') as f:
            user_data = json.load(f)
            assert user_data["user_id"] == user_id
            assert user_data["preferences"] == {"theme": "light"}
        
        with open(knowledge_fact_path, 'r') as f:
            fact_data = json.load(f)
            assert fact_data["fact_id"] == fact_id
            assert fact_data["content"] == "Test fact content"
    
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_item(self, memory_store):
        """Test retrieving a non-existent item."""
        nonexistent_id = "does_not_exist"
        
        retrieved_profile = await memory_store.retrieve_item(UserProfile, nonexistent_id)
        assert retrieved_profile is None
        
        retrieved_fact = await memory_store.retrieve_item(KnowledgeFact, nonexistent_id)
        assert retrieved_fact is None
    
    @pytest.mark.asyncio
    async def test_delete_item(self, memory_store):
        """Test deleting an item."""
        # Store a user profile
        user_id = "test_user_to_delete"
        test_profile = UserProfile(user_id=user_id, preferences={"theme": "dark"})
        await memory_store.store_item(test_profile)
        
        # Verify it exists
        retrieved_profile = await memory_store.retrieve_item(UserProfile, user_id)
        assert retrieved_profile is not None
        
        # Delete it
        result = await memory_store.delete_item(UserProfile, user_id)
        assert result is True
        
        # Verify it's gone
        retrieved_profile_after_delete = await memory_store.retrieve_item(UserProfile, user_id)
        assert retrieved_profile_after_delete is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_item(self, memory_store):
        """Test deleting a non-existent item."""
        result = await memory_store.delete_item(UserProfile, "nonexistent_id")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_list_item_ids(self, memory_store):
        """Test listing all item IDs of a specific model type."""
        # Store several user profiles
        user_ids = ["user1", "user2", "user3"]
        for user_id in user_ids:
            await memory_store.store_item(UserProfile(user_id=user_id))
        
        # List all user profile IDs
        retrieved_ids = await memory_store.list_item_ids(UserProfile)
        
        # Verify all IDs are in the list
        for user_id in user_ids:
            assert user_id in retrieved_ids
        
        # Verify count
        assert len(retrieved_ids) == len(user_ids)
    
    @pytest.mark.asyncio
    async def test_list_item_ids_empty_directory(self, memory_store):
        """Test listing item IDs when directory is empty."""
        # The KnowledgeFact directory might not exist yet or be empty
        ids = await memory_store.list_item_ids(KnowledgeFact)
        assert isinstance(ids, list)
    
    @pytest.mark.asyncio
    async def test_update_existing_item(self, memory_store):
        """Test updating an existing item."""
        # Store initial user profile
        user_id = "test_update_user"
        initial_profile = UserProfile(
            user_id=user_id,
            preferences={"theme": "light"},
            history_summary="Initial history"
        )
        await memory_store.store_item(initial_profile)
        
        # Create updated profile with same ID
        updated_profile = UserProfile(
            user_id=user_id,
            preferences={"theme": "dark", "language": "en-US"},
            history_summary="Updated history"
        )
        
        # Update by storing again
        await memory_store.store_item(updated_profile)
        
        # Retrieve the profile
        retrieved_profile = await memory_store.retrieve_item(UserProfile, user_id)
        
        # Verify updated values
        assert retrieved_profile is not None
        assert retrieved_profile.user_id == user_id
        assert retrieved_profile.preferences == {"theme": "dark", "language": "en-US"}
        assert retrieved_profile.history_summary == "Updated history"
