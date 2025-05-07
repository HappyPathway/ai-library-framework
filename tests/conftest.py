"""
Global pytest configuration for the project.
"""

import os
import sys
import pytest
import redis

from utils.messaging.redis import RedisClient, RedisConfig
from ailf.messaging.mock_redis import MockRedisClient

# Add the project root to the path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Skip tests that require external services if running in CI without credentials


def pytest_configure(config):
    """Configure pytest with custom markers."""
    # Register all markers to avoid warnings
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running test")
    config.addinivalue_line(
        "markers", "requires_redis: mark test as requiring a real Redis server"
    )


# Define fixtures that should be available to all tests


@pytest.fixture(scope="session")
def temp_dir(tmpdir_factory):
    """Create a temporary directory for the test session."""
    return tmpdir_factory.mktemp("test_data")


@pytest.fixture(scope="session")
def test_env():
    """Return environment variables needed for tests."""
    return {
        "has_openai": "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"],
        "has_gemini": "GEMINI_API_KEY" in os.environ and os.environ["GEMINI_API_KEY"],
        "has_anthropic": "ANTHROPIC_API_KEY" in os.environ and os.environ["ANTHROPIC_API_KEY"],
        "has_gcp": "GOOGLE_APPLICATION_CREDENTIALS" in os.environ and os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
        "has_github": "GITHUB_TOKEN" in os.environ and os.environ["GITHUB_TOKEN"],
    }


def is_redis_available():
    """Check if Redis server is available.
    
    Returns:
        bool: True if Redis server is available, False otherwise.
    """
    try:
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        return r.ping()
    except (redis.exceptions.ConnectionError, redis.exceptions.ResponseError):
        return False


@pytest.fixture
def redis_config():
    """Provide Redis configuration for tests.
    
    Returns:
        RedisConfig: Configuration for Redis client with test-specific settings.
    """
    return RedisConfig(
        host='localhost',
        port=6379,
        db=1,  # Use database 1 for tests to avoid conflicts
        decode_responses=True
    )


@pytest.fixture
def redis_client(redis_config):
    """Return a Redis client for testing.
    
    Tries to use a real Redis server if available, otherwise falls back to mock.
    Redis database is flushed before and after tests to ensure clean state.
    
    Args:
        redis_config: Redis configuration fixture
    
    Returns:
        RedisClient or MockRedisClient: Redis client instance
    """
    if os.environ.get('FORCE_MOCK_REDIS'):
        # Force mock Redis if explicitly requested
        client = MockRedisClient(redis_config)
        yield client
        return
    
    if is_redis_available():
        # Use real Redis if available
        client = RedisClient(redis_config)
        
        # Clean database before test
        client.client.flushdb()
        
        yield client
        
        # Clean up after test
        client.client.flushdb()
        client.close()
    else:
        # Fall back to mock Redis if real Redis isn't available
        print("Real Redis not available, using mock implementation")
        client = MockRedisClient(redis_config)
        yield client


@pytest.fixture
def clear_redis(redis_client):
    """Ensure Redis database is empty.
    
    This fixture can be used when tests need to start with a clean Redis state.
    
    Args:
        redis_client: Redis client fixture
    """
    if hasattr(redis_client, 'client') and hasattr(redis_client.client, 'flushdb'):
        redis_client.client.flushdb()
    yield
    if hasattr(redis_client, 'client') and hasattr(redis_client.client, 'flushdb'):
        redis_client.client.flushdb()


@pytest.fixture(scope="function")
def requires_real_redis():
    """Skip test if real Redis is not available."""
    if not is_redis_available():
        pytest.skip("This test requires a real Redis server")
