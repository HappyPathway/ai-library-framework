"""Redis Client Utilities.

This module provides Redis client implementations for both synchronous and
asynchronous communication patterns. It supports common Redis operations,
pub/sub messaging, and stream processing for distributed agent communication.

Key Components:
    RedisConfig: Configuration model for Redis connections
    RedisClient: Synchronous Redis client implementation
    AsyncRedisClient: Asynchronous Redis client implementation
    RedisPubSub: Higher-level pub/sub implementation

Example:
    Synchronous usage:
        >>> from ailf.messaging.redis import RedisClient
        >>> client = RedisClient()
        >>> client.set("key", "value")
        >>> value = client.get("key")
        >>> print(value)
        'value'
    
    Asynchronous usage:
        >>> import asyncio
        >>> from ailf.messaging.redis import AsyncRedisClient
        >>> 
        >>> async def main():
        ...     client = AsyncRedisClient()
        ...     await client.set("key", "value")
        ...     value = await client.get("key")
        ...     print(value)
        ... 
        >>> asyncio.run(main())
        'value'
    
    Pub/Sub usage:
        >>> from ailf.messaging.redis import RedisPubSub
        >>> 
        >>> # Publisher
        >>> pubsub = RedisPubSub()
        >>> pubsub.publish("channel", {"message": "hello"})
        >>> 
        >>> # Subscriber
        >>> def message_handler(data):
        ...     print(f"Received: {data}")
        >>> 
        >>> pubsub = RedisPubSub()
        >>> pubsub.subscribe("channel", message_handler)
        >>> pubsub.run()  # Blocks and processes messages
"""
import json
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import redis
from pydantic import BaseModel
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError

from ailf.core.logging import setup_logging

logger = setup_logging(__name__)

# Type variable for return values
T = TypeVar('T')


class RedisConfig(BaseModel):
    """Redis connection configuration.

    Attributes:
        host: Redis server hostname
        port: Redis server port
        db: Redis database number
        password: Optional Redis password
        ssl: Whether to use SSL for the connection
        socket_timeout: Socket timeout in seconds
        socket_connect_timeout: Socket connection timeout in seconds
        socket_keepalive: Whether to enable TCP keepalive
        retry_on_timeout: Whether to retry commands on timeout errors
        max_connections: Maximum number of connections in the connection pool
        decode_responses: Whether to decode byte responses to strings
    """
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True
    retry_on_timeout: bool = True
    max_connections: int = 10
    decode_responses: bool = True

    class Config:
        """Pydantic model configuration."""
        frozen = True


class RedisClient:
    """Synchronous Redis client for agent communication.

    This class provides a simplified interface to Redis operations with
    error handling, logging, and convenience methods for common operations.

    Attributes:
        config: Redis connection configuration
        client: Raw Redis client instance
    """

    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize the Redis client.

        Args:
            config: Redis connection configuration (optional)
        """
        self.config = config or RedisConfig()
        self._client = None
        self.connect()

    def connect(self) -> None:
        """Connect to Redis server."""
        try:
            self._client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                ssl=self.config.ssl,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                socket_keepalive=self.config.socket_keepalive,
                # retry_on_timeout parameter is deprecated in newer Redis versions
                decode_responses=self.config.decode_responses,
                max_connections=self.config.max_connections
            )
            # Test the connection
            self._client.ping()
            logger.info(
                f"Connected to Redis at {self.config.host}:{self.config.port}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    @property
    def client(self) -> redis.Redis:
        """Get the raw Redis client.

        Returns:
            The underlying Redis client instance
        """
        if self._client is None:
            self.connect()
        return self._client

    def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            self._client.close()
            self._client = None
            logger.debug("Redis connection closed")

    @contextmanager
    def pipeline(self):
        """Create a Redis pipeline for batched operations.

        Yields:
            A Redis pipeline object
        """
        pipe = self.client.pipeline()
        try:
            yield pipe
        finally:
            pipe.execute()

    def get(self, key: str) -> Optional[str]:
        """Get a value from Redis.

        Args:
            key: The key to get

        Returns:
            The value of the key, or None if it doesn't exist
        """
        try:
            return self.client.get(key)
        except RedisError as e:
            logger.error(f"Error getting key {key}: {str(e)}")
            return None

    def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set a value in Redis.

        Args:
            key: The key to set
            value: The value to set
            expire: Optional expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.client.set(key, value, ex=expire)
        except RedisError as e:
            logger.error(f"Error setting key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from Redis.

        Args:
            key: The key to delete

        Returns:
            True if the key was deleted, False otherwise
        """
        try:
            return bool(self.client.delete(key))
        except RedisError as e:
            logger.error(f"Error deleting key {key}: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        except RedisError as e:
            logger.error(f"Error checking key {key}: {str(e)}")
            return False

    def set_json(self, key: str, value: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Set a JSON value in Redis.

        Args:
            key: The key to set
            value: The dictionary to serialize and store
            expire: Optional expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            json_str = json.dumps(value)
            return self.set(key, json_str, expire)
        except Exception as e:
            logger.error(f"Error setting JSON key {key}: {str(e)}")
            return False

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a JSON value from Redis.

        Args:
            key: The key to get

        Returns:
            The deserialized JSON value, or None if it doesn't exist
        """
        try:
            value = self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting JSON key {key}: {str(e)}")
            return None

    def publish(self, channel: str, message: Union[str, Dict[str, Any]]) -> int:
        """Publish a message to a Redis channel.

        Args:
            channel: The channel to publish to
            message: The message to publish (string or dict)

        Returns:
            Number of clients that received the message
        """
        try:
            # Convert dict to JSON string if necessary
            if isinstance(message, dict):
                message = json.dumps(message)

            return self.client.publish(channel, message)
        except RedisError as e:
            logger.error(f"Error publishing to channel {channel}: {str(e)}")
            return 0

    def health_check(self) -> bool:
        """Check if Redis connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            return self.client.ping()
        except RedisError:
            return False


class AsyncRedisClient:
    """Asynchronous Redis client for agent communication.

    This class provides an async interface to Redis operations with
    error handling, logging, and convenience methods.

    Attributes:
        config: Redis connection configuration
        client: Raw Redis async client instance
    """

    def __init__(self, config: Optional[RedisConfig] = None):
        """Initialize the async Redis client.

        Args:
            config: Redis connection configuration (optional)
        """
        self.config = config or RedisConfig()
        self._client = None

    async def connect(self) -> None:
        """Connect to Redis server asynchronously."""
        try:
            self._client = AsyncRedis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                ssl=self.config.ssl,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                socket_keepalive=self.config.socket_keepalive,
                # retry_on_timeout parameter is deprecated in newer Redis versions
                decode_responses=self.config.decode_responses,
                max_connections=self.config.max_connections
            )
            # Test the connection
            await self._client.ping()
            logger.info(
                f"Connected to Redis at {self.config.host}:{self.config.port}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    @property
    async def client(self) -> AsyncRedis:
        """Get the raw Redis client asynchronously.

        Returns:
            The underlying Redis client instance
        """
        if self._client is None:
            await self.connect()
        return self._client

    async def close(self) -> None:
        """Close the Redis connection asynchronously."""
        if self._client:
            # Use aclose() instead of close() as recommended by Redis library
            await self._client.aclose()
            self._client = None
            logger.debug("Redis connection closed")

    @asynccontextmanager
    async def pipeline(self):
        """Create a Redis pipeline for batched operations asynchronously.

        Yields:
            A Redis pipeline object
        """
        client = await self.client
        pipe = client.pipeline()
        try:
            yield pipe
        finally:
            await pipe.execute()

    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis asynchronously.

        Args:
            key: The key to get

        Returns:
            The value of the key, or None if it doesn't exist
        """
        try:
            client = await self.client
            return await client.get(key)
        except RedisError as e:
            logger.error(f"Error getting key {key}: {str(e)}")
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set a value in Redis asynchronously.

        Args:
            key: The key to set
            value: The value to set
            expire: Optional expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await self.client
            return await client.set(key, value, ex=expire)
        except RedisError as e:
            logger.error(f"Error setting key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from Redis asynchronously.

        Args:
            key: The key to delete

        Returns:
            True if the key was deleted, False otherwise
        """
        try:
            client = await self.client
            return bool(await client.delete(key))
        except RedisError as e:
            logger.error(f"Error deleting key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis asynchronously.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        try:
            client = await self.client
            return bool(await client.exists(key))
        except RedisError as e:
            logger.error(f"Error checking key {key}: {str(e)}")
            return False

    async def set_json(self, key: str, value: Dict[str, Any], expire: Optional[int] = None) -> bool:
        """Set a JSON value in Redis asynchronously.

        Args:
            key: The key to set
            value: The dictionary to serialize and store
            expire: Optional expiration time in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, expire)
        except Exception as e:
            logger.error(f"Error setting JSON key {key}: {str(e)}")
            return False

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a JSON value from Redis asynchronously.

        Args:
            key: The key to get

        Returns:
            The deserialized JSON value, or None if it doesn't exist
        """
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting JSON key {key}: {str(e)}")
            return None

    async def publish(self, channel: str, message: Union[str, Dict[str, Any]]) -> int:
        """Publish a message to a Redis channel asynchronously.

        Args:
            channel: The channel to publish to
            message: The message to publish (string or dict)

        Returns:
            Number of clients that received the message
        """
        try:
            # Convert dict to JSON string if necessary
            if isinstance(message, dict):
                message = json.dumps(message)

            client = await self.client
            return await client.publish(channel, message)
        except RedisError as e:
            logger.error(f"Error publishing to channel {channel}: {str(e)}")
            return 0

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy asynchronously.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            client = await self.client
            return await client.ping()
        except RedisError:
            return False


class RedisPubSub:
    """High-level Redis Pub/Sub interface.

    This class provides a simple interface for Pub/Sub messaging patterns
    with automatic JSON serialization/deserialization.

    Attributes:
        client: Redis client instance
        subscriptions: Dictionary of channel to handler mappings
    """

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """Initialize the Redis Pub/Sub interface.

        Args:
            redis_client: Optional Redis client to use
        """
        self.client = redis_client or RedisClient()
        self.pubsub = self.client.client.pubsub()
        self.subscriptions: Dict[str, Callable] = {}
        self._running = False
        self._thread = None

    def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish a message to a channel.

        Args:
            channel: Channel name to publish to
            message: Message data to publish (will be JSON encoded)

        Returns:
            Number of clients that received the message
        """
        return self.client.publish(channel, message)

    def subscribe(self, channel: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to a channel.

        Args:
            channel: Channel name to subscribe to
            handler: Function to call with received messages
        """
        self.subscriptions[channel] = handler
        self.pubsub.subscribe(**{channel: self._message_handler})
        logger.info(f"Subscribed to Redis channel: {channel}")

    def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel.

        Args:
            channel: Channel name to unsubscribe from
        """
        if channel in self.subscriptions:
            self.pubsub.unsubscribe(channel)
            del self.subscriptions[channel]
            logger.info(f"Unsubscribed from Redis channel: {channel}")

    def _message_handler(self, message: Dict[str, Any]) -> None:
        """Handle incoming messages.

        Args:
            message: Raw message from Redis
        """
        if message["type"] == "message":
            channel = message["channel"]
            data = message["data"]

            # Try to parse JSON data
            try:
                if isinstance(data, str):
                    data = json.loads(data)
            except json.JSONDecodeError:
                pass

            # Call the appropriate handler
            if channel in self.subscriptions:
                try:
                    self.subscriptions[channel](data)
                except Exception as e:
                    logger.error(
                        f"Error in message handler for channel {channel}: {str(e)}")

    def run(self) -> None:
        """Start listening for messages in the current thread (blocking).

        This method will block until stop() is called from another thread.
        """
        self._running = True
        try:
            for message in self.pubsub.listen():
                if not self._running:
                    break
                if message["type"] == "message":
                    self._message_handler(message)
        finally:
            self._running = False

    def run_in_thread(self, daemon: bool = True) -> threading.Thread:
        """Start listening for messages in a background thread.

        Args:
            daemon: Whether the thread should be a daemon

        Returns:
            The background thread
        """
        self._thread = threading.Thread(target=self.run, daemon=daemon)
        self._thread.start()
        return self._thread

    def stop(self) -> None:
        """Stop listening for messages."""
        self._running = False
        try:
            self.pubsub.close()
        except Exception as e:
            # Safely handle any errors during close
            logger.debug(f"Error closing pubsub: {str(e)}")

    def __del__(self):
        """Clean up resources."""
        try:
            self.stop()
        except Exception:
            # Ignore errors during garbage collection
            pass


class RedisStream:
    """High-level Redis Stream interface.

    Redis Streams are an append-only data structure that can be used for
    message brokers, event sourcing, and time-series data.

    Attributes:
        client: Redis client instance
        stream_name: Name of the stream
    """

    def __init__(self, stream_name: str, redis_client: Optional[RedisClient] = None):
        """Initialize the Redis Stream interface.

        Args:
            stream_name: Name of the stream
            redis_client: Optional Redis client to use
        """
        self.client = redis_client or RedisClient()
        self.stream_name = stream_name
        self._consumer_group = None
        self._consumer_name = None
        self._running = False
        self._thread = None

    def add(self, data: Dict[str, Any]) -> str:
        """Add a message to the stream.

        Args:
            data: Message data (values must be strings)

        Returns:
            Message ID
        """
        # Convert all values to strings (Redis requirement)
        string_data = {k: str(v) for k, v in data.items()}

        try:
            return self.client.client.xadd(self.stream_name, string_data)
        except RedisError as e:
            logger.error(
                f"Error adding to stream {self.stream_name}: {str(e)}")
            raise

    def read(self, count: int = 10, block: Optional[int] = None, last_id: str = "$") -> List[Dict[str, Any]]:
        """Read messages from the stream.

        Args:
            count: Maximum number of messages to read
            block: Milliseconds to block waiting for messages (None = no blocking)
            last_id: ID to start reading from ($ = only new messages)

        Returns:
            List of messages
        """
        try:
            response = self.client.client.xread(
                {self.stream_name: last_id}, count=count, block=block)
            result = []

            if response:
                for stream_name, messages in response:
                    for message_id, fields in messages:
                        result.append({
                            "id": message_id,
                            "data": fields
                        })

            return result
        except RedisError as e:
            logger.error(
                f"Error reading from stream {self.stream_name}: {str(e)}")
            return []

    def create_consumer_group(self, group_name: str, consumer_name: str, start_id: str = "$") -> bool:
        """Create a consumer group for the stream.

        Args:
            group_name: Name of the consumer group
            consumer_name: Name of this consumer
            start_id: ID to start consuming from ($ = only new messages, 0 = all messages)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if stream exists and create if not
            if not self.client.client.exists(self.stream_name):
                self.client.client.xadd(self.stream_name, {"create": "stream"})

            # Create the consumer group
            try:
                self.client.client.xgroup_create(
                    self.stream_name, group_name, start_id)
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            self._consumer_group = group_name
            self._consumer_name = consumer_name
            return True
        except RedisError as e:
            logger.error(
                f"Error creating consumer group for stream {self.stream_name}: {str(e)}")
            return False

    def read_group(self, count: int = 10, block: Optional[int] = None, last_id: str = ">") -> List[Dict[str, Any]]:
        """Read messages from the stream as part of a consumer group.

        Args:
            count: Maximum number of messages to read
            block: Milliseconds to block waiting for messages (None = no blocking)
            last_id: ID to start reading from (> = only new messages)

        Returns:
            List of messages
        """
        if not self._consumer_group:
            raise ValueError(
                "No consumer group set. Call create_consumer_group first.")

        try:
            response = self.client.client.xreadgroup(
                self._consumer_group,
                self._consumer_name,
                {self.stream_name: last_id},
                count=count,
                block=block
            )

            result = []

            if response:
                for stream_name, messages in response:
                    for message_id, fields in messages:
                        result.append({
                            "id": message_id,
                            "data": fields
                        })

            return result
        except RedisError as e:
            logger.error(
                f"Error reading from group in stream {self.stream_name}: {str(e)}")
            return []

    def acknowledge(self, message_id: str) -> bool:
        """Acknowledge a message as processed.

        Args:
            message_id: ID of the message to acknowledge

        Returns:
            True if successful, False otherwise
        """
        if not self._consumer_group:
            raise ValueError(
                "No consumer group set. Call create_consumer_group first.")

        try:
            return bool(self.client.client.xack(self.stream_name, self._consumer_group, message_id))
        except RedisError as e:
            logger.error(
                f"Error acknowledging message in stream {self.stream_name}: {str(e)}")
            return False

    def process_messages(
        self,
        processor: Callable[[Dict[str, Any]], bool],
        count: int = 10,
        block: int = 1000,
        last_id: str = ">"
    ) -> None:
        """Process messages from the stream.

        Args:
            processor: Function to process each message
            count: Maximum number of messages to process per batch
            block: Milliseconds to block waiting for messages
            last_id: ID to start reading from (> = only new messages)
        """
        self._running = True

        while self._running:
            messages = self.read_group(
                count=count, block=block, last_id=last_id)

            for message in messages:
                try:
                    # Process the message
                    success = processor(message["data"])

                    # Acknowledge if processed successfully
                    if success:
                        self.acknowledge(message["id"])
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")

    def process_in_thread(
        self,
        processor: Callable[[Dict[str, Any]], bool],
        count: int = 10,
        block: int = 1000,
        daemon: bool = True
    ) -> threading.Thread:
        """Process messages from the stream in a background thread.

        Args:
            processor: Function to process each message
            count: Maximum number of messages to process per batch
            block: Milliseconds to block waiting for messages
            daemon: Whether the thread should be a daemon

        Returns:
            The background thread
        """
        self._thread = threading.Thread(
            target=self.process_messages,
            args=(processor, count, block),
            daemon=daemon
        )
        self._thread.start()
        return self._thread

    def stop(self) -> None:
        """Stop processing messages."""
        self._running = False


class RedisLock:
    """Distributed lock implementation using Redis.

    This class implements the Redis distributed lock pattern (RedLock) for
    ensuring mutual exclusion across processes/servers.

    Attributes:
        client: Redis client instance
        lock_name: Name of the lock
        expire: Lock expiration time in seconds
    """

    def __init__(
        self,
        lock_name: str,
        expire: int = 10,
        redis_client: Optional[RedisClient] = None
    ):
        """Initialize the Redis lock.

        Args:
            lock_name: Name of the lock
            expire: Lock expiration time in seconds (default: 10)
            redis_client: Optional Redis client to use
        """
        self.client = redis_client or RedisClient()
        self.lock_name = f"lock:{lock_name}"
        self.expire = expire
        self.token = None

    def acquire(self, retry: int = 3, retry_delay: float = 0.2) -> bool:
        """Acquire the lock.

        Args:
            retry: Number of times to retry if lock acquisition fails
            retry_delay: Delay between retries in seconds

        Returns:
            True if lock was acquired, False otherwise
        """
        # Generate a unique token for this lock
        import uuid
        self.token = str(uuid.uuid4())

        # Try to acquire the lock
        for attempt in range(retry + 1):
            # Use SET NX EX to acquire the lock
            result = self.client.client.set(
                self.lock_name,
                self.token,
                nx=True,
                ex=self.expire
            )

            if result:
                logger.debug(f"Acquired lock: {self.lock_name}")
                return True

            if attempt < retry:
                time.sleep(retry_delay)

        logger.debug(f"Failed to acquire lock: {self.lock_name}")
        return False

    def release(self) -> bool:
        """Release the lock.

        Returns:
            True if lock was released, False otherwise
        """
        if not self.token:
            return False

        # Use a Lua script to ensure we only delete our own lock
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            result = self.client.client.eval(
                script, 1, self.lock_name, self.token)
            success = bool(result)
            if success:
                logger.debug(f"Released lock: {self.lock_name}")
            return success
        except RedisError as e:
            logger.error(f"Error releasing lock {self.lock_name}: {str(e)}")
            return False

    @contextmanager
    def acquire_context(self, retry: int = 3, retry_delay: float = 0.2):
        """Context manager for acquiring and releasing a lock.

        Args:
            retry: Number of times to retry if lock acquisition fails
            retry_delay: Delay between retries in seconds

        Yields:
            True if lock was acquired, False otherwise
        """
        acquired = self.acquire(retry, retry_delay)
        try:
            yield acquired
        finally:
            if acquired:
                self.release()


class RedisRateLimiter:
    """Rate limiter implementation using Redis.

    This class implements token bucket rate limiting using Redis.

    Attributes:
        client: Redis client instance
        key_prefix: Prefix for rate limiter keys
        rate: Number of tokens per time period
        period: Time period in seconds
    """

    def __init__(
        self,
        key_prefix: str,
        rate: int = 10,
        period: int = 1,
        redis_client: Optional[RedisClient] = None
    ):
        """Initialize the rate limiter.

        Args:
            key_prefix: Prefix for rate limiter keys
            rate: Number of tokens per time period (default: 10)
            period: Time period in seconds (default: 1)
            redis_client: Optional Redis client to use
        """
        self.client = redis_client or RedisClient()
        self.key_prefix = f"ratelimit:{key_prefix}"
        self.rate = rate
        self.period = period

    def is_allowed(self, key: str) -> bool:
        """Check if an action is allowed under the rate limit.

        Args:
            key: Identifier for the entity being rate limited

        Returns:
            True if action is allowed, False otherwise
        """
        redis_key = f"{self.key_prefix}:{key}"

        # Use Redis pipeline for atomic operations
        with self.client.pipeline() as pipe:
            now = time.time()

            # Clean up old tokens
            pipe.zremrangebyscore(redis_key, 0, now - self.period)

            # Count remaining tokens
            pipe.zcard(redis_key)

            # Add a new token
            pipe.zadd(redis_key, {str(now): now})

            # Set key expiration
            pipe.expire(redis_key, self.period)

            # Execute the pipeline
            _, tokens, _, _ = pipe.execute()

            # Check if under the limit
            return tokens <= self.rate
