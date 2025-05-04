"""Utils messaging package.

This package provides implementations for various messaging systems to enable
distributed agent communication.
"""

from importlib.util import find_spec

# Conditionally expose Redis client if redis package is installed
if find_spec('redis'):
    try:
        from .redis import (AsyncRedisClient, RedisClient, RedisConfig,
                            RedisLock, RedisPubSub, RedisRateLimiter,
                            RedisStream)
        __all__ = [
            'RedisClient',
            'AsyncRedisClient',
            'RedisConfig',
            'RedisPubSub',
            'RedisStream',
            'RedisLock',
            'RedisRateLimiter'
        ]
    except ImportError:
        pass

# Expose existing ZMQ functionality
try:
    from ..zmq import ZMQClient
    from ..zmq_devices import DeviceType, ZMQDevice

    # Add ZMQ to __all__ if already defined, otherwise create it
    if '__all__' in locals():
        __all__.extend(['ZMQClient', 'ZMQDevice', 'DeviceType'])
    else:
        __all__ = ['ZMQClient', 'ZMQDevice', 'DeviceType']
except ImportError:
    pass
