"""Memory schemas.

This module defines the data models for the memory subsystem.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memory items."""
    
    OBSERVATION = "observation"
    ACTION = "action"
    THOUGHT = "thought"
    DECISION = "decision"
    RESULT = "result"
    ERROR = "error"
    USER_INPUT = "user_input"
    SYSTEM_MESSAGE = "system_message"
    OTHER = "other"


class MemoryItem(BaseModel):
    """Base class for all memory items."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # For backwards compatibility
    type: MemoryType
    content: Any
    created_at: datetime = Field(default_factory=datetime.now)
    importance: float = 0.5  # 0.0 - 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def __str__(self) -> str:
        """Get string representation of the memory item."""
        return f"{self.type}: {self.content}"


class Observation(MemoryItem):
    """Memory item for observations."""
    
    type: MemoryType = MemoryType.OBSERVATION


class Action(MemoryItem):
    """Memory item for actions."""
    
    type: MemoryType = MemoryType.ACTION
    result: Optional[Any] = None


class Thought(MemoryItem):
    """Memory item for thoughts."""
    
    type: MemoryType = MemoryType.THOUGHT


class MemoryResponse(BaseModel):
    """Response from a memory query."""
    
    items: List[MemoryItem] = Field(default_factory=list)
    query: Optional[str] = None
    total_items: int = 0


class KnowledgeFact(MemoryItem):
    """Knowledge fact stored in memory."""
    
    type: MemoryType = MemoryType.OTHER
    source: Optional[str] = None
    confidence: float = 1.0


class UserProfile(BaseModel):
    """User profile information."""
    
    user_id: str
    preferences: Dict[str, Any] = Field(default_factory=dict)
    history: List[MemoryItem] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
