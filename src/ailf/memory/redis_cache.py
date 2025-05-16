"""Redis-backed distributed cache implementation for AILF agents."""

import json
from typing import Any, Dict, List, Optional, Union

# Updated import pattern to address deprecation warning
from redis import asyncio as redis

from ailf.schemas.memory import MemoryItem

class RedisDistributedCache:
    """
    Manages a distributed cache using Redis, storing MemoryItem objects.
    """

    def __init__(self, redis_url: str, default_ttl: int = 3600, key_prefix: str = "ailf:cache:"):
        """
        Initializes the Redis distributed cache.

        :param redis_url: URL for the Redis server (e.g., "redis://localhost:6379/0").
        :type redis_url: str
        :param default_ttl: Default time-to-live for cache items in seconds.
        :type default_ttl: int
        :param key_prefix: Prefix for all keys stored in Redis to avoid collisions.
        :type key_prefix: str
        """
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix

    def _get_redis_key(self, item_id: str) -> str:
        """Constructs the full Redis key with the prefix."""
        return f"{self.key_prefix}{item_id}"

    async def add_item(self, memory_item: MemoryItem, ttl: Optional[int] = None) -> None:
        """
        Adds a MemoryItem to the Redis cache.

        :param memory_item: The memory item to store
        :type memory_item: MemoryItem
        :param ttl: Time-to-live for this item in seconds. Uses default_ttl if None.
                    A TTL of 0 or less means the item will not expire (persistent).
        :type ttl: Optional[int]
        """
        actual_ttl = ttl if ttl is not None else self.default_ttl
        redis_key = self._get_redis_key(memory_item.id)
        
        # Serialize to JSON
        try:
            serialized_data = memory_item.model_dump_json()
        except AttributeError:
            # Fallback for older Pydantic versions
            serialized_data = memory_item.json()
            
        # Store in Redis
        if actual_ttl > 0:
            # With TTL
            await self.redis_client.setex(redis_key, actual_ttl, serialized_data)
        else:
            # Persistent (no TTL)
            await self.redis_client.set(redis_key, serialized_data)

    async def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieves an item from the Redis cache.

        :param item_id: The ID of the item to retrieve.
        :type item_id: str
        :return: The MemoryItem if found, else None.
        :rtype: Optional[MemoryItem]
        """
        redis_key = self._get_redis_key(item_id)
        serialized_item = await self.redis_client.get(redis_key)
        
        if not serialized_item:
            return None
            
        # Convert from bytes if needed
        if isinstance(serialized_item, bytes):
            serialized_item = serialized_item.decode('utf-8')
            
        try:
            # Parse JSON into MemoryItem
            item_dict = json.loads(serialized_item)
            return MemoryItem.model_validate(item_dict) if hasattr(MemoryItem, 'model_validate') else MemoryItem.parse_obj(item_dict)
        except Exception as e:
            # Log the error but don't crash
            print(f"Error parsing MemoryItem from cache: {e}")
            return None

    async def remove_item(self, item_id: str) -> bool:
        """
        Removes an item from the Redis cache.

        :param item_id: The ID of the item to remove.
        :type item_id: str
        :return: True if the item was found and removed, False otherwise.
        :rtype: bool
        """
        redis_key = self._get_redis_key(item_id)
        deleted_count = await self.redis_client.delete(redis_key)
        return deleted_count > 0

    async def list_item_ids(self, pattern: str = "*") -> List[str]:
        """
        Lists item IDs in the cache matching a pattern (relative to the key_prefix).
        Warning: `KEYS` can be slow in production Redis environments. Use with caution.

        :param pattern: The pattern to match item IDs (e.g., "user:*").
        :type pattern: str
        :return: A list of item IDs (without the global prefix).
        :rtype: List[str]
        """
        full_pattern = f"{self.key_prefix}{pattern}"
        keys = await self.redis_client.keys(full_pattern)
        
        # Handle both string and bytes keys
        result = []
        for key in keys:
            if isinstance(key, bytes):
                key_str = key.decode('utf-8')
            else:
                key_str = key
            result.append(key_str.replace(self.key_prefix, "", 1))
        
        return result

    async def clear_all(self, pattern: str = "*") -> int:
        """
        Clears items from the cache matching a pattern (relative to the key_prefix).
        If pattern is "*", it clears all keys managed by this cache instance (with its prefix).
        Warning: `KEYS` can be slow. For full flush, consider `FLUSHDB` or `FLUSHALL` if appropriate
        and if this client is the only user or specific to a DB.
        This method only deletes keys matching the prefix + pattern.

        :param pattern: The pattern to match item IDs for clearing.
        :type pattern: str
        :return: The number of keys deleted.
        :rtype: int
        """
        full_pattern = f"{self.key_prefix}{pattern}"
        keys = await self.redis_client.keys(full_pattern)
        
        if not keys:
            return 0
        
        return await self.redis_client.delete(*keys)

    async def ping(self) -> bool:
        """Checks the connection to Redis."""
        return await self.redis_client.ping()

    async def close(self) -> None:
        """Closes the Redis connection."""
        await self.redis_client.close()
        await self.redis_client.connection_pool.disconnect()
