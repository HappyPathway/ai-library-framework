"""ZeroMQ Utilities Module.

This module provides a unified interface for ZMQ operations with proper resource
management, error handling, and common messaging patterns.

Key Components:
    ZMQBase: Base class for all ZMQ communication classes
    ZMQPublisher: Implementation of the publisher pattern
    ZMQSubscriber: Implementation of the subscriber pattern
    ZMQClient: Implementation of the request-reply client pattern
    ZMQServer: Implementation of the request-reply server pattern

Example:
    >>> from ailf.messaging.zmq import ZMQPublisher, ZMQSubscriber
    >>> 
    >>> # Publisher example
    >>> pub = ZMQPublisher()
    >>> pub.connect("tcp://*:5555")
    >>> pub.publish("topic", "Hello World")
    >>> 
    >>> # Subscriber example
    >>> sub = ZMQSubscriber(["topic"])
    >>> sub.connect("tcp://localhost:5555")
    >>> topic, message = sub.receive()
    >>> print(message)
    >>> 'Hello World'

Note:
    All sockets should be properly closed after use with the close() method.
"""

import atexit
import json
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union

import zmq

from ailf.core.logging import setup_logging

# Initialize logging
logger = setup_logging(__name__)


class ZMQBase:
    """Base class for all ZMQ communication classes."""
    
    def __init__(self):
        """Initialize the base ZMQ class."""
        self.context = zmq.Context.instance()
        self.socket = None
        self.socket_type = None
        self._connected = False
        
    def connect(self, address: str) -> None:
        """Connect the socket to an address.
        
        Args:
            address: Address to connect to
        """
        if self.socket is None:
            raise RuntimeError("Socket not initialized")
            
        try:
            if address.startswith("tcp://*"):
                # For TCP addresses with wildcard, we need to bind
                self.socket.bind(address)
            else:
                # For all other addresses, we connect
                self.socket.connect(address)
            self._connected = True
            logger.debug(f"Connected to {address}")
        except zmq.ZMQError as e:
            logger.error(f"Failed to connect to {address}: {str(e)}")
            raise
        
    def close(self) -> None:
        """Close the socket and clean up resources."""
        if self.socket:
            self.socket.close()
            self.socket = None
            self._connected = False
            
    def __del__(self):
        """Clean up resources when the object is garbage collected."""
        self.close()
        
        
class ZMQPublisher(ZMQBase):
    """Publisher implementation for the ZMQ PUB-SUB pattern."""
    
    def __init__(self):
        """Initialize the publisher."""
        super().__init__()
        self.socket_type = zmq.PUB
        self.socket = self.context.socket(self.socket_type)
        
    def publish(self, topic: str, message: Union[str, bytes, dict]) -> None:
        """Publish a message with the given topic.
        
        Args:
            topic: Message topic
            message: Message payload (string, bytes, or dict)
        """
        if not self._connected:
            raise RuntimeError("Not connected to an address")
            
        # Encode the topic as bytes
        topic_bytes = topic.encode('utf-8') if isinstance(topic, str) else topic
        
        # Encode the message based on its type
        if isinstance(message, dict):
            message_bytes = json.dumps(message).encode('utf-8')
        elif isinstance(message, str):
            message_bytes = message.encode('utf-8')
        else:
            # Assume it's already bytes
            message_bytes = message
            
        self.socket.send_multipart([topic_bytes, message_bytes])


class ZMQSubscriber(ZMQBase):
    """Subscriber implementation for the ZMQ PUB-SUB pattern."""
    
    def __init__(self, topics: Optional[List[str]] = None):
        """Initialize the subscriber with optional topic filters.
        
        Args:
            topics: List of topics to subscribe to
        """
        super().__init__()
        self.socket_type = zmq.SUB
        self.socket = self.context.socket(self.socket_type)
        
        # Subscribe to topics
        if topics:
            for topic in topics:
                self.subscribe(topic)
        else:
            # Subscribe to all messages
            self.socket.setsockopt(zmq.SUBSCRIBE, b'')
            
    def subscribe(self, topic: str) -> None:
        """Subscribe to a topic.
        
        Args:
            topic: Topic to subscribe to
        """
        topic_bytes = topic.encode('utf-8') if isinstance(topic, str) else topic
        self.socket.setsockopt(zmq.SUBSCRIBE, topic_bytes)
        
    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from a topic.
        
        Args:
            topic: Topic to unsubscribe from
        """
        topic_bytes = topic.encode('utf-8') if isinstance(topic, str) else topic
        self.socket.setsockopt(zmq.UNSUBSCRIBE, topic_bytes)
        
    def receive(self, timeout: int = None) -> Tuple[bytes, bytes]:
        """Receive a message from the socket.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            Tuple of (topic, message)
        """
        if not self._connected:
            raise RuntimeError("Not connected to an address")
            
        if timeout is not None:
            # Use a poller to implement timeout
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)
            if poller.poll(timeout):
                return self.socket.recv_multipart()
            else:
                raise zmq.ZMQError("Timeout waiting for message")
        else:
            return self.socket.recv_multipart()
            
    def receive_string(self, timeout: int = None) -> Tuple[str, str]:
        """Receive a message and decode as string.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            Tuple of (topic, message) as strings
        """
        topic, message = self.receive(timeout)
        return topic.decode('utf-8'), message.decode('utf-8')
        
    def receive_json(self, timeout: int = None) -> Tuple[str, Dict[str, Any]]:
        """Receive a message and decode as JSON.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            Tuple of (topic, message) with message decoded from JSON
        """
        topic, message = self.receive(timeout)
        return topic.decode('utf-8'), json.loads(message.decode('utf-8'))


class ZMQClient(ZMQBase):
    """Client implementation for the ZMQ REQ-REP pattern."""
    
    def __init__(self):
        """Initialize the client."""
        super().__init__()
        self.socket_type = zmq.REQ
        self.socket = self.context.socket(self.socket_type)
        
    def send_request(self, request: Union[str, bytes, dict], timeout: int = None) -> bytes:
        """Send a request and wait for a response.
        
        Args:
            request: Request message
            timeout: Timeout in milliseconds
            
        Returns:
            Response message
        """
        if not self._connected:
            raise RuntimeError("Not connected to an address")
            
        # Encode the request based on its type
        if isinstance(request, dict):
            request_bytes = json.dumps(request).encode('utf-8')
        elif isinstance(request, str):
            request_bytes = request.encode('utf-8')
        else:
            # Assume it's already bytes
            request_bytes = request
            
        # Send the request
        self.socket.send(request_bytes)
        
        if timeout is not None:
            # Use a poller to implement timeout
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)
            if poller.poll(timeout):
                return self.socket.recv()
            else:
                raise zmq.ZMQError("Timeout waiting for response")
        else:
            return self.socket.recv()
            
    def send_request_string(self, request: str, timeout: int = None) -> str:
        """Send a string request and receive a string response.
        
        Args:
            request: Request string
            timeout: Timeout in milliseconds
            
        Returns:
            Response string
        """
        response = self.send_request(request, timeout)
        return response.decode('utf-8')
        
    def send_request_json(self, request: Dict[str, Any], timeout: int = None) -> Dict[str, Any]:
        """Send a JSON request and receive a JSON response.
        
        Args:
            request: Request dictionary
            timeout: Timeout in milliseconds
            
        Returns:
            Response dictionary
        """
        response = self.send_request(request, timeout)
        return json.loads(response.decode('utf-8'))


class ZMQServer(ZMQBase):
    """Server implementation for the ZMQ REQ-REP pattern."""
    
    def __init__(self):
        """Initialize the server."""
        super().__init__()
        self.socket_type = zmq.REP
        self.socket = self.context.socket(self.socket_type)
        self._running = False
        self._thread = None
        
    def receive(self, timeout: int = None) -> bytes:
        """Receive a request.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            Request message
        """
        if not self._connected:
            raise RuntimeError("Not connected to an address")
            
        if timeout is not None:
            # Use a poller to implement timeout
            poller = zmq.Poller()
            poller.register(self.socket, zmq.POLLIN)
            if poller.poll(timeout):
                return self.socket.recv()
            else:
                raise zmq.ZMQError("Timeout waiting for request")
        else:
            return self.socket.recv()
            
    def receive_string(self, timeout: int = None) -> str:
        """Receive a request and decode as string.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            Request string
        """
        request = self.receive(timeout)
        return request.decode('utf-8')
        
    def receive_json(self, timeout: int = None) -> Dict[str, Any]:
        """Receive a request and decode as JSON.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            Request dictionary
        """
        request = self.receive(timeout)
        return json.loads(request.decode('utf-8'))
            
    def send_response(self, response: Union[str, bytes, dict]) -> None:
        """Send a response to a client.
        
        Args:
            response: Response message
        """
        if not self._connected:
            raise RuntimeError("Not connected to an address")
            
        # Encode the response based on its type
        if isinstance(response, dict):
            response_bytes = json.dumps(response).encode('utf-8')
        elif isinstance(response, str):
            response_bytes = response.encode('utf-8')
        else:
            # Assume it's already bytes
            response_bytes = response
            
        # Send the response
        self.socket.send(response_bytes)
        
    def start(self, handler: callable, daemon: bool = True) -> None:
        """Start the server in a background thread.
        
        Args:
            handler: Function to handle requests, takes bytes and returns bytes
            daemon: Whether the thread should be a daemon
        """
        if self._running:
            return
            
        def _server_loop():
            while self._running:
                try:
                    request = self.receive(timeout=1000)
                    response = handler(request)
                    self.send_response(response)
                except zmq.ZMQError as e:
                    if e.errno != zmq.EAGAIN:  # Timeout
                        logger.error(f"ZMQ error: {str(e)}")
                except Exception as e:
                    logger.error(f"Handler error: {str(e)}")
        
        self._running = True
        self._thread = threading.Thread(target=_server_loop, daemon=daemon)
        self._thread.start()
        
    def stop(self, timeout: float = 1.0) -> None:
        """Stop the server thread.
        
        Args:
            timeout: Join timeout in seconds
        """
        if not self._running or self._thread is None:
            return
            
        self._running = False
        self._thread.join(timeout)
        self._thread = None


# Define exports
__all__ = [
    'ZMQBase',
    'ZMQPublisher',
    'ZMQSubscriber',
    'ZMQClient',
    'ZMQServer'
]
