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
from ailf.schemas.memory import UserProfile, KnowledgeFact, MemoryType


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
            properties={"interests": ["AI", "programming"]}
        )
        
        # Store the profile
        await memory_store.store_item(test_profile)
        
        # Retrieve the profile
        retrieved_profile = await memory_store.retrieve_item(UserProfile, user_id)
        
        # Validate retrieved profile
        assert retrieved_profile is not None
        assert retrieved_profile.user_id == user_id
        assert retrieved_profile.preferences == {"theme": "dark", "notifications": "hourly"}
        assert retrieved_profile.properties == {"interests": ["AI", "programming"]}
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_knowledge_fact(self, memory_store):
        """Test storing and retrieving a knowledge fact."""
        fact_id = str(uuid.uuid4())
        print(f"KnowledgeFact test using ID: {fact_id}")
        test_fact = KnowledgeFact(
            id=fact_id,
            content="Python is a programming language.",
            source="documentation",
            confidence=0.95
        )
        
        # Debug: Print the fact object
        print(f"Test fact: {test_fact}")
        print(f"Test fact dict: {test_fact.model_dump()}")
        
        # Store the fact
        await memory_store.store_item(test_fact)
        
        # Debug: Check if file actually exists
        import pathlib
        expected_path = pathlib.Path(memory_store.base_path / "KnowledgeFact" / f"{fact_id}.json")
        print(f"Expected file path: {expected_path}")
        print(f"File exists: {expected_path.exists()}")
        
        # Debug: Check file content if it exists
        if expected_path.exists():
            with open(expected_path, "r") as f:
                print(f"File content: {f.read()}")
        
        # Retrieve the fact
        retrieved_fact = await memory_store.retrieve_item(KnowledgeFact, fact_id)
        print(f"Retrieved fact: {retrieved_fact}")
        
        # Validate retrieved fact
        assert retrieved_fact is not None
        assert retrieved_fact.id == fact_id
        assert retrieved_fact.content == "Python is a programming language."
        assert retrieved_fact.source == "documentation"
        assert retrieved_fact.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_file_storage_structure(self, memory_store, temp_dir):
        """Test the file storage structure."""
        # Store a user profile
        user_id = "test_user_2"
        test_profile = UserProfile(
            user_id=user_id,
            preferences={"theme": "light"}
        )
        await memory_store.store_item(test_profile)
        
        # Check that the file exists (use the actual class name with correct case)
        user_path = Path(temp_dir) / "UserProfile" / f"{user_id}.json"
        assert user_path.exists()
        
        # Verify file contents
        with open(user_path, 'r') as f:
            data = json.load(f)
            assert data["user_id"] == user_id
            assert data["preferences"] == {"theme": "light"}
    
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_item(self, memory_store):
        """Test retrieving a non-existent item."""
        retrieved_item = await memory_store.retrieve_item(UserProfile, "nonexistent_id")
        assert retrieved_item is None
    
    @pytest.mark.asyncio
    async def test_delete_item(self, memory_store):
        """Test deleting an item."""
        # Store an item
        user_id = "test_user_3"
        test_profile = UserProfile(user_id=user_id)
        await memory_store.store_item(test_profile)
        
        # Verify it exists
        assert await memory_store.retrieve_item(UserProfile, user_id) is not None
        
        # Delete it
        success = await memory_store.delete_item(UserProfile, user_id)
        assert success is True
        
        # Verify it's gone
        assert await memory_store.retrieve_item(UserProfile, user_id) is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_item(self, memory_store):
        """Test deleting a non-existent item."""
        # Attempt to delete a non-existent item
        success = await memory_store.delete_item(UserProfile, "nonexistent_id")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_list_item_ids(self, memory_store):
        """Test listing item IDs."""
        # Store multiple items
        user_ids = ["user1", "user2", "user3"]
        for user_id in user_ids:
            await memory_store.store_item(UserProfile(user_id=user_id))
        
        # List the IDs
        retrieved_ids = await memory_store.list_item_ids(UserProfile)
        
        # Check that all stored IDs are retrieved
        assert set(retrieved_ids) == set(user_ids)
    
    @pytest.mark.asyncio
    async def test_list_item_ids_empty_directory(self, memory_store):
        """Test listing item IDs when no items exist."""
        # List IDs for a type with no stored items
        retrieved_ids = await memory_store.list_item_ids(KnowledgeFact)
        assert retrieved_ids == []
    
    @pytest.mark.asyncio
    async def test_update_existing_item(self, memory_store):
        """Test updating an existing item."""
        # Store initial item
        user_id = "test_user_4"
        test_profile = UserProfile(
            user_id=user_id,
            preferences={"theme": "dark"}
        )
        await memory_store.store_item(test_profile)
        
        # Update the item
        updated_profile = UserProfile(
            user_id=user_id,
            preferences={"theme": "light", "language": "en"}
        )
        await memory_store.store_item(updated_profile)
        
        # Retrieve the updated item
        retrieved_profile = await memory_store.retrieve_item(UserProfile, user_id)
        
        # Verify it was updated
        assert retrieved_profile.preferences == {"theme": "light", "language": "en"}
