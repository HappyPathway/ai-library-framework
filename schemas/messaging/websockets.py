"""
WebSocket message schemas for client-server communication.

This module defines Pydantic models for standardized WebSocket message formats,
providing structure, validation, and serialization capabilities.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class MessageType(str, Enum):
    """Types of WebSocket messages."""
    
    # Connection management
    CONNECT = "connect"
    CONNECT_ACK = "connect_ack"
    DISCONNECT = "disconnect"
    
    # Standard messages
    MESSAGE = "message"
    
    # Error messages
    ERROR = "error"
    
    # Special message types
    PING = "ping"
    PONG = "pong"
    
    # Subscription messages (for pub/sub pattern)
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PUBLISH = "publish"
    
    # Room/group messages (for multi-user chat)
    JOIN = "join"
    LEAVE = "leave"


class WebSocketMessage(BaseModel):
    """Base WebSocket message model.
    
    All WebSocket messages should inherit from this base class to ensure
    a consistent message structure across the application.
    """
    
    type: MessageType = Field(..., description="Type of message")
    id: Optional[str] = Field(None, description="Unique message identifier")
    timestamp: Optional[int] = Field(
        None, 
        description="Message timestamp (Unix timestamp in milliseconds)"
    )
    
    class Config:
        """Pydantic model configuration."""
        
        # Allow extra fields for forward compatibility
        extra = "allow"


class ConnectMessage(WebSocketMessage):
    """Message for initiating a connection with parameters."""
    
    type: MessageType = MessageType.CONNECT
    auth_token: Optional[str] = Field(None, description="Authentication token")
    client_id: Optional[str] = Field(None, description="Client identifier")
    version: Optional[str] = Field(None, description="Protocol version")
    user_agent: Optional[str] = Field(None, description="Client user agent")


class ConnectAckMessage(WebSocketMessage):
    """Message acknowledging a successful connection."""
    
    type: MessageType = MessageType.CONNECT_ACK
    session_id: str = Field(..., description="Session identifier")
    server_id: Optional[str] = Field(None, description="Server identifier")
    features: Optional[List[str]] = Field(None, description="Supported features")


class DisconnectMessage(WebSocketMessage):
    """Message for disconnecting from the server."""
    
    type: MessageType = MessageType.DISCONNECT
    reason: Optional[str] = Field(None, description="Reason for disconnection")


class StandardMessage(WebSocketMessage):
    """Regular message containing application data."""
    
    type: MessageType = MessageType.MESSAGE
    topic: Optional[str] = Field(None, description="Message topic or channel")
    content: Any = Field(..., description="Message content")
    content_type: Optional[str] = Field(
        "text/plain", 
        description="MIME type of the content"
    )
    recipient_id: Optional[str] = Field(
        None, 
        description="Intended recipient (for direct messages)"
    )


class ErrorMessage(WebSocketMessage):
    """Error message with details."""
    
    type: MessageType = MessageType.ERROR
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error description")
    details: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional error details"
    )
    original_message_id: Optional[str] = Field(
        None, 
        description="ID of the message that caused the error"
    )


class PingMessage(WebSocketMessage):
    """Ping message to check connection health."""
    
    type: MessageType = MessageType.PING
    data: Optional[str] = Field(None, description="Optional ping data")


class PongMessage(WebSocketMessage):
    """Pong response to a ping message."""
    
    type: MessageType = MessageType.PONG
    data: Optional[str] = Field(None, description="Echo of ping data")


class SubscribeMessage(WebSocketMessage):
    """Message to subscribe to a topic or channel."""
    
    type: MessageType = MessageType.SUBSCRIBE
    topics: List[str] = Field(..., description="Topics to subscribe to")
    
    @validator("topics")
    def topics_not_empty(cls, v):
        """Validate that topics list is not empty."""
        if not v:
            raise ValueError("topics cannot be empty")
        return v


class UnsubscribeMessage(WebSocketMessage):
    """Message to unsubscribe from a topic or channel."""
    
    type: MessageType = MessageType.UNSUBSCRIBE
    topics: List[str] = Field(..., description="Topics to unsubscribe from")
    
    @validator("topics")
    def topics_not_empty(cls, v):
        """Validate that topics list is not empty."""
        if not v:
            raise ValueError("topics cannot be empty")
        return v


class PublishMessage(WebSocketMessage):
    """Message to publish content to a topic."""
    
    type: MessageType = MessageType.PUBLISH
    topic: str = Field(..., description="Topic to publish to")
    content: Any = Field(..., description="Content to publish")
    content_type: Optional[str] = Field(
        "text/plain", 
        description="MIME type of the content"
    )


class JoinMessage(WebSocketMessage):
    """Message to join a room or group."""
    
    type: MessageType = MessageType.JOIN
    room: str = Field(..., description="Room or group to join")


class LeaveMessage(WebSocketMessage):
    """Message to leave a room or group."""
    
    type: MessageType = MessageType.LEAVE
    room: str = Field(..., description="Room or group to leave")
