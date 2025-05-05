"""Mock Redis Client for Testing.

This module provides mock implementations of Redis clients for testing environments
without a Redis server. It implements the same interfaces as the real clients but
uses in-memory storage instead of connecting to a Redis server.

Example:
    >>> from utils.messaging.mock_redis import MockRedisClient
    >>> client = MockRedisClient()
    >>> client.set("key", "value")
    >>> value = client.get("key")
    >>> print(value)
    'value'
"""

import asyncio
import json
import time
from collections import defaultdict
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from utils.messaging.redis import RedisConfig


class MockRedisClient:
    """Mock implementation of RedisClient for testing without a Redis server."""

    _storage: Dict[str, Dict[str, Any]] = {}
    _pubsub_channels: Dict[str, List[Callable]] = {}
    _lock = Lock()

    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize the mock Redis client.

        Args:
            config: Redis configuration (ignored in mock implementation)
        """
        self._db_id = 0 if config is None else config.db
        # Initialize storage for this DB if needed
        with self._lock:
            if self._db_id not in self._storage:
                self._storage[self._db_id] = {}
        self.client = self  # For compatibility with RedisClient

        # Log the initialization to help with debugging
        print(f"MockRedisClient initialized with db={self._db_id}")

        # Track whether Redis would be available in a real environment
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("localhost", 6379))
            s.close()
            self._real_redis_available = True
            print("Note: Real Redis is actually available, but using mock implementation")
        except (socket.error, ConnectionRefusedError):
            self._real_redis_available = False
            print("Note: Real Redis is not available, mock implementation is appropriate")

    @property
    def _db(self) -> Dict[str, Any]:
        """Get the current database."""
        return self._storage[self._db_id]

    def get(self, key: str) -> Optional[str]:
        """Get a value from the mock Redis store."""
        with self._lock:
            return self._db.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set a value in the mock Redis store."""
        with self._lock:
            self._db[key] = value
            return True

    def delete(self, key: str) -> int:
        """Delete a key from the mock Redis store."""
        with self._lock:
            if key in self._db:
                del self._db[key]
                return 1
            return 0

    def exists(self, key: str) -> bool:
        """Check if a key exists in the mock Redis store."""
        with self._lock:
            return key in self._db

    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern from the mock Redis store."""
        import fnmatch
        with self._lock:
            return [k for k in self._db.keys() if fnmatch.fnmatch(k, pattern)]

    def flushdb(self) -> bool:
        """Clear the current database."""
        with self._lock:
            self._db.clear()
            return True

    def close(self) -> None:
        """Close the connection (no-op in mock)."""
        pass

    # JSON operations
    def json_set(self, key: str, path: str, obj: Any) -> bool:
        """Set a JSON value in the mock Redis store."""
        with self._lock:
            if path != ".":
                raise NotImplementedError("Only root path is supported in mock")
            self._db[key] = json.dumps(obj)
            return True

    def json_get(self, key: str, path: str = ".") -> Optional[Any]:
        """Get a JSON value from the mock Redis store."""
        with self._lock:
            if path != ".":
                raise NotImplementedError("Only root path is supported in mock")
            if key not in self._db:
                return None
            return json.loads(self._db[key])


class MockAsyncRedisClient:
    """Mock implementation of AsyncRedisClient for testing without a Redis server."""

    _storage: Dict[str, Dict[str, Any]] = {}
    _lock = Lock()

    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize the mock async Redis client.

        Args:
            config: Redis configuration (ignored in mock implementation)
        """
        self._db_id = 0 if config is None else config.db
        # Initialize storage for this DB if needed
        with self._lock:
            if self._db_id not in self._storage:
                self._storage[self._db_id] = {}
        self.client = self  # For compatibility with AsyncRedisClient

    @property
    def _db(self) -> Dict[str, Any]:
        """Get the current database."""
        return self._storage[self._db_id]

    async def get(self, key: str) -> Optional[str]:
        """Get a value from the mock Redis store."""
        with self._lock:
            return self._db.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set a value in the mock Redis store."""
        with self._lock:
            self._db[key] = value
            return True

    async def delete(self, key: str) -> int:
        """Delete a key from the mock Redis store."""
        with self._lock:
            if key in self._db:
                del self._db[key]
                return 1
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the mock Redis store."""
        with self._lock:
            return key in self._db

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching a pattern from the mock Redis store."""
        import fnmatch
        with self._lock:
            return [k for k in self._db.keys() if fnmatch.fnmatch(k, pattern)]

    async def flushdb(self) -> bool:
        """Clear the current database."""
        with self._lock:
            self._db.clear()
            return True

    async def close(self) -> None:
        """Close the connection (no-op in mock)."""
        pass

    # JSON operations
    async def json_set(self, key: str, path: str, obj: Any) -> bool:
        """Set a JSON value in the mock Redis store."""
        with self._lock:
            if path != ".":
                raise NotImplementedError("Only root path is supported in mock")
            self._db[key] = json.dumps(obj)
            return True

    async def json_get(self, key: str, path: str = ".") -> Optional[Any]:
        """Get a JSON value from the mock Redis store."""
        with self._lock:
            if path != ".":
                raise NotImplementedError("Only root path is supported in mock")
            if key not in self._db:
                return None
            return json.loads(self._db[key])

    def is_connected(self) -> bool:
        """Check if the client is connected (always True for mock)."""
        return True
