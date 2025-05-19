"""Tests for in_memory storage.

This module contains tests for the InMemoryShortTermMemory class.
"""
import asyncio
import time
import pytest

from ailf.memory.in_memory import InMemoryShortTermMemory
from ailf.schemas.memory import MemoryItem, MemoryType


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
            id="test1",
            type=MemoryType.OBSERVATION,
            content="test data",
            metadata={"source": "test"}
        )
        
        # Add the item to memory
        await memory_store.add_item(test_item)
        
        # Retrieve the item
        retrieved_item = await memory_store.get_item("test1")
        
        # Check that retrieved item matches the original
        assert retrieved_item is not None
        assert retrieved_item.id == test_item.id
        assert retrieved_item.content == test_item.content
        assert retrieved_item.metadata == test_item.metadata
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_item(self, memory_store):
        """Test retrieving a non-existent item returns None."""
        retrieved_item = await memory_store.get_item("does_not_exist")
        assert retrieved_item is None
    
    @pytest.mark.asyncio
    async def test_get_recent_items(self, memory_store):
        """Test retrieving recent items in correct order."""
        # Create test items
        items = [
            MemoryItem(id=f"test{i}", type=MemoryType.OBSERVATION, content=f"data{i}")
            for i in range(1, 4)
        ]
        
        # Add items to memory with delays to ensure different timestamps
        for item in items:
            await memory_store.add_item(item)
            await asyncio.sleep(0.01)  # Small delay to ensure different timestamps
        
        # Get recent items
        recent_items = await memory_store.get_recent_items(2)
        
        # Check that we got the expected number of items
        assert len(recent_items) == 2
        
        # Check that items are returned in reverse order (most recent first)
        assert recent_items[0].id == "test3"
        assert recent_items[1].id == "test2"
    
    @pytest.mark.asyncio
    async def test_max_size_constraint(self, memory_store):
        """Test that the memory respects the max_size constraint."""
        # Add more items than the max_size
        for i in range(5):  # Max size is 3
            await memory_store.add_item(MemoryItem(
                id=f"test{i}", 
                type=MemoryType.OBSERVATION,
                content=f"data{i}"
            ))
        
        # Check that only the most recent items are retained
        all_items = await memory_store.get_recent_items(5)
        assert len(all_items) == 3  # Should only have max_size items
        
        # Check that the oldest items were evicted
        item_ids = [item.id for item in all_items]
        assert "test0" not in item_ids
        assert "test1" not in item_ids
        assert "test2" in item_ids
        assert "test3" in item_ids
        assert "test4" in item_ids
    
    @pytest.mark.asyncio
    async def test_get_recent_with_zero_count(self, memory_store):
        """Test retrieving zero recent items returns an empty list."""
        # Add some items
        await memory_store.add_item(MemoryItem(id="test1", type=MemoryType.OBSERVATION, content="data1"))
        
        # Get zero recent items
        recent_items = await memory_store.get_recent_items(0)
        assert recent_items == []
    
    @pytest.mark.asyncio
    async def test_get_recent_with_negative_count(self, memory_store):
        """Test retrieving a negative count of recent items returns an empty list."""
        # Add some items
        await memory_store.add_item(MemoryItem(id="test1", type=MemoryType.OBSERVATION, content="data1"))
        
        # Get negative count of recent items
        recent_items = await memory_store.get_recent_items(-1)
        assert recent_items == []
    
    @pytest.mark.asyncio
    async def test_clear(self, memory_store):
        """Test clearing all items from memory."""
        # Add some items
        await memory_store.add_item(MemoryItem(id="test1", type=MemoryType.OBSERVATION, content="data1"))
        await memory_store.add_item(MemoryItem(id="test2", type=MemoryType.OBSERVATION, content="data2"))
        
        # Clear memory
        await memory_store.clear()
        
        # Check that all items are gone
        assert await memory_store.get_item("test1") is None
        assert await memory_store.get_item("test2") is None
        assert await memory_store.get_recent_items(10) == []
