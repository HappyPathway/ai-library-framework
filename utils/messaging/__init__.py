"""Utils messaging package.

This package provides implementations for various messaging systems to enable
distributed agent communication.
"""

from importlib.util import find_spec

# Initialize __all__ to avoid "used before assignment" error
__all__ = []

# Conditionally expose Redis client if redis package is installed
if find_spec('redis'):
    try:
        from .redis import (AsyncRedisClient, RedisClient, RedisConfig,
                            RedisLock, RedisPubSub, RedisRateLimiter,
                            RedisStream)

        # Import async Redis implementations
        try:
            from .async_redis import AsyncRedisPubSub
            has_async_redis = True
        except ImportError:
            has_async_redis = False

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
