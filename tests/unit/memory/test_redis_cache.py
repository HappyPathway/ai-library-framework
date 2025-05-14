"""Tests for redis_cache.py module.

This module contains tests for the Redis distributed cache implementation.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from ailf.memory.redis_cache import RedisDistributedCache
from ailf.schemas.memory import MemoryItem


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
        item_id = "test1"
        data = {"name": "Test Item"}
        metadata = {"source": "test"}
        ttl = 60
        
        await redis_cache.add_item(item_id, data, ttl, metadata)
        
        # Get the expected Redis key
        expected_key = f"{redis_cache.key_prefix}{item_id}"
        
        # Verify setex was called with the right parameters
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        
        assert call_args[0] == expected_key
        assert call_args[1] == ttl
        
        # Deserialize the stored item to verify contents
        serialized_item = call_args[2]
        stored_item = json.loads(serialized_item)
        
        assert stored_item["item_id"] == item_id
        assert stored_item["data"] == data
        assert stored_item["metadata"] == metadata
    
    @pytest.mark.asyncio
    async def test_add_item_no_ttl(self, redis_cache, mock_redis):
        """Test adding an item with default TTL."""
        item_id = "test1"
        data = {"name": "Test Item"}
        
        await redis_cache.add_item(item_id, data)
        
        # Verify setex was called with default TTL
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == redis_cache.default_ttl
    
    @pytest.mark.asyncio
    async def test_add_persistent_item(self, redis_cache, mock_redis):
        """Test adding a persistent item (no expiration)."""
        item_id = "test_persistent"
        data = {"name": "Persistent Item"}
        
        await redis_cache.add_item(item_id, data, ttl=0)  # 0 means persist
        
        # Verify set was called instead of setex
        mock_redis.set.assert_called_once()
        mock_redis.setex.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_item_existing(self, redis_cache, mock_redis):
        """Test retrieving an existing item."""
        item_id = "test1"
        test_item = MemoryItem(
            item_id=item_id,
            data={"name": "Test Item"},
            metadata={"source": "test"}
        )
        
        # Mock Redis get to return serialized test item
        serialized_item = json.dumps(test_item.model_dump())
        mock_redis.get.return_value = serialized_item
        
        # Retrieve the item
        retrieved_item = await redis_cache.get_item(item_id)
        
        # Verify Redis get was called with the right key
        expected_key = f"{redis_cache.key_prefix}{item_id}"
        mock_redis.get.assert_called_once_with(expected_key)
        
        # Verify retrieved item matches expected values
        assert retrieved_item is not None
        assert retrieved_item.item_id == item_id
        assert retrieved_item.data == test_item.data
        assert retrieved_item.metadata == test_item.metadata
    
    @pytest.mark.asyncio
    async def test_get_item_nonexistent(self, redis_cache, mock_redis):
        """Test retrieving a non-existent item."""
        mock_redis.get.return_value = None
        
        retrieved_item = await redis_cache.get_item("nonexistent_id")
        assert retrieved_item is None
    
    @pytest.mark.asyncio
    async def test_remove_item(self, redis_cache, mock_redis):
        """Test removing an item."""
        item_id = "test1"
        mock_redis.delete.return_value = 1  # 1 key deleted
        
        result = await redis_cache.remove_item(item_id)
        
        # Verify Redis delete was called with the right key
        expected_key = f"{redis_cache.key_prefix}{item_id}"
        mock_redis.delete.assert_called_once_with(expected_key)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_item(self, redis_cache, mock_redis):
        """Test removing a non-existent item."""
        item_id = "nonexistent_id"
        mock_redis.delete.return_value = 0  # 0 keys deleted
        
        result = await redis_cache.remove_item(item_id)
        assert result is True  # Should still return True as the operation was successful
    
    @pytest.mark.asyncio
    async def test_list_item_ids(self, redis_cache, mock_redis):
        """Test listing item IDs."""
        # Mock the keys that Redis would return
        prefix = redis_cache.key_prefix
        mock_keys = [
            f"{prefix}item1".encode('utf-8'),
            f"{prefix}item2".encode('utf-8'),
            f"{prefix}item3".encode('utf-8')
        ]
        mock_redis.keys.return_value = mock_keys
        
        # Get item IDs
        item_ids = await redis_cache.list_item_ids()
        
        # Verify Redis keys was called with the right pattern
        expected_pattern = f"{prefix}*"
        mock_redis.keys.assert_called_once_with(expected_pattern)
        
        # Verify the returned list has the prefix stripped
        assert item_ids == ["item1", "item2", "item3"]
    
    @pytest.mark.asyncio
    async def test_clear_all(self, redis_cache, mock_redis):
        """Test clearing all items."""
        # Setup mock to return some keys
        mock_redis.keys.return_value = [
            b"ailf:cache:item1",
            b"ailf:cache:item2"
        ]
        mock_redis.delete.return_value = 2  # 2 keys deleted
        
        # Call clear_all
        deleted_count = await redis_cache.clear_all()
        
        # Verify keys were fetched with the right pattern
        mock_redis.keys.assert_called_once_with("ailf:cache:*")
        
        # Verify delete was called with the right keys
        mock_redis.delete.assert_called_once_with("ailf:cache:item1", "ailf:cache:item2")
        assert deleted_count == 2
    
    @pytest.mark.asyncio
    async def test_ping(self, redis_cache, mock_redis):
        """Test pinging Redis."""
        result = await redis_cache.ping()
        mock_redis.ping.assert_called_once()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_close(self, redis_cache, mock_redis):
        """Test closing Redis connection."""
        # Create a mock connection pool
        mock_pool = AsyncMock()
        mock_redis.connection_pool = mock_pool
        
        await redis_cache.close()
        
        mock_redis.close.assert_called_once()
        mock_pool.disconnect.assert_called_once()
