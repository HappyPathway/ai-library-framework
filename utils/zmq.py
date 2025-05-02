"""ZeroMQ Utilities Module.

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

import zmq
import json
import time
from contextlib import contextmanager
from typing import Optional, Union, Any

from .schemas.zmq import ZMQConfig, SocketType, MessageEnvelope
from .logging import setup_logging
from .monitoring import Metrics

logger = setup_logging(__name__)
metrics = Metrics(__name__)

class ZMQError(Exception):
    """Base exception for ZMQ operations.
    
    This exception wraps ZMQ-specific errors and provides additional context.
    
    :param message: The error message
    :type message: str
    :param original_error: The original exception that caused this error
    :type original_error: Optional[Exception]
    """
    pass

class ZMQSocket:
    """Wrapper for ZMQ socket with context management.
    
    This class provides a high-level interface for ZMQ socket operations with
    automatic resource management, error handling, and metrics collection.
    
    :param config: Socket configuration parameters
    :type config: ZMQConfig
    :param context: ZMQ context to use for socket creation
    :type context: zmq.Context
    :param metrics: Optional metrics collector
    :type metrics: Optional[Metrics]
    
    Example:
        >>> config = ZMQConfig(socket_type=SocketType.PUB, address="tcp://*:5555")
        >>> with ZMQSocket(config, context) as socket:
        ...     socket.send_message("Hello", topic="greetings")
    """
    
    def __init__(self, config: ZMQConfig, context: zmq.Context, metrics: Optional[Metrics] = None):
        """Initialize ZMQ socket wrapper.
        
        :param config: Socket configuration parameters
        :type config: ZMQConfig
        :param context: ZMQ context to use for socket creation
        :type context: zmq.Context
        :param metrics: Optional metrics collector
        :type metrics: Optional[Metrics]
        :raises ZMQError: If socket initialization fails
        """
        self.config = config
        self.context = context
        self.metrics = metrics or Metrics(__name__)
        self.socket = None
        
    def __enter__(self):
        """Configure and return socket."""
        try:
            socket_type = getattr(zmq, self.config.socket_type.value)
            self.socket = self.context.socket(socket_type)
            
            if self.config.receive_timeout:
                self.socket.setsockopt(zmq.RCVTIMEO, self.config.receive_timeout)
            if self.config.send_timeout:
                self.socket.setsockopt(zmq.SNDTIMEO, self.config.send_timeout)
            if self.config.identity:
                self.socket.setsockopt(zmq.IDENTITY, self.config.identity)
                
            try:
                if self.config.bind:
                    self.socket.bind(self.config.address)
                else:
                    self.socket.connect(self.config.address)
            except zmq.ZMQError as e:
                raise ZMQError(f"Failed to {self.config.bind and 'bind' or 'connect'}: {str(e)}")
                
            if self.config.socket_type == SocketType.SUB:
                for topic in (self.config.topics or [""]):
                    self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)
                    
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize ZMQ socket: {str(e)}")
            self.metrics.increment("socket.init.error")
            raise ZMQError(f"Socket initialization failed: {str(e)}") from e

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up socket resources."""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error closing socket: {str(e)}")
                self.metrics.increment("socket.close.error")

    def send_message(
        self, 
        data: Union[str, bytes, dict], 
        topic: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """Send a message through the socket.
        
        Sends data through the socket with optional topic and metadata. The data
        is automatically serialized and wrapped in a MessageEnvelope.
        
        :param data: The message payload to send
        :type data: Union[str, bytes, dict]
        :param topic: Optional topic for pub/sub messaging
        :type topic: Optional[str]
        :param metadata: Optional metadata to include with the message
        :type metadata: Optional[dict]
        :return: True if sent successfully, False otherwise
        :rtype: bool
        :raises ZMQError: If sending fails
        
        Example:
            >>> socket.send_message({"key": "value"}, topic="updates")
            True
            >>> socket.send_message("Hello", metadata={"priority": "high"})
            True
        """
        start_time = time.time()
        try:
            if isinstance(data, dict):
                payload = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                payload = data.encode('utf-8')
            else:
                payload = data
                
            envelope = MessageEnvelope(
                topic=topic,
                payload=payload,
                metadata=metadata or {}
            )
            
            if topic:
                self.socket.send_multipart([
                    topic.encode('utf-8'),
                    envelope.json().encode('utf-8')
                ])
            else:
                self.socket.send(envelope.json().encode('utf-8'))
                
            self.metrics.timing("message.send", time.time() - start_time)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            self.metrics.increment("message.send.error")
            return False

class ZMQManager:
    """Manager for ZMQ operations.
    
    This class manages ZMQ contexts and provides factory methods for creating
    configured sockets. It ensures proper resource cleanup and consistent
    socket configuration.
    
    :param metrics: Optional metrics collector
    :type metrics: Optional[Metrics]
    
    Example:
        >>> with ZMQManager() as zmq:
        ...     with zmq.socket(SocketType.REQ, "tcp://localhost:5555") as sock:
        ...         sock.send_message({"request": "data"})
        ...         response = sock.receive()
    """
    
    def __init__(self, metrics: Optional[Metrics] = None):
        """Initialize ZMQ manager.
        
        :param metrics: Optional metrics collector
        :type metrics: Optional[Metrics]
        """
        self.context = zmq.Context()
        self.metrics = metrics or Metrics(__name__)
        
    def __enter__(self):
        """Return manager instance."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up ZMQ context."""
        self.context.term()
        
    @contextmanager
    def socket(self, socket_type: SocketType, address: str, **kwargs) -> ZMQSocket:
        """Create a configured socket.
        
        Creates and configures a ZMQ socket with the specified type and address.
        Additional configuration can be provided through kwargs.
        
        :param socket_type: Type of socket to create (PUB, SUB, REQ, etc.)
        :type socket_type: SocketType
        :param address: Socket address (e.g., "tcp://localhost:5555")
        :type address: str
        :param kwargs: Additional socket configuration options
        :type kwargs: dict
        :return: Configured socket wrapper
        :rtype: ZMQSocket
        :raises ZMQError: If socket creation or configuration fails
        
        Example:
            >>> with zmq.socket(SocketType.PUB, "tcp://*:5555", bind=True) as pub:
            ...     pub.send_message("Hello", topic="greetings")
        """
        config = ZMQConfig(
            socket_type=socket_type,
            address=address,
            **kwargs
        )
        with ZMQSocket(config, self.context, self.metrics) as socket:
            yield socket
