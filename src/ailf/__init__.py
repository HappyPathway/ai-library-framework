"""AI Liberation Front: Freedom tools for AI agent development.

This package provides a collection of utilities, patterns, and infrastructure
components specifically designed to accelerate the development of AI agents.
"""

__version__ = "0.1.0"

# Direct imports for convenience
from .ai.engine import AIEngine, AIEngineError
from .async_tasks import TaskManager, TaskStatus
from .mcp.base import BaseMCP, Context

# Cognition components
from .cognition import (
    ReActProcessor, TaskPlanner, IntentRefiner, 
    PromptTemplateV1, PromptLibrary
)

# Core utilities
from .core.logging import setup_logging
from .core.monitoring import setup_monitoring
from .core.storage import LocalStorage, CloudStorage
from .core.secrets import get_secret

# Agent framework components
try:
    from .agent.base import Agent, AgentConfig, AgentStatus
    from .agent.patterns import ReactivePlan, DeliberativePlan, TreeOfThoughtsPlan
    from .agent.tools import tool, ToolRegistry, execute_tool
except ImportError:
    # Agent module may not be installed or available yet
    pass

# AI components
from .ai.engine import AIEngine
from .ai.engine_factory import create_ai_engine
from .ai.openai_engine import OpenAIEngine
try:
    from .ai.anthropic_engine import AnthropicEngine
except ImportError:
    # Anthropic may not be installed
    pass

# Cloud components
from .cloud.secrets import get_secrets_manager
from .cloud.gcs_storage import GCSStorage
from .cloud.gcs_config_stash import ConfigStash as GCSConfigStash

# Messaging components
from .messaging.zmq import ZMQPublisher, ZMQSubscriber, ZMQClient, ZMQServer
from .messaging.zmq_devices import ZMQDevice, ZMQForwarder, ZMQStreamer, ZMQProxy
from .messaging.zmq_device_manager import DeviceManager, create_device
from .messaging.redis import RedisClient, RedisPubSub, RedisStream, AsyncRedisClient
from .messaging.websocket_client import WebSocketClient
from .messaging.websocket_server import WebSocketServer

# Memory components
from .memory import Memory, InMemory, FileMemory
from .memory import ShortTermMemory, LongTermMemory

# Storage components
from .storage.local import LocalStorage
from .storage.database import DatabaseStorage

# Schema components
from .schemas.ai import AIRequest, AIResponse, AIEngineConfig
from .schemas.redis import RedisConfig

# Type hints for public API
__all__ = [
    # Main components
    "AIEngine",
    "AIEngineError",
    "TaskManager",
    "TaskStatus",
    "BaseMCP",
    "Context",
    
    # Agent components
    "Agent",
    "AgentConfig",
    "AgentStatus",
    "ReactivePlan",
    "DeliberativePlan",
    "TreeOfThoughtsPlan",
    "tool",
    "ToolRegistry",
    "execute_tool",
    
    # AI components
    "create_ai_engine",
    "OpenAIEngine",
    "AnthropicEngine",
    "AIRequest",
    "AIResponse",
    "AIEngineConfig",
    
    # Cloud components
    "get_secrets_manager",
    "GCSStorage",
    "GCSConfigStash",
    
    # Memory components
    "Memory",
    "InMemory",
    "FileMemory",
    "RedisMemory",
    "ShortTermMemory",
    "LongTermMemory",
    
    # Cognition components
    "ReActProcessor",
    "TaskPlanner",
    "IntentRefiner",
    "PromptTemplateV1",
    "PromptLibrary",
    
    # Storage components
    "LocalStorage", 
    "DatabaseStorage",
    
    # Core utilities
    "setup_logging",
    "setup_monitoring",
    "get_secret",
    
    # Redis components
    "RedisClient",
    "AsyncRedisClient",
    "RedisPubSub", 
    "RedisStream",
    "RedisConfig",
    
    # WebSocket components
    "WebSocketClient",
    "WebSocketServer",
    
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
