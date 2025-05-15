"""WebSocket schemas for messaging.

This module contains schema definitions for the WebSocket messaging system.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Enumeration of message types."""
    
    CONNECT = "connect"
    CONNECT_ACK = "connect_ack"
    DISCONNECT = "disconnect"
    STANDARD = "standard"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """Base class for all WebSocket messages."""
    
    type: MessageType
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        """Pydantic model configuration."""
        
        extra = "allow"


class ConnectMessage(WebSocketMessage):
    """Message sent by clients to initiate a WebSocket connection."""
    
    type: MessageType = MessageType.CONNECT
    client_id: Optional[str] = None
    auth_token: Optional[str] = None
    user_agent: Optional[str] = None
    
    
class ConnectAckMessage(WebSocketMessage):
    """Message sent by server to acknowledge a connection."""
    
    type: MessageType = MessageType.CONNECT_ACK
    server_id: str
    client_id: str
    session_id: str
    

class DisconnectMessage(WebSocketMessage):
    """Message sent to indicate a disconnection."""
    
    type: MessageType = MessageType.DISCONNECT
    reason: Optional[str] = None
    code: int = 1000
    

class StandardMessage(WebSocketMessage):
    """Standard message for regular communication."""
    
    type: MessageType = MessageType.STANDARD
    payload: Dict[str, Any]
    

class ErrorMessage(WebSocketMessage):
    """Error message indicating a problem."""
    
    type: MessageType = MessageType.ERROR
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
