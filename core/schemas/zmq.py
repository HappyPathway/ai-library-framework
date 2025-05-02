"""ZMQ Schema Definitions

This module defines the data models and configuration schemas for ZMQ operations.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class SocketType(str, Enum):
    """ZMQ socket types."""
    PUB = "PUB"
    SUB = "SUB"
    REQ = "REQ"
    REP = "REP"
    PUSH = "PUSH"
    PULL = "PULL"

class ZMQConfig(BaseModel):
    """ZMQ connection configuration."""
    socket_type: SocketType
    address: str
    bind: bool = False
    topics: List[str] = Field(default_factory=list)
    receive_timeout: Optional[int] = None
    send_timeout: Optional[int] = None
    identity: Optional[bytes] = None
    
    @validator('address')
    def validate_address(cls, v):
        """Validate ZMQ address format."""
        if not v.startswith(('tcp://', 'ipc://')):
            raise ValueError("Address must start with tcp:// or ipc://")
        return v

class MessageEnvelope(BaseModel):
    """Message envelope for ZMQ communications."""
    topic: Optional[str] = None
    payload: bytes
    metadata: dict = Field(default_factory=dict)
