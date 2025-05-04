"""Schema Models

This package contains Pydantic models used throughout the application.
Each module contains models related to a specific domain or functionality.
"""

from .ai import AIResponse, UsageLimits
from .mcp import (AssistantMessage, DuplicateHandling, MCPSettings, Message,
                  PromptMetadata, ResourceMetadata, SystemMessage,
                  ToolMetadata, UserMessage)
from .storage import StorageConfig
# Import commonly used models for convenience
from .zmq import MessageEnvelope, SocketType, ZMQConfig
from .zmq_devices import AuthConfig, DeviceConfig, DeviceType

__all__ = [
    # ZMQ models
    "MessageEnvelope", "SocketType", "ZMQConfig",
    # ZMQ device models
    "DeviceConfig", "DeviceType", "AuthConfig",
    # Storage models
    "StorageConfig",
    # AI models
    "AIResponse", "UsageLimits",
    # MCP models
    "MCPSettings", "ToolMetadata", "ResourceMetadata", "PromptMetadata",
    "DuplicateHandling", "Message", "UserMessage", "AssistantMessage", "SystemMessage",
]
