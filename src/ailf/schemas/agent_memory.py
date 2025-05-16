"""Agent memory schemas.

This module defines the data models for the agent memory subsystem, extending the base memory schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from ailf.schemas.memory import MemoryItem, MemoryType


class Interaction(BaseModel):
    """Representation of an agent-user interaction."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    query: str = Field(description="User query or instruction")
    result: Any = Field(description="Result of processing the query")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentFact(BaseModel):
    """A discrete fact that an agent has learned."""
    
    content: str = Field(description="The factual information")
    source: Optional[str] = Field(default=None, description="Source of the fact")
    confidence: float = Field(default=1.0, description="Confidence level (0.0-1.0)")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentMemoryConfig(BaseModel):
    """Configuration for agent memory systems."""
    
    memory_type: str = Field(default="in_memory", description="Type of memory storage to use")
    enable_short_term: bool = Field(default=True, description="Enable short-term memory")
    enable_long_term: bool = Field(default=True, description="Enable long-term memory") 
    max_interactions: int = Field(default=100, description="Maximum number of interactions to store")
    max_facts: int = Field(default=1000, description="Maximum number of facts to store")
    connection_string: Optional[str] = Field(default=None, description="Connection string for external storage")
    file_path: Optional[str] = Field(default=None, description="Path for file-based storage")
