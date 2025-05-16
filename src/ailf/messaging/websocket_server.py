"""
WebSocket server implementation for real-time communication.

This module provides a WebSocket server with support for:
- Client connection management
- Message broadcasting
- Room-based grouping
- Authentication integration
- Customizable message handling

Examples:
    >>> server = WebSocketServer(host="0.0.0.0", port=8765)
    >>> server.on_message = my_message_handler
    >>> await server.start()
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set, Union, cast

import websockets
from pydantic import BaseModel, ValidationError
from websockets.asyncio.server import ServerConnection as WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

from ailf.schemas.websockets import (
    WebSocketMessage, ConnectMessage, ConnectAckMessage, 
    DisconnectMessage, StandardMessage, ErrorMessage,
    MessageType
)

logger = logging.getLogger(__name__)

# Type definitions for handlers
ClientConnectHandler = Callable[[WebSocketServerProtocol, ConnectMessage], Awaitable[bool]]
ClientDisconnectHandler = Callable[[WebSocketServerProtocol, Optional[DisconnectMessage]], Awaitable[None]]
MessageHandler = Callable[[WebSocketServerProtocol, WebSocketMessage], Awaitable[None]]
ErrorHandler = Callable[[WebSocketServerProtocol, Exception, Optional[dict]], Awaitable[None]]
AuthHandler = Callable[[ConnectMessage], Awaitable[bool]]


class Client:
    """Representation of a connected WebSocket client."""
    
    def __init__(
        self, 
        websocket: WebSocketServerProtocol, 
        client_id: str,
        session_id: str
    ):
        """Initialize client information.
        
        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
            session_id: Session identifier for this connection
        """
        self.websocket = websocket
        self.client_id = client_id
        self.session_id = session_id
        self.rooms: Set[str] = set()
        self.subscriptions: Set[str] = set()
        self.user_id: Optional[str] = None
        self.authenticated = False
        self.connected_at = time.time()
        self.last_activity = time.time()
        self.metadata: Dict[str, Any] = {}


class WebSocketServer:
    """Server for WebSocket communication.
    
    This server handles WebSocket connections, dispatches messages,
    and provides utilities for broadcasting and room management.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        ping_interval: Optional[float] = 30.0,
        ping_timeout: Optional[float] = 10.0,
        max_message_size: int = 1024 * 1024,  # 1MB
        max_clients: Optional[int] = None,
        server_id: Optional[str] = None
    ):
        """Initialize the WebSocket server.
        
        Args:
            host: Host address to bind
            port: Port number to use
            ping_interval: Interval for ping checks
            ping_timeout: Timeout for ping responses
            max_message_size: Maximum message size in bytes
            max_clients: Maximum number of concurrent clients
            server_id: Server identifier
        """
        self.host = host
        self.port = port
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.max_message_size = max_message_size
        self.max_clients = max_clients
        self.server_id = server_id or str(uuid.uuid4())
        
        # Client tracking
        self.clients: Dict[str, Client] = {}
        self.rooms: Dict[str, Set[str]] = {}
        
        # Handlers with default implementations
        self.on_connect: ClientConnectHandler = self._default_connect_handler
        self.on_disconnect: ClientDisconnectHandler = self._default_disconnect_handler
        self.on_message: MessageHandler = self._default_message_handler
        self.on_error: ErrorHandler = self._default_error_handler
        self.on_auth: Optional[AuthHandler] = None
        
        # Server state
        self._server: Optional[websockets.WebSocketServer] = None
        self._tasks: List[asyncio.Task] = []
        self._stop_event = asyncio.Event()
    
    async def start(self) -> None:
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            max_size=self.max_message_size
        )
        
        # Start maintenance task
        self._tasks.append(asyncio.create_task(self._maintenance_loop()))
        
        logger.info(f"WebSocket server started (server_id: {self.server_id})")
    
    async def stop(self) -> None:
        """Stop the WebSocket server gracefully."""
        logger.info("Stopping WebSocket server...")
        
        # Stop accepting new connections
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        # Set stop event
        self._stop_event.set()
        
        # Cancel maintenance task
        for task in self._tasks:
            task.cancel()
        
        # Close all client connections
        for client_id, client in list(self.clients.items()):
            try:
                await self._disconnect_client(
                    client.websocket, 
                    DisconnectMessage(reason="Server shutting down")
                )
            except Exception as e:
                logger.error(f"Error disconnecting client {client_id}: {e}")
        
        logger.info("WebSocket server stopped")
    
    async def broadcast(
        self,
        message: Union[Dict, WebSocketMessage],
        exclude: Optional[List[str]] = None
    ) -> None:
        """Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast
            exclude: Optional list of client IDs to exclude
        """
        exclude_set = set(exclude) if exclude else set()
        
        for client_id, client in list(self.clients.items()):
            if client_id in exclude_set:
                continue
                
            try:
                await self._send_message_to_client(client.websocket, message)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
    
    async def send_to_client(
        self,
        client_id: str,
        message: Union[Dict, WebSocketMessage]
    ) -> bool:
        """Send a message to a specific client.
        
        Args:
            client_id: Target client ID
            message: Message to send
            
        Returns:
            bool: True if sent successfully
        """
        client = self.clients.get(client_id)
        if not client:
            return False
            
        try:
            await self._send_message_to_client(client.websocket, message)
            return True
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {e}")
            return False
    
    async def broadcast_to_room(
        self,
        room: str,
        message: Union[Dict, WebSocketMessage],
        exclude: Optional[List[str]] = None
    ) -> None:
        """Broadcast a message to all clients in a room.
        
        Args:
            room: Room name
            message: Message to broadcast
            exclude: Optional list of client IDs to exclude
        """
        if room not in self.rooms:
            return
            
        exclude_set = set(exclude) if exclude else set()
        
        for client_id in list(self.rooms[room]):
            if client_id in exclude_set:
                continue
                
            client = self.clients.get(client_id)
            if client:
                try:
                    await self._send_message_to_client(client.websocket, message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id} in room {room}: {e}")
    
    def add_to_room(self, client_id: str, room: str) -> bool:
        """Add a client to a room.
        
        Args:
            client_id: Client ID
            room: Room name
            
        Returns:
            bool: True if added successfully
        """
        client = self.clients.get(client_id)
        if not client:
            return False
            
        if room not in self.rooms:
            self.rooms[room] = set()
            
        self.rooms[room].add(client_id)
        client.rooms.add(room)
        return True
    
    def remove_from_room(self, client_id: str, room: str) -> bool:
        """Remove a client from a room.
        
        Args:
            client_id: Client ID
            room: Room name
            
        Returns:
            bool: True if removed successfully
        """
        client = self.clients.get(client_id)
        if not client:
            return False
            
        if room in self.rooms and client_id in self.rooms[room]:
            self.rooms[room].remove(client_id)
            client.rooms.remove(room)
            
            # Clean up empty room
            if not self.rooms[room]:
                del self.rooms[room]
                
            return True
            
        return False
    
    def get_room_clients(self, room: str) -> List[str]:
        """Get all client IDs in a room.
        
        Args:
            room: Room name
            
        Returns:
            List[str]: List of client IDs
        """
        if room not in self.rooms:
            return []
            
        return list(self.rooms[room])
    
    def get_client_rooms(self, client_id: str) -> List[str]:
        """Get all rooms a client is in.
        
        Args:
            client_id: Client ID
            
        Returns:
            List[str]: List of room names
        """
        client = self.clients.get(client_id)
        if not client:
            return []
            
        return list(client.rooms)
    
    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """Handle a client connection.
        
        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        client_id = None
        try:
            # Check max clients limit
            if self.max_clients is not None and len(self.clients) >= self.max_clients:
                logger.warning("Max clients limit reached, rejecting connection")
                await websocket.close(1008, "Server is at capacity")
                return
                
            # Perform initial handshake - wait for connect message
            connect_message = await self._receive_connect_message(websocket)
            if not connect_message:
                await websocket.close(1002, "Invalid connect message")
                return
                
            # Use client_id from message or generate a new one
            client_id = connect_message.client_id or str(uuid.uuid4())
            
            # Check authentication if handler exists
            if self.on_auth:
                if not await self.on_auth(connect_message):
                    logger.warning(f"Authentication failed for client {client_id}")
                    await websocket.close(1008, "Authentication failed")
                    return
            
            # Call custom connect handler
            if not await self.on_connect(websocket, connect_message):
                logger.info(f"Connection rejected for client {client_id}")
                await websocket.close(1006, "Connection rejected")
                return
                
            # Create session ID
            session_id = str(uuid.uuid4())
            
            # Register client
            client = Client(websocket, client_id, session_id)
            self.clients[client_id] = client
            
            # Send connect acknowledgment
            ack_message = ConnectAckMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                server_id=self.server_id
            )
            await self._send_message_to_client(websocket, ack_message)
            
            logger.info(f"Client connected: {client_id} (session: {session_id})")
            
            # Handle messages
            await self._handle_client_messages(websocket, client_id)
                
        except ConnectionClosed as e:
            logger.info(f"Client connection closed: {e}")
        except Exception as e:
            logger.error(f"Error handling client: {e}", exc_info=True)
            try:
                await websocket.close(1011, "Internal server error")
            except Exception:
                pass
        finally:
            # Ensure cleanup happens
            if client_id in self.clients:
                await self._disconnect_client(websocket, None)
    
    async def _receive_connect_message(
        self, 
        websocket: WebSocketServerProtocol
    ) -> Optional[ConnectMessage]:
        """Wait for and validate a connect message.
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            Optional[ConnectMessage]: Parsed connect message or None if invalid
        """
        try:
            # Wait for initial message
            raw_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            
            # Parse message
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode('utf-8')
                
            message_dict = json.loads(raw_message)
            
            # Check if it's a connect message
            if message_dict.get("type") != MessageType.CONNECT:
                logger.warning("First message is not a connect message")
                return None
                
            # Parse connect message
            try:
                return ConnectMessage.parse_obj(message_dict)
            except ValidationError as e:
                logger.error(f"Invalid connect message: {e}")
                return None
                
        except asyncio.TimeoutError:
            logger.warning("Connect message timeout")
            return None
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in connect message")
            return None
        except Exception as e:
            logger.error(f"Error receiving connect message: {e}")
            return None
    
    async def _handle_client_messages(
        self,
        websocket: WebSocketServerProtocol,
        client_id: str
    ) -> None:
        """Handle messages from a connected client.
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        while client_id in self.clients:
            try:
                raw_message = await websocket.recv()
                
                # Update activity timestamp
                client = self.clients.get(client_id)
                if client:
                    client.last_activity = time.time()
                
                # Parse message
                try:
                    if isinstance(raw_message, bytes):
                        raw_message = raw_message.decode('utf-8')
                        
                    message_dict = json.loads(raw_message)
                    
                    # Handle disconnect message
                    if message_dict.get("type") == MessageType.DISCONNECT:
                        disconnect_message = DisconnectMessage.parse_obj(message_dict)
                        await self._disconnect_client(websocket, disconnect_message)
                        break
                        
                    # Parse message based on type
                    message_type = message_dict.get("type")
                    message: WebSocketMessage
                    
                    if message_type == MessageType.MESSAGE:
                        message = StandardMessage.parse_obj(message_dict)
                    else:
                        message = WebSocketMessage.parse_obj(message_dict)
                        
                    # Call message handler
                    await self.on_message(websocket, message)
                    
                except ValidationError as e:
                    logger.warning(f"Invalid message format: {e}")
                    # Send error response
                    error_message = ErrorMessage(
                        id=str(uuid.uuid4()),
                        code="invalid_format",
                        message="Invalid message format",
                        details={"errors": str(e)}
                    )
                    await self._send_message_to_client(websocket, error_message)
                    
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in message")
                    # Send error response
                    error_message = ErrorMessage(
                        id=str(uuid.uuid4()),
                        code="invalid_json",
                        message="Invalid JSON format"
                    )
                    await self._send_message_to_client(websocket, error_message)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self.on_error(websocket, e, None)
                    
            except ConnectionClosed:
                break
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                try:
                    await self.on_error(websocket, e, None)
                except Exception:
                    pass
    
    async def _disconnect_client(
        self, 
        websocket: WebSocketServerProtocol,
        disconnect_message: Optional[DisconnectMessage]
    ) -> None:
        """Disconnect and clean up a client.
        
        Args:
            websocket: WebSocket connection
            disconnect_message: Optional disconnect message
        """
        # Find client by websocket
        client_id = None
        for cid, client in list(self.clients.items()):
            if client.websocket == websocket:
                client_id = cid
                break
                
        if client_id:
            # Get client before removal
            client = self.clients.get(client_id)
            
            # Remove from rooms
            if client:
                for room in list(client.rooms):
                    self.remove_from_room(client_id, room)
            
            # Remove client
            self.clients.pop(client_id, None)
            
            # Call disconnect handler
            await self.on_disconnect(websocket, disconnect_message)
            
            logger.info(f"Client disconnected: {client_id}")
    
    async def _maintenance_loop(self) -> None:
        """Background task for server maintenance."""
        try:
            while not self._stop_event.is_set():
                # Wait with timeout to allow clean cancellation
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=60.0  # Run maintenance every minute
                    )
                    break
                except asyncio.TimeoutError:
                    pass
                
                # Run maintenance tasks
                await self._check_dead_connections()
                self._clean_empty_rooms()
                
        except asyncio.CancelledError:
            # Task was cancelled
            pass
        except Exception as e:
            logger.error(f"Error in maintenance loop: {e}")
    
    async def _check_dead_connections(self) -> None:
        """Check and remove dead connections."""
        if not self.ping_timeout:
            return
            
        now = time.time()
        max_inactivity = self.ping_interval + self.ping_timeout + 30.0 if self.ping_interval else 120.0
        
        for client_id, client in list(self.clients.items()):
            if now - client.last_activity > max_inactivity:
                logger.warning(f"Client {client_id} connection timed out")
                try:
                    await self._disconnect_client(
                        client.websocket,
                        DisconnectMessage(reason="Connection timeout")
                    )
                except Exception as e:
                    logger.error(f"Error disconnecting timed-out client {client_id}: {e}")
    
    def _clean_empty_rooms(self) -> None:
        """Remove empty rooms."""
        empty_rooms = [room for room, clients in self.rooms.items() if not clients]
        for room in empty_rooms:
            del self.rooms[room]
    
    async def _send_message_to_client(
        self,
        websocket: WebSocketServerProtocol,
        message: Union[Dict, WebSocketMessage]
    ) -> None:
        """Send a message to a client.
        
        Args:
            websocket: WebSocket connection
            message: Message to send
        """
        try:
            if isinstance(message, BaseModel):
                data = message.json()
            elif isinstance(message, dict):
                data = json.dumps(message)
            else:
                data = str(message)
                
            await websocket.send(data)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def _default_connect_handler(
        self,
        websocket: WebSocketServerProtocol,
        message: ConnectMessage
    ) -> bool:
        """Default handler for client connection.
        
        Args:
            websocket: WebSocket connection
            message: Connect message
            
        Returns:
            bool: True to accept the connection
        """
        # Default implementation accepts all connections
        return True
    
    async def _default_disconnect_handler(
        self,
        websocket: WebSocketServerProtocol,
        message: Optional[DisconnectMessage]
    ) -> None:
        """Default handler for client disconnection.
        
        Args:
            websocket: WebSocket connection
            message: Optional disconnect message
        """
        # Default implementation does nothing
        pass
    
    async def _default_message_handler(
        self,
        websocket: WebSocketServerProtocol,
        message: WebSocketMessage
    ) -> None:
        """Default handler for client messages.
        
        Args:
            websocket: WebSocket connection
            message: Received message
        """
        # Default implementation logs message type
        logger.debug(f"Received message type: {message.type}")
    
    async def _default_error_handler(
        self,
        websocket: WebSocketServerProtocol,
        error: Exception,
        message: Optional[dict]
    ) -> None:
        """Default handler for errors.
        
        Args:
            websocket: WebSocket connection
            error: The exception that occurred
            message: Original message that caused the error, if available
        """
        # Default implementation sends error message to client
        try:
            error_message = ErrorMessage(
                id=str(uuid.uuid4()),
                code="internal_error",
                message="Internal server error"
            )
            await self._send_message_to_client(websocket, error_message)
        except Exception:
            # Ignore errors in error handling
            pass
