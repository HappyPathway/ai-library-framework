"""AILF Communication Package.

This package provides components for inter-agent communication, including
the Agent Communication Protocol (ACP) handling and integration with
various messaging backends.

Key Components:
    ACPHandler: Manages sending and receiving structured ACP messages.
    A2AClient: Client for interacting with A2A-compatible agents.
    AILFASA2AServer: Base class for exposing AILF agents as A2A-compatible servers.
"""

from .handler import ACPHandler
from .a2a_client import A2AClient, A2AClientError, A2AHTTPError, A2AJSONError
from .a2a_server import (
    AILFASA2AServer,
    A2AAgentExecutor,
    A2ARequestContext,
    A2AServerError,
    TaskStore,
)

__all__ = [
    "ACPHandler",
    "A2AClient",
    "A2AClientError", 
    "A2AHTTPError",
    "A2AJSONError",
    "AILFASA2AServer",
    "A2AAgentExecutor",
    "A2ARequestContext",
    "A2AServerError",
    "TaskStore",
]
