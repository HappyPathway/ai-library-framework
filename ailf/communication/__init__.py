"""AILF Communication Package.

This package provides components for inter-agent communication, including
the Agent Communication Protocol (ACP) handling and integration with
various messaging backends.

Key Components:
    ACPHandler: Manages sending and receiving structured ACP messages.
    A2AClient: Client for interacting with A2A-compatible agents.
    AILFASA2AServer: Base class for exposing AILF agents as A2A-compatible servers.
    AGUIClient: Client for interacting with AG-UI-compatible agents.
    AILFAsAGUIServer: Base class for exposing AILF agents as AG-UI-compatible servers.
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
from .ag_ui_client import AGUIClient, AGUIClientError, AGUIHTTPError, AGUIJSONError
from .ag_ui_server import AGUIRequestContext, AGUIExecutor, AILFAsAGUIServer, AGUIServerError
from .ag_ui_executor import SimpleAGUIExecutor
from .ag_ui_advanced import AdvancedAGUIExecutor
from .ag_ui_state import AGUIStateManager
from .ag_ui_tools import AGUIToolHandler

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
    # AG-UI components
    "AGUIClient",
    "AGUIClientError",
    "AGUIHTTPError",
    "AGUIJSONError",
    "AGUIRequestContext",
    "AGUIExecutor",
    "AILFAsAGUIServer",
    "AGUIServerError",
    "SimpleAGUIExecutor",
    "AdvancedAGUIExecutor",
    "AGUIStateManager",
    "AGUIToolHandler",
]
