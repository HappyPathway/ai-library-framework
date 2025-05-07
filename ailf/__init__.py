"""AI Liberation Front.

A comprehensive toolkit for building autonomous AI agents with:

- Structured LLM interactions via Pydantic models
- Tool registration and management
- AI engine abstraction for multiple providers
- Distributed computing via ZeroMQ and Redis
- Configurable storage backends
- Comprehensive logging and monitoring
- Secure secret management
- MCP server functionality

The package is designed to liberate AI developers from repetitive infrastructure work
and provide a solid foundation for building sophisticated agent systems.
"""

__version__ = "0.1.0"

# Direct imports for convenience
from .ai_engine import AIEngine, AIEngineError
from .async_tasks import TaskManager, TaskStatus
from .base_mcp import BaseMCP, Context

# Core utilities
from .core.logging import setup_logging
from .core.monitoring import setup_monitoring
from .core.storage import LocalStorage, CloudStorage
from .core.secrets import get_secret

# Core components
from .core.logging import setup_logging
from .core.monitoring import setup_monitoring
from .core.storage import LocalStorage, CloudStorage
from .core.secrets import get_secret

# Messaging components
from .messaging.zmq import ZMQPublisher, ZMQSubscriber, ZMQClient, ZMQServer
from .messaging.zmq_devices import ZMQDevice, ZMQForwarder, ZMQStreamer, ZMQProxy
from .messaging.zmq_device_manager import DeviceManager, create_device
from .messaging.redis import RedisClient, RedisPubSub, RedisStream, AsyncRedisClient

# Schema components
from .schemas.redis import RedisConfig

# Type hints for public API
__all__ = [
    # Main components
    "AIEngine",
    "AIEngineError",
    "BaseMCP",
    "Context",
    
    # Core utilities
    "setup_logging",
    "setup_monitoring",
    "LocalStorage",
    "CloudStorage",
    "get_secret",
    
    # Redis components
    "RedisClient",
    "AsyncRedisClient",
    "RedisPubSub", 
    "RedisStream",
    "RedisConfig",
    
    # ZMQ components
    "ZMQPublisher",
    "ZMQSubscriber",
    "ZMQClient",
    "ZMQServer",
    "ZMQDevice",
    "ZMQForwarder",
    "ZMQStreamer", 
    "ZMQProxy",
    "DeviceManager",
    "create_device",
]
