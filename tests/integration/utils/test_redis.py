"""Integration tests for Redis messaging utilities.

This module contains integration tests for the Redis messaging utilities.
These tests require a running Redis server.
"""
import json
import threading
import time
from typing import Any, Dict, List

import pytest

from utils.messaging.redis import (AsyncRedisClient, RedisClient, RedisConfig,
                                   RedisLock, RedisPubSub, RedisRateLimiter,
                                   RedisStream)


@pytest.fixture
def redis_config():
    """Redis configuration for tests."""
    return RedisConfig(
        host="localhost",
        port=6379,
        db=1,  # Use a different DB than default to avoid conflicts
        decode_responses=True
    )


@pytest.fixture
def redis_client(redis_config):
    """Redis client fixture."""
    client = RedisClient(redis_config)
    yield client
    client.close()


@pytest.fixture
def clear_redis(redis_client):
    """Clear Redis database before and after tests."""
    redis_client.client.flushdb()
    yield
    redis_client.client.flushdb()


@pytest.fixture
def test_stream_name():
    """Test stream name for stream tests."""
    return "test_stream"


@pytest.fixture
def test_pubsub_channel():
    """Test channel name for pubsub tests."""
    return "test_channel"


@pytest.mark.integration
class TestRedisClient:
    """Integration tests for RedisClient."""

    def test_connection(self, redis_client):
        """Test Redis connection."""
        assert redis_client.health_check() is True

    def test_basic_operations(self, redis_client, clear_redis):
        """Test basic Redis operations."""
        # Set and get
        assert redis_client.set("test_key", "test_value") is True
        assert redis_client.get("test_key") == "test_value"

        # Exists
        assert redis_client.exists("test_key") is True
        assert redis_client.exists("nonexistent_key") is False

        # Delete
        assert redis_client.delete("test_key") is True
        assert redis_client.get("test_key") is None

    def test_json_operations(self, redis_client, clear_redis):
        """Test JSON Redis operations."""
        test_data = {"name": "test", "value": 42, "nested": {"key": "value"}}

        # Set and get JSON
        assert redis_client.set_json("test_json", test_data) is True
        result = redis_client.get_json("test_json")

        assert result == test_data
        assert result["nested"]["key"] == "value"


@pytest.mark.asyncio
@pytest.mark.integration
class TestAsyncRedisClient:
    """Integration tests for AsyncRedisClient."""

    async def test_connection(self, redis_config):
        """Test async Redis connection."""
        client = AsyncRedisClient(redis_config)
        assert await client.health_check() is True
        await client.close()

    async def test_basic_operations(self, redis_config):
        """Test basic async Redis operations."""
        client = AsyncRedisClient(redis_config)

        # Clear any existing data
        redis_client = redis_config.client
        redis_client.flushdb()

        # Set and get
        assert await client.set("test_key_async", "test_value") is True
        assert await client.get("test_key_async") == "test_value"

        # Exists
        assert await client.exists("test_key_async") is True
        assert await client.exists("nonexistent_key") is False

        # Delete
        assert await client.delete("test_key_async") is True
        assert await client.get("test_key_async") is None

        await client.close()


@pytest.mark.integration
class TestRedisPubSub:
    """Integration tests for RedisPubSub."""

    def test_publish_subscribe(self, redis_client, test_pubsub_channel, clear_redis):
        """Test publish and subscribe."""
        received_messages = []

        def message_handler(message):
            received_messages.append(message)

        # Create a PubSub instance
        pubsub = RedisPubSub(redis_client)
        pubsub.subscribe(test_pubsub_channel, message_handler)

        # Start listening in a background thread
        thread = pubsub.run_in_thread()

        # Give it a moment to subscribe
        time.sleep(0.5)

        # Publish some messages
        test_messages = [
            {"id": 1, "text": "Hello"},
            {"id": 2, "text": "World"}
        ]

        for message in test_messages:
            pubsub.publish(test_pubsub_channel, message)
            time.sleep(0.1)  # Give it time to process

        # Wait a bit for messages to be processed
        time.sleep(0.5)

        # Stop the pubsub thread
        pubsub.stop()
        thread.join(timeout=1)

        # Verify received messages
        assert len(received_messages) == len(test_messages)
        assert received_messages[0]["id"] == 1
        assert received_messages[1]["text"] == "World"


@pytest.mark.integration
class TestRedisStream:
    """Integration tests for RedisStream."""

    def test_add_and_read(self, redis_client, test_stream_name, clear_redis):
        """Test adding and reading from a stream."""
        stream = RedisStream(test_stream_name, redis_client)

        # Add some messages
        message_id1 = stream.add({"key1": "value1", "number": "42"})
        message_id2 = stream.add({"key2": "value2", "boolean": "true"})

        # Read messages
        messages = stream.read(count=10)

        # Verify messages
        assert len(messages) == 2
        assert messages[0]["id"] == message_id1
        assert messages[0]["data"]["key1"] == "value1"
        assert messages[1]["id"] == message_id2
        assert messages[1]["data"]["key2"] == "value2"

    def test_consumer_group(self, redis_client, test_stream_name, clear_redis):
        """Test consumer groups with streams."""
        stream = RedisStream(test_stream_name, redis_client)

        # Create a consumer group
        assert stream.create_consumer_group(
            "test_group", "test_consumer", "0") is True

        # Add some messages
        stream.add({"task": "task1"})
        stream.add({"task": "task2"})

        # Read from the group
        messages = stream.read_group(count=10)

        # Verify messages
        assert len(messages) == 2
        assert messages[0]["data"]["task"] == "task1"
        assert messages[1]["data"]["task"] == "task2"

        # Acknowledge a message
        assert stream.acknowledge(messages[0]["id"]) is True


@pytest.mark.integration
class TestRedisLock:
    """Integration tests for RedisLock."""

    def test_acquire_release(self, redis_client, clear_redis):
        """Test acquiring and releasing a lock."""
        lock = RedisLock("test_lock", expire=5, redis_client=redis_client)

        # Acquire the lock
        assert lock.acquire() is True

        # Try to acquire the same lock (should fail)
        lock2 = RedisLock("test_lock", expire=5, redis_client=redis_client)
        assert lock2.acquire(retry=1) is False

        # Release the lock
        assert lock.release() is True

        # Now lock2 should be able to acquire
        assert lock2.acquire() is True

        # Clean up
        lock2.release()

    def test_context_manager(self, redis_client, clear_redis):
        """Test lock as a context manager."""
        results = []

        def task1():
            with RedisLock("shared_lock", redis_client=redis_client).acquire_context() as acquired:
                if acquired:
                    results.append("task1")
                    time.sleep(0.2)

        def task2():
            # Wait a bit for task1 to acquire the lock
            time.sleep(0.1)
            with RedisLock("shared_lock", redis_client=redis_client).acquire_context() as acquired:
                if acquired:
                    results.append("task2")

        # Run the tasks in separate threads
        t1 = threading.Thread(target=task1)
        t2 = threading.Thread(target=task2)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # task1 should run first, followed by task2
        assert results == ["task1", "task2"]


@pytest.mark.integration
class TestRedisRateLimiter:
    """Integration tests for RedisRateLimiter."""

    def test_rate_limiting(self, redis_client, clear_redis):
        """Test rate limiting functionality."""
        # Create a rate limiter with a limit of 3 requests per second
        limiter = RedisRateLimiter(
            "test_limiter", rate=3, period=1, redis_client=redis_client)

        # First 3 requests should be allowed
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True
        assert limiter.is_allowed("user1") is True

        # 4th request should be denied
        assert limiter.is_allowed("user1") is False

        # Different user should be allowed
        assert limiter.is_allowed("user2") is True

        # Wait for the rate limit to reset
        time.sleep(1.1)

        # Should be allowed again
        assert limiter.is_allowed("user1") is True
