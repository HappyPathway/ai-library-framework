"""ZeroMQ Core Module

This module provides a unified interface for ZMQ operations with proper resource
management, error handling, and common messaging patterns.

Example:
    ```python
    from core.zmq import ZMQManager
    from core.schemas.zmq import SocketType
    
    # Publisher example
    with ZMQManager() as zmq:
        with zmq.socket(SocketType.PUB, "tcp://*:5555") as pub:
            pub.send_message("Hello", topic="greetings")
    ```
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
    """Base exception for ZMQ operations."""
    pass

class ZMQSocket:
    """Wrapper for ZMQ socket with context management."""
    
    def __init__(self, config: ZMQConfig, context: zmq.Context, metrics: Optional[Metrics] = None):
        """Initialize ZMQ socket wrapper.
        
        Args:
            config: Socket configuration
            context: ZMQ context
            metrics: Optional metrics collector
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
            
            # Apply configuration
            if self.config.receive_timeout:
                self.socket.setsockopt(zmq.RCVTIMEO, self.config.receive_timeout)
            if self.config.send_timeout:
                self.socket.setsockopt(zmq.SNDTIMEO, self.config.send_timeout)
            if self.config.identity:
                self.socket.setsockopt(zmq.IDENTITY, self.config.identity)
                
            # Connect or bind
            try:
                if self.config.bind:
                    self.socket.bind(self.config.address)
                else:
                    self.socket.connect(self.config.address)
            except zmq.ZMQError as e:
                raise ZMQError(f"Failed to {self.config.bind and 'bind' or 'connect'}: {str(e)}")
                
            # Subscribe to topics for SUB sockets
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
        
        Args:
            data: Message payload
            topic: Optional message topic
            metadata: Optional message metadata
            
        Returns:
            bool: True if sent successfully
        """
        start_time = time.time()
        try:
            # Prepare message
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
            
            # Send message
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
    """Manager for ZMQ operations."""
    
    def __init__(self, metrics: Optional[Metrics] = None):
        """Initialize ZMQ manager.
        
        Args:
            metrics: Optional metrics collector
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
        
        Args:
            socket_type: Type of socket to create
            address: Socket address
            **kwargs: Additional configuration options
            
        Returns:
            ZMQSocket: Configured socket wrapper
        """
        config = ZMQConfig(
            socket_type=socket_type,
            address=address,
            **kwargs
        )
        with ZMQSocket(config, self.context, self.metrics) as socket:
            yield socket
