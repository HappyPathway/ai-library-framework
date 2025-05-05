"""Utils messaging package.

This pa        __all__ = [
            'RedisClient',
            'AsyncRedisClient',
            'RedisConfig',
            'RedisPubSub',
            'RedisStream',
            'RedisLock',
            'RedisRateLimiter',
        ]

        # Add AsyncRedisPubSub if available
        if has_async_redis:
            __all__.append('AsyncRedisPubSub')
            
        # Add mock classes if available
        if has_mock_redis:
            __all__.extend(['MockRedisClient', 'MockAsyncRedisClient'])
    except ImportError:
        pass
elif USE_MOCK_REDIS:
    # If redis is not available but we want mock implementations
    try:
        from .mock_redis import MockRedisClient, MockAsyncRedisClient
        
        # Create alias for compatibility
        RedisClient = MockRedisClient
        AsyncRedisClient = MockAsyncRedisClient
        
        __all__ = [
            'MockRedisClient',
            'MockAsyncRedisClient',
            'RedisClient',
            'AsyncRedisClient',
        ]
    except ImportError:
        passimplementations for various messaging systems to enable
distributed agent communication.
"""

import os
from importlib.util import find_spec

# Initialize __all__ to avoid "used before assignment" error
__all__ = []

# Check if we should use mock Redis (for testing without Redis server)
USE_MOCK_REDIS = os.environ.get('USE_MOCK_REDIS', '').lower() in ('true', '1', 'yes')

# Conditionally expose Redis client if redis package is installed
if find_spec('redis') and not USE_MOCK_REDIS:
    try:
        from .redis import (
            AsyncRedisClient,
            RedisClient,
            RedisConfig,
            RedisLock,
            RedisPubSub,
            RedisRateLimiter,
            RedisStream,
        )

        # Import async Redis implementations
        try:
            from .async_redis import AsyncRedisPubSub
            has_async_redis = True
        except ImportError:
            has_async_redis = False

        # Try to import mock implementations for testing without Redis
        try:
            from .mock_redis import MockAsyncRedisClient, MockRedisClient
            has_mock_redis = True
        except ImportError:
            has_mock_redis = False

        __all__ = [
            'RedisClient',
            'AsyncRedisClient',
            'RedisConfig',
            'RedisPubSub',
            'RedisStream',
            'RedisLock',
            'RedisRateLimiter'
        ]

        # Add async Redis classes if available
        if has_async_redis:
            __all__.extend(['AsyncRedisPubSub'])
    except ImportError:
        pass

# Expose existing ZMQ functionality
try:
    # Update import paths to correctly reference zmq.py classes
    from ..schemas.zmq import MessageEnvelope, SocketType, ZMQConfig
    from ..zmq import ZMQError, ZMQManager, ZMQSocket

    # If devices module exists, import from there
    try:
        from .devices import DeviceType, ZMQDevice
        has_devices = True
    except ImportError:
        has_devices = False

    # Add ZMQ to __all__ if already defined, otherwise create it
    __all__.extend([
        'ZMQManager',
        'ZMQSocket',
        'ZMQError',
        'SocketType',
        'ZMQConfig',
        'MessageEnvelope'
    ])
    if has_devices:
        __all__.extend(['ZMQDevice', 'DeviceType'])
except ImportError:
    pass
