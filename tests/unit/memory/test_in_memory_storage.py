"""Tests for in_memory storage.

This module contains tests for the InMemoryShortTermMemory class.
"""
import asyncio
import time
import pytest

from ailf.memory.in_memory import InMemoryShortTermMemory
from ailf.schemas.memory import MemoryItem


class TestInMemoryShortTermMemory:
    """Tests for InMemoryShortTermMemory class."""
    
    @pytest.fixture
    def memory_store(self):
        """Create a memory store for testing."""
        return InMemoryShortTermMemory(max_size=3)
    
    @pytest.mark.asyncio
    async def test_add_and_get_item(self, memory_store):
        """Test adding and retrieving an item from memory."""
        # Create a test item
        test_item = MemoryItem(
            item_id="test1",
            data="test data",
            metadata={"source": "test"}
        )
        
        # Add the item to memory
        await memory_store.add_item(test_item)
        
        # Retrieve the item
        retrieved_item = await memory_store.get_item("test1")
        
        # Check that retrieved item matches the original
        assert retrieved_item is not None
        assert retrieved_item.item_id == test_item.item_id
        assert retrieved_item.data == test_item.data
        assert retrieved_item.metadata == test_item.metadata
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_item(self, memory_store):
        """Test retrieving a non-existent item returns None."""
        retrieved_item = await memory_store.get_item("does_not_exist")
        assert retrieved_item is None
    
    @pytest.mark.asyncio
    async def test_get_recent_items(self, memory_store):
        """Test retrieving recent items in correct order."""
        # Add several test items with small delays to ensure timestamp differences
        item1 = MemoryItem(item_id="id1", data="data1")
        await memory_store.add_item(item1)
        await asyncio.sleep(0.01)  # Small delay for timestamp difference
        
        item2 = MemoryItem(item_id="id2", data="data2")
        await memory_store.add_item(item2)
        await asyncio.sleep(0.01)  # Small delay for timestamp difference
        
        item3 = MemoryItem(item_id="id3", data="data3")
        await memory_store.add_item(item3)
        
        # Get recent items - should return in reverse chronological order
        recent_items = await memory_store.get_recent_items(2)
        
        # Validate that we got 2 most recent items in correct order
        assert len(recent_items) == 2
        assert recent_items[0].item_id == "id3"
        assert recent_items[1].item_id == "id2"
    
    @pytest.mark.asyncio
    async def test_max_size_constraint(self, memory_store):
        """Test that memory store doesn't exceed max size and evicts oldest items."""
        # Add items up to the max capacity (3)
        await memory_store.add_item(MemoryItem(item_id="id1", data="data1"))
        await asyncio.sleep(0.01)
        await memory_store.add_item(MemoryItem(item_id="id2", data="data2"))
        await asyncio.sleep(0.01)
        await memory_store.add_item(MemoryItem(item_id="id3", data="data3"))
        
        # At this point, all three items should be in memory
        assert await memory_store.get_item("id1") is not None
        assert await memory_store.get_item("id2") is not None
        assert await memory_store.get_item("id3") is not None
        
        # Add a fourth item - this should evict the oldest item (id1)
        await asyncio.sleep(0.01)
        await memory_store.add_item(MemoryItem(item_id="id4", data="data4"))
        
        # The oldest item should have been removed
        assert await memory_store.get_item("id1") is None
        assert await memory_store.get_item("id2") is not None
        assert await memory_store.get_item("id3") is not None
        assert await memory_store.get_item("id4") is not None
    
    @pytest.mark.asyncio
    async def test_get_recent_with_zero_count(self, memory_store):
        """Test retrieving zero recent items."""
        await memory_store.add_item(MemoryItem(item_id="id1", data="data1"))
        
        recent_items = await memory_store.get_recent_items(0)
        assert len(recent_items) == 0
    
    @pytest.mark.asyncio
    async def test_get_recent_with_negative_count(self, memory_store):
        """Test retrieving with negative count."""
        await memory_store.add_item(MemoryItem(item_id="id1", data="data1"))
        
        recent_items = await memory_store.get_recent_items(-5)
        assert len(recent_items) == 0
    
    @pytest.mark.asyncio
    async def test_clear(self, memory_store):
        """Test clearing the memory store."""
        # Add items
        await memory_store.add_item(MemoryItem(item_id="id1", data="data1"))
        await memory_store.add_item(MemoryItem(item_id="id2", data="data2"))
        
        # Verify items are in memory
        assert await memory_store.get_item("id1") is not None
        assert await memory_store.get_item("id2") is not None
        
        # Clear the memory store
        await memory_store.clear()
        
        # Verify items are gone
        assert await memory_store.get_item("id1") is None
        assert await memory_store.get_item("id2") is None
        
        # Verify get_recent_items returns empty list
        recent_items = await memory_store.get_recent_items(10)
        assert len(recent_items) == 0
