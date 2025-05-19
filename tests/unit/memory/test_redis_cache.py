"""Tests for redis_cache.py module.

This module contains tests for the Redis distributed cache implementation.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ailf.memory.redis_cache import RedisDistributedCache
from ailf.schemas.memory import MemoryItem, MemoryType


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    # Setup common methods
    mock.ping.return_value = True
    return mock


@pytest.fixture
def redis_cache(mock_redis):
    """Create a RedisDistributedCache with a mock Redis client."""
    with patch('redis.asyncio.from_url', return_value=mock_redis):
        cache = RedisDistributedCache(redis_url="redis://localhost:6379/0")
        # Inject the mock directly to ensure it's used
        cache.redis_client = mock_redis
        return cache


class TestRedisDistributedCache:
    """Tests for the RedisDistributedCache class."""
    
    @pytest.mark.asyncio
    async def test_init(self):
        """Test initialization of RedisDistributedCache."""
        with patch('redis.asyncio.from_url') as mock_from_url:
            cache = RedisDistributedCache(
                redis_url="redis://localhost:6379/0", 
                default_ttl=1800,
                key_prefix="test:"
            )
            
            mock_from_url.assert_called_once_with("redis://localhost:6379/0")
            assert cache.default_ttl == 1800
            assert cache.key_prefix == "test:"
    
    @pytest.mark.asyncio
    async def test_add_item_with_ttl(self, redis_cache, mock_redis):
        """Test adding an item with TTL."""
        # Create test item
        test_item = MemoryItem(
            id="test1", 
            type=MemoryType.OBSERVATION,
            content="test data"
        )
        
        # Add item to cache
        await redis_cache.add_item(test_item, ttl=60)
        
        # Mock conversion to JSON
        json_data = test_item.model_dump_json()
        
        # Check that the set command was called correctly
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[0] == "ailf:cache:test1"  # Key
        assert args[1] == 60  # TTL
        # Check that the value is valid JSON that can be parsed back to an item
        assert json.loads(args[2])["id"] == "test1"
        assert json.loads(args[2])["type"] == "observation"
        assert json.loads(args[2])["content"] == "test data"
    
    @pytest.mark.asyncio
    async def test_add_item_no_ttl(self, redis_cache, mock_redis):
        """Test adding an item with default TTL."""
        # Create test item
        test_item = MemoryItem(
            id="test2", 
            type=MemoryType.ACTION,
            content="action data"
        )
        
        # Add item to cache with default TTL
        await redis_cache.add_item(test_item)
        
        # Check that setex was called with default TTL
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[0] == "ailf:cache:test2"
        assert args[1] == redis_cache.default_ttl
    
    @pytest.mark.asyncio
    async def test_add_persistent_item(self, redis_cache, mock_redis):
        """Test adding a persistent item (no TTL)."""
        # Create test item
        test_item = MemoryItem(
            id="test3", 
            type=MemoryType.ACTION,
            content="persistent data"
        )
        
        # Add as persistent item (TTL = -1)
        await redis_cache.add_item(test_item, ttl=-1)
        
        # Check that set was called instead of setex for persistent items
        mock_redis.set.assert_called_once()
        args = mock_redis.set.call_args[0]
        assert args[0] == "ailf:cache:test3"
        
    @pytest.mark.asyncio
    async def test_get_item_existing(self, redis_cache, mock_redis):
        """Test retrieving an existing item."""
        # Create test item
        test_item = MemoryItem(
            id="test4",
            type=MemoryType.OBSERVATION,
            content="retrievable data"
        )
        
        # Setup mock to return the JSON data
        mock_redis.get.return_value = test_item.model_dump_json()
        
        # Get the item
        retrieved_item = await redis_cache.get_item("test4")
        
        # Check that get was called with the right key
        mock_redis.get.assert_called_once_with("ailf:cache:test4")
        
        # Check retrieved item
        assert retrieved_item is not None
        assert retrieved_item.id == "test4"
        assert retrieved_item.type == MemoryType.OBSERVATION
        assert retrieved_item.content == "retrievable data"
    
    @pytest.mark.asyncio
    async def test_get_item_nonexistent(self, redis_cache, mock_redis):
        """Test retrieving a non-existent item."""
        # Setup mock to return None for non-existent key
        mock_redis.get.return_value = None
        
        # Try to get a non-existent item
        retrieved_item = await redis_cache.get_item("nonexistent")
        
        # Check that get was called
        mock_redis.get.assert_called_once_with("ailf:cache:nonexistent")
        
        # Check that None is returned for non-existent items
        assert retrieved_item is None
    
    @pytest.mark.asyncio
    async def test_remove_item(self, redis_cache, mock_redis):
        """Test removing an item."""
        # Setup mock to return 1 (successful deletion)
        mock_redis.delete.return_value = 1
        
        # Remove an item
        success = await redis_cache.remove_item("test5")
        
        # Check that delete was called with the right key
        mock_redis.delete.assert_called_once_with("ailf:cache:test5")
        
        # Check that True is returned for successful deletion
        assert success is True
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_item(self, redis_cache, mock_redis):
        """Test removing a non-existent item."""
        # Setup mock to return 0 (no keys deleted)
        mock_redis.delete.return_value = 0
        
        # Try to remove a non-existent item
        success = await redis_cache.remove_item("nonexistent")
        
        # Check that delete was called
        mock_redis.delete.assert_called_once_with("ailf:cache:nonexistent")
        
        # Check that False is returned for unsuccessful deletion
        assert success is False
    
    @pytest.mark.asyncio
    async def test_list_item_ids(self, redis_cache, mock_redis):
        """Test listing all item IDs."""
        # Setup mock to return keys
        mock_redis.keys.return_value = ["ailf:cache:item1", "ailf:cache:item2", "ailf:cache:item3"]
        
        # Get all item IDs
        item_ids = await redis_cache.list_item_ids()
        
        # Check that keys was called with the right pattern
        mock_redis.keys.assert_called_once_with("ailf:cache:*")
        
        # Check that the IDs are extracted correctly
        assert set(item_ids) == {"item1", "item2", "item3"}
    
    @pytest.mark.asyncio
    async def test_clear_all(self, redis_cache, mock_redis):
        """Test clearing all items."""
        # Setup keys to delete
        mock_redis.keys.return_value = ["ailf:cache:item1", "ailf:cache:item2"]
        # Setup delete to return number of keys deleted
        mock_redis.delete.return_value = 2
        
        # Clear all items
        deleted_count = await redis_cache.clear_all()
        
        # Check that keys was called to find all keys
        mock_redis.keys.assert_called_once_with("ailf:cache:*")
        
        # Check that delete was called with all keys
        mock_redis.delete.assert_called_once_with("ailf:cache:item1", "ailf:cache:item2")
        
        # Check that the correct count is returned
        assert deleted_count == 2
    
    @pytest.mark.asyncio
    async def test_ping(self, redis_cache, mock_redis):
        """Test pinging the Redis server."""
        # Call ping
        is_connected = await redis_cache.ping()
        
        # Check that ping was called on the Redis client
        mock_redis.ping.assert_called_once()
        
        # Check that True is returned for successful ping
        assert is_connected is True
    
    @pytest.mark.asyncio
    async def test_close(self, redis_cache, mock_redis):
        """Test closing the Redis connection."""
        # Call close
        await redis_cache.close()
        
        # Check that close was called on the Redis client
        mock_redis.close.assert_called_once()
