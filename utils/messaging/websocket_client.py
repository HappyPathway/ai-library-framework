"""
WebSocket client for real-time bidirectional communication.

This module provides a WebSocket client implementation with support for:
- Automatic reconnection
- Message serialization/deserialization
- Structured message handling
- Asynchronous event-driven architecture

Examples:
    >>> async with WebSocketClient("ws://example.com/ws") as client:
    >>>     await client.connect()
    >>>     await client.send({"type": "message", "content": "Hello"})
    >>>     message = await client.receive()
"""

import asyncio
import json
import logging
import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Type, cast

import websockets
from pydantic import BaseModel
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import (
    ConnectionClosed, ConnectionClosedError, ConnectionClosedOK
)

from schemas.messaging.websockets import (
    WebSocketMessage, StandardMessage, MessageType,
    ConnectMessage, ConnectAckMessage, ErrorMessage
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)
MessageHandler = Callable[[WebSocketMessage], None]


class ConnectionState(Enum):
    """Connection states for the WebSocket client."""
    
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSING = "closing"
    CLOSED = "closed"


class WebSocketError(Exception):
    """Base exception for WebSocket errors."""
    pass


class ConnectionError(WebSocketError):
    """Exception raised for connection errors."""
    pass


class MessageError(WebSocketError):
    """Exception raised for message errors."""
    pass


class WebSocketClient:
    """Client for WebSocket communication.
    
    This client provides methods to connect to a WebSocket server,
    send and receive messages, and handle reconnection.
    """
    
    def __init__(
        self,
        uri: str,
        auto_reconnect: bool = True,
        reconnect_interval: float = 1.0,
        max_reconnect_attempts: int = 5,
        ping_interval: Optional[float] = 30.0,
        ping_timeout: Optional[float] = 10.0,
        extra_headers: Optional[Dict[str, str]] = None,
        connection_timeout: float = 10.0
    ):
        """Initialize the WebSocket client.
        
        Args:
            uri: WebSocket server URI
            auto_reconnect: Whether to automatically reconnect
            reconnect_interval: Time between reconnection attempts
            max_reconnect_attempts: Maximum number of reconnection attempts
            ping_interval: Interval for sending ping messages
            ping_timeout: Timeout for ping responses
            extra_headers: Additional HTTP headers for the connection
            connection_timeout: Timeout for connection attempts
        """
        self.uri = uri
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.extra_headers = extra_headers or {}
        self.connection_timeout = connection_timeout
        
        self._connection: Optional[WebSocketClientProtocol] = None
        self._state = ConnectionState.DISCONNECTED
        self._reconnect_attempts = 0
        self._message_handlers: List[MessageHandler] = []
        self._incoming_queue: asyncio.Queue = asyncio.Queue()
        self._outgoing_queue: asyncio.Queue = asyncio.Queue()
        self._tasks: List[asyncio.Task] = []
        self._session_id: Optional[str] = None
        self._client_id = str(uuid.uuid4())
        self._close_event = asyncio.Event()
    
    @property
    def connected(self) -> bool:
        """Check if the client is connected."""
        return self._state == ConnectionState.CONNECTED and self._connection is not None
    
    @property
    def state(self) -> ConnectionState:
        """Get the current connection state."""
        return self._state
    
    @property
    def session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self._session_id
    
    async def __aenter__(self):
        """Enter async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.disconnect()
    
    async def connect(
        self, 
        auth_token: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> bool:
        """Connect to the WebSocket server.
        
        Args:
            auth_token: Optional authentication token
            timeout: Connection timeout override
            
        Returns:
            bool: True if connected successfully
            
        Raises:
            ConnectionError: If connection fails
        """
        if self._state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
            logger.warning("Already connected or connecting")
            return True
        
        self._state = ConnectionState.CONNECTING
        self._reconnect_attempts = 0
        self._close_event.clear()
        
        try:
            connection_timeout = timeout or self.connection_timeout
            headers = self.extra_headers.copy()
            
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
                
            self._connection = await asyncio.wait_for(
                websockets.connect(
                    self.uri,
                    extra_headers=headers
                ),
                timeout=connection_timeout
            )
            
            # Start worker tasks
            self._tasks = [
                asyncio.create_task(self._receive_loop()),
                asyncio.create_task(self._send_loop()),
                asyncio.create_task(self._handler_loop())
            ]
            
            # Add ping task if ping_interval is set
            if self.ping_interval:
                self._tasks.append(
                    asyncio.create_task(self._ping_loop())
                )
            
            # Send connect message
            connect_msg = ConnectMessage(
                client_id=self._client_id,
                auth_token=auth_token,
                version="1.0",
                id=str(uuid.uuid4())
            )
            
            await self._outgoing_queue.put(connect_msg)
            
            # Wait for connect acknowledgment or timeout
            try:
                response = await asyncio.wait_for(
                    self._wait_for_message_type(MessageType.CONNECT_ACK),
                    timeout=connection_timeout
                )
                
                if isinstance(response, ConnectAckMessage):
                    self._session_id = response.session_id
                    self._state = ConnectionState.CONNECTED
                    logger.info(f"Connected to WebSocket server: {self.uri}")
                    return True
                else:
                    logger.error("Invalid connection acknowledgment")
                    await self.disconnect()
                    raise ConnectionError("Invalid connection acknowledgment")
                    
            except asyncio.TimeoutError:
                logger.error("Connection acknowledgment timeout")
                await self.disconnect()
                raise ConnectionError("Connection acknowledgment timeout")
            
        except asyncio.TimeoutError:
            self._state = ConnectionState.DISCONNECTED
            logger.error(f"Connection timeout: {self.uri}")
            raise ConnectionError(f"Connection timeout: {self.uri}")
            
        except Exception as e:
            self._state = ConnectionState.DISCONNECTED
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self, reason: Optional[str] = None) -> None:
        """Disconnect from the WebSocket server.
        
        Args:
            reason: Optional reason for disconnection
        """
        if self._state in (ConnectionState.DISCONNECTED, ConnectionState.CLOSED):
            return
            
        self._state = ConnectionState.CLOSING
        logger.info(f"Disconnecting from WebSocket server: {self.uri}")
        
        # Try to send disconnect message
        if self._connection and self._connection.open:
            try:
                disconnect_msg = {
                    "type": "disconnect",
                    "id": str(uuid.uuid4()),
                    "timestamp": int(time.time() * 1000),
                }
                if reason:
                    disconnect_msg["reason"] = reason
                    
                await self._connection.send(json.dumps(disconnect_msg))
            except Exception:
                # Ignore errors during disconnect
                pass
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        self._tasks = []
        
        # Close the connection
        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                # Ignore errors during close
                pass
                
        self._connection = None
        self._state = ConnectionState.CLOSED
        self._close_event.set()
        logger.info("Disconnected from WebSocket server")
    
    def add_message_handler(self, handler: MessageHandler) -> None:
        """Add a message handler.
        
        Args:
            handler: Function to handle incoming messages
        """
        self._message_handlers.append(handler)
    
    def remove_message_handler(self, handler: MessageHandler) -> None:
        """Remove a message handler.
        
        Args:
            handler: Handler function to remove
        """
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
    
    async def send(self, message: Union[Dict, WebSocketMessage]) -> None:
        """Send a message to the server.
        
        Args:
            message: Message to send (dict or WebSocketMessage)
            
        Raises:
            ConnectionError: If not connected
        """
        if not self.connected:
            raise ConnectionError("Not connected")
            
        await self._outgoing_queue.put(message)
    
    async def send_message(self, content: Any, topic: Optional[str] = None) -> None:
        """Send a standard message with content.
        
        Args:
            content: Message content
            topic: Optional message topic
            
        Raises:
            ConnectionError: If not connected
        """
        message = StandardMessage(
            id=str(uuid.uuid4()),
            content=content,
            topic=topic,
            timestamp=int(time.time() * 1000)
        )
        await self.send(message)
    
    async def receive(self, timeout: Optional[float] = None) -> WebSocketMessage:
        """Receive a message from the server.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            WebSocketMessage: The received message
            
        Raises:
            asyncio.TimeoutError: If timeout occurs
            ConnectionError: If not connected
        """
        if not self.connected:
            raise ConnectionError("Not connected")
            
        if timeout:
            return await asyncio.wait_for(self._incoming_queue.get(), timeout=timeout)
        else:
            return await self._incoming_queue.get()
    
    async def wait_for_close(self) -> None:
        """Wait until the connection is closed."""
        await self._close_event.wait()
    
    async def _receive_loop(self) -> None:
        """Background task for receiving messages."""
        if not self._connection:
            return
            
        try:
            while True:
                try:
                    data = await self._connection.recv()
                    await self._process_incoming_message(data)
                except ConnectionClosedOK:
                    logger.info("Connection closed normally")
                    break
                except ConnectionClosedError as e:
                    logger.error(f"Connection closed with error: {e}")
                    break
                except ConnectionClosed as e:
                    logger.error(f"Connection closed: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    # Continue trying to receive messages
                    
        except asyncio.CancelledError:
            # Task was cancelled, exit quietly
            pass
        finally:
            await self._handle_connection_lost()
    
    async def _send_loop(self) -> None:
        """Background task for sending messages."""
        if not self._connection:
            return
            
        try:
            while True:
                message = await self._outgoing_queue.get()
                
                try:
                    if isinstance(message, BaseModel):
                        data = message.json()
                    elif isinstance(message, dict):
                        data = json.dumps(message)
                    else:
                        data = str(message)
                        
                    await self._connection.send(data)
                    self._outgoing_queue.task_done()
                except ConnectionClosed:
                    # Put message back in queue for potential reconnection
                    self._outgoing_queue.put_nowait(message)
                    break
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    self._outgoing_queue.task_done()
                    
        except asyncio.CancelledError:
            # Task was cancelled, exit quietly
            pass
    
    async def _handler_loop(self) -> None:
        """Background task for handling messages."""
        try:
            while True:
                message = await self._incoming_queue.get()
                
                for handler in self._message_handlers:
                    try:
                        handler(message)
                    except Exception as e:
                        logger.error(f"Error in message handler: {e}")
                        
                self._incoming_queue.task_done()
                
        except asyncio.CancelledError:
            # Task was cancelled, exit quietly
            pass
    
    async def _ping_loop(self) -> None:
        """Background task for sending ping messages."""
        if not self._connection or not self.ping_interval:
            return
            
        try:
            while True:
                await asyncio.sleep(self.ping_interval)
                
                if not self.connected:
                    break
                    
                try:
                    ping_id = str(uuid.uuid4())
                    ping_data = {"timestamp": int(time.time() * 1000)}
                    
                    await self._connection.ping(json.dumps(ping_data))
                    
                    # Wait for pong
                    if self.ping_timeout:
                        try:
                            await asyncio.wait_for(
                                self._connection.pong(),
                                timeout=self.ping_timeout
                            )
                        except asyncio.TimeoutError:
                            logger.warning("Ping timeout, reconnecting")
                            asyncio.create_task(self._reconnect())
                            break
                            
                except Exception as e:
                    logger.error(f"Error in ping: {e}")
                    break
                    
        except asyncio.CancelledError:
            # Task was cancelled, exit quietly
            pass
    
    async def _process_incoming_message(self, data: Union[str, bytes]) -> None:
        """Process an incoming message.
        
        Args:
            data: Raw message data
        """
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
                
            message_dict = json.loads(data)
            
            # Determine message type
            message_type = message_dict.get("type")
            if not message_type:
                logger.warning("Received message without type")
                return
                
            try:
                # Parse message based on its type
                if message_type == MessageType.ERROR:
                    message = ErrorMessage.parse_obj(message_dict)
                elif message_type == MessageType.CONNECT_ACK:
                    message = ConnectAckMessage.parse_obj(message_dict)
                else:
                    # Default to generic WebSocketMessage
                    message = WebSocketMessage.parse_obj(message_dict)
                    
            except Exception as e:
                logger.error(f"Error parsing message: {e}")
                # Fall back to raw dictionary
                message = WebSocketMessage(
                    type=message_type,
                    id=message_dict.get("id"),
                    timestamp=message_dict.get("timestamp")
                )
                
            # Add message to the incoming queue
            await self._incoming_queue.put(message)
            
        except json.JSONDecodeError:
            logger.error("Received invalid JSON")
        except Exception as e:
            logger.error(f"Error processing incoming message: {e}")
    
    async def _handle_connection_lost(self) -> None:
        """Handle a lost connection."""
        if self._state in (ConnectionState.CLOSING, ConnectionState.CLOSED):
            # Expected closure
            return
            
        self._state = ConnectionState.DISCONNECTED
        
        if self.auto_reconnect and self._reconnect_attempts < self.max_reconnect_attempts:
            await self._reconnect()
        else:
            # Disconnect completely
            await self.disconnect("Connection lost")
    
    async def _reconnect(self) -> None:
        """Attempt to reconnect to the server."""
        if self._state in (ConnectionState.RECONNECTING, ConnectionState.CONNECTING):
            return
            
        self._state = ConnectionState.RECONNECTING
        self._reconnect_attempts += 1
        
        logger.info(f"Attempting reconnection ({self._reconnect_attempts}/{self.max_reconnect_attempts})")
        
        # Cancel all existing tasks except this one
        for task in self._tasks:
            if not task.done():
                task.cancel()
                
        self._tasks = []
        
        # Close existing connection
        if self._connection:
            try:
                await self._connection.close()
            except Exception:
                pass
                
        self._connection = None
        
        # Wait before reconnecting
        await asyncio.sleep(self.reconnect_interval)
        
        try:
            # Attempt to reconnect
            await self.connect()
            self._reconnect_attempts = 0
        except ConnectionError:
            if self._reconnect_attempts >= self.max_reconnect_attempts:
                logger.error("Max reconnection attempts reached")
                await self.disconnect("Max reconnection attempts reached")
            else:
                # Try again later
                asyncio.create_task(self._reconnect())
    
    async def _wait_for_message_type(
        self, 
        message_type: MessageType, 
        timeout: Optional[float] = None
    ) -> WebSocketMessage:
        """Wait for a specific message type.
        
        Args:
            message_type: Type of message to wait for
            timeout: Optional timeout
            
        Returns:
            WebSocketMessage: Received message of the specified type
            
        Raises:
            asyncio.TimeoutError: If timeout occurs
        """
        start_time = time.time()
        while timeout is None or (time.time() - start_time) < timeout:
            # Get message with remaining timeout
            remaining = None
            if timeout is not None:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    raise asyncio.TimeoutError()
                    
            message = await self.receive(timeout=remaining)
            
            if message.type == message_type:
                return message
                
            # Put the message back for regular processing
            self._incoming_queue.put_nowait(message)
            
            # Small delay to avoid CPU spinning
            await asyncio.sleep(0.01)
            
        raise asyncio.TimeoutError()
