"""Tests for Redis messaging components.

This module tests the Redis messaging patterns.
"""

import json
import unittest
from unittest import mock

import pytest

from ailf.messaging.redis import RedisClient, RedisPubSub, RedisStream
from ailf.schemas.redis import RedisConfig


class TestRedisConfig(unittest.TestCase):
    """Test the RedisConfig model."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = RedisConfig()
        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 6379)
        self.assertEqual(config.db, 0)
        self.assertIsNone(config.password)
        self.assertFalse(config.ssl)
        self.assertEqual(config.socket_timeout, 5)
        self.assertEqual(config.socket_connect_timeout, 5)
        self.assertTrue(config.socket_keepalive)
        self.assertEqual(config.max_connections, 10)
        self.assertTrue(config.decode_responses)
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            ssl=True,
            socket_timeout=10,
            socket_connect_timeout=10,
            socket_keepalive=False,
            max_connections=20,
            decode_responses=False
        )
        self.assertEqual(config.host, "redis.example.com")
        self.assertEqual(config.port, 6380)
        self.assertEqual(config.db, 1)
        self.assertEqual(config.password, "secret")
        self.assertTrue(config.ssl)
        self.assertEqual(config.socket_timeout, 10)
        self.assertEqual(config.socket_connect_timeout, 10)
        self.assertFalse(config.socket_keepalive)
        self.assertEqual(config.max_connections, 20)
        self.assertFalse(config.decode_responses)


class TestRedisClient:
    """Test the RedisClient class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        with mock.patch('ailf.messaging.redis.redis') as mock_redis_module:
            mock_client = mock.MagicMock()
            mock_redis_module.Redis.return_value = mock_client
            yield mock_client
    
    def test_init(self, mock_redis):
        """Test initialization."""
        client = RedisClient()
        assert client.config.host == "localhost"
        assert client.config.port == 6379
        
    def test_get(self, mock_redis):
        """Test get operation."""
        mock_redis.get.return_value = "value"
        client = RedisClient()
        result = client.get("key")
        mock_redis.get.assert_called_once_with("key")
        assert result == "value"
        
    def test_set(self, mock_redis):
        """Test set operation."""
        mock_redis.set.return_value = True
        client = RedisClient()
        result = client.set("key", "value")
        mock_redis.set.assert_called_once_with("key", "value", ex=None)
        assert result is True
        
    def test_delete(self, mock_redis):
        """Test delete operation."""
        mock_redis.delete.return_value = 1
        client = RedisClient()
        result = client.delete("key")
        mock_redis.delete.assert_called_once_with("key")
        assert result is True
        
    def test_exists(self, mock_redis):
        """Test exists operation."""
        mock_redis.exists.return_value = 1
        client = RedisClient()
        result = client.exists("key")
        mock_redis.exists.assert_called_once_with("key")
        assert result is True
        
    def test_set_json(self, mock_redis):
        """Test set_json operation."""
        mock_redis.set.return_value = True
        client = RedisClient()
        data = {"name": "test", "value": 123}
        result = client.set_json("key", data)
        mock_redis.set.assert_called_once_with("key", json.dumps(data), ex=None)
        assert result is True
        
    def test_get_json(self, mock_redis):
        """Test get_json operation."""
        data = {"name": "test", "value": 123}
        mock_redis.get.return_value = json.dumps(data)
        client = RedisClient()
        result = client.get_json("key")
        mock_redis.get.assert_called_once_with("key")
        assert result == data


class TestRedisPubSub:
    """Test the RedisPubSub class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        with mock.patch('ailf.messaging.redis.redis') as mock_redis_module:
            mock_client = mock.MagicMock()
            mock_pubsub = mock.MagicMock()
            mock_client.pubsub.return_value = mock_pubsub
            mock_redis_module.Redis.return_value = mock_client
            yield mock_client, mock_pubsub
    
    def test_init(self, mock_redis):
        """Test initialization."""
        mock_client, _ = mock_redis
        pubsub = RedisPubSub()
        assert pubsub.client is not None
        
    def test_publish(self, mock_redis):
        """Test publish operation."""
        mock_client, _ = mock_redis
        mock_client.publish.return_value = 5  # 5 clients received the message
        
        pubsub = RedisPubSub()
        message = {"type": "alert", "message": "Test"}
        result = pubsub.publish("channel", message)
        
        mock_client.publish.assert_called_once()
        assert result == 5
        
    def test_subscribe(self, mock_redis):
        """Test subscribe operation."""
        mock_client, mock_pubsub = mock_redis
        
        def handler(message):
            pass
            
        pubsub = RedisPubSub()
        pubsub.subscribe("channel", handler)
        
        mock_pubsub.subscribe.assert_called_once_with("channel")
        assert "channel" in pubsub.subscriptions
        assert pubsub.subscriptions["channel"] == handler
        
    def test_unsubscribe(self, mock_redis):
        """Test unsubscribe operation."""
        mock_client, mock_pubsub = mock_redis
        
        def handler(message):
            pass
            
        pubsub = RedisPubSub()
        pubsub.subscribe("channel", handler)
        pubsub.unsubscribe("channel")
        
        mock_pubsub.unsubscribe.assert_called_once_with("channel")
        assert "channel" not in pubsub.subscriptions


class TestRedisStream:
    """Test the RedisStream class."""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        with mock.patch('ailf.messaging.redis.redis') as mock_redis_module:
            mock_client = mock.MagicMock()
            mock_redis_module.Redis.return_value = mock_client
            yield mock_client
    
    def test_init(self, mock_redis):
        """Test initialization."""
        stream = RedisStream("test-stream")
        assert stream.stream_name == "test-stream"
        assert stream.client is not None
        
    def test_add(self, mock_redis):
        """Test add operation."""
        mock_redis.xadd.return_value = "1234567890-0"
        
        stream = RedisStream("test-stream")
        data = {"type": "event", "name": "test"}
        result = stream.add(data)
        
        mock_redis.xadd.assert_called_once()
        assert result == "1234567890-0"
        
    def test_read(self, mock_redis):
        """Test read operation."""
        # Mock the complex nested structure returned by xread
        mock_redis.xread.return_value = [
            (b'test-stream', [(b'1234567890-0', {b'type': b'event', b'name': b'test'})])
        ]
        
        stream = RedisStream("test-stream")
        result = stream.read(count=1)
        
        mock_redis.xread.assert_called_once()
        assert len(result) == 1
        assert result[0]['id'] == "1234567890-0"
        assert result[0]['data']['type'] == 'event'
        assert result[0]['data']['name'] == 'test'
        
    def test_create_consumer_group(self, mock_redis):
        """Test create_consumer_group operation."""
        mock_redis.exists.return_value = True
        mock_redis.xgroup_create.return_value = True
        
        stream = RedisStream("test-stream")
        result = stream.create_consumer_group("group1", "consumer1")
        
        mock_redis.xgroup_create.assert_called_once()
        assert result is True
        assert stream._consumer_group == "group1"
        assert stream._consumer_name == "consumer1"
        
    def test_read_group(self, mock_redis):
        """Test read_group operation."""
        # Mock the complex nested structure returned by xreadgroup
        mock_redis.xreadgroup.return_value = [
            (b'test-stream', [(b'1234567890-0', {b'type': b'event', b'name': b'test'})])
        ]
        
        stream = RedisStream("test-stream")
        stream._consumer_group = "group1"
        stream._consumer_name = "consumer1"
        
        result = stream.read_group(count=1)
        
        mock_redis.xreadgroup.assert_called_once()
        assert len(result) == 1
        assert result[0]['id'] == "1234567890-0"
        assert result[0]['data']['type'] == 'event'
        assert result[0]['data']['name'] == 'test'
        
    def test_acknowledge(self, mock_redis):
        """Test acknowledge operation."""
        mock_redis.xack.return_value = 1
        
        stream = RedisStream("test-stream")
        stream._consumer_group = "group1"
        
        result = stream.acknowledge("1234567890-0")
        
        mock_redis.xack.assert_called_once()
        assert result is True
        
    def test_read_group_no_consumer_group(self, mock_redis):
        """Test read_group with no consumer group set."""
        stream = RedisStream("test-stream")
        result = stream.read_group()
        
        mock_redis.xreadgroup.assert_not_called()
        assert result == []
        
    def test_acknowledge_no_consumer_group(self, mock_redis):
        """Test acknowledge with no consumer group set."""
        stream = RedisStream("test-stream")
        result = stream.acknowledge("1234567890-0")
        
        mock_redis.xack.assert_not_called()
        assert result is False


if __name__ == '__main__':
    unittest.main()
