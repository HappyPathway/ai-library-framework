"""ZeroMQ Utilities Module.

DEPRECATED: This module has been moved to ailf.messaging.zmq.
Please update your imports to: from ailf.messaging.zmq import ZMQManager, ZMQSocket

This module provides a unified interface for ZMQ operations with proper resource
management, error handling, and common messaging patterns.

Key Components:
    ZMQManager: Central manager for ZMQ contexts and socket creation
    ZMQSocket: Context-managed wrapper for ZMQ sockets
    ZMQError: Custom exception type for ZMQ-specific errors

Example:
    >>> from utils.zmq import ZMQManager
    >>> from utils.schemas.zmq import SocketType
    >>> 
    >>> # Publisher example
    >>> with ZMQManager() as zmq:
    ...     with zmq.socket(SocketType.PUB, "tcp://*:5555") as pub:
    ...         pub.send_message("Hello", topic="greetings")
    ...
    >>> # Subscriber example
    >>> with ZMQManager() as zmq:
    ...     with zmq.socket(SocketType.SUB, "tcp://localhost:5555", topics=["greetings"]) as sub:
    ...         message = sub.receive()
    ...         print(message.payload.decode())
    ...         'Hello'

Note:
    All sockets are automatically managed using context managers to ensure proper cleanup.
"""

import warnings

# Add deprecation warning
warnings.warn(
    "The utils.messaging.zmq module is deprecated. Use ailf.messaging.zmq instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all symbols from the new module location
from ailf.messaging.zmq import *
