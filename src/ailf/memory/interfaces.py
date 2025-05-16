"""Enhanced memory system interfaces for AILF.

This module provides the foundation for all memory systems in the AILF framework,
with a focus on unified interfaces for different memory storage backends.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, TypeVar

from ailf.schemas.memory import MemoryItem
from ailf.schemas.agent_memory import Interaction, AgentFact

T = TypeVar('T')


class AgentMemoryInterface(ABC):
    """Interface for Agent memory systems.
    
    This interface defines the common operations that all agent memory systems
    should implement, regardless of their backend storage mechanism.
    """
    
    @abstractmethod
    async def add_interaction(self, query: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add an interaction to memory.
        
        Args:
            query: User query or instruction
            result: Result of processing the query
            metadata: Additional metadata about the interaction
            
        Returns:
            str: ID of the stored interaction
        """
        pass
    
    @abstractmethod
    async def add_fact(self, fact: str, source: Optional[str] = None, 
                      confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a fact to memory.
        
        Args:
            fact: The fact to remember
            source: Source of the fact
            confidence: Confidence level (0.0-1.0)
            metadata: Additional metadata about the fact
            
        Returns:
            str: ID of the stored fact
        """
        pass
    
    @abstractmethod
    async def get_recent_interactions(self, count: int = 5) -> List[Interaction]:
        """Get recent interactions.
        
        Args:
            count: Number of recent interactions to return
            
        Returns:
            List[Interaction]: Recent interactions
        """
        pass
    
    @abstractmethod
    async def get_relevant_facts(self, query: str, count: int = 5) -> List[AgentFact]:
        """Get facts relevant to a query.
        
        Args:
            query: The query to find relevant facts for
            count: Maximum number of facts to return
            
        Returns:
            List[AgentFact]: Relevant facts
        """
        pass
    
    @abstractmethod
    async def get_all_facts(self) -> List[AgentFact]:
        """Get all stored facts.
        
        Returns:
            List[AgentFact]: All facts in memory
        """
        pass
    
    @abstractmethod
    async def add_working_memory_item(self, key: str, value: Any) -> None:
        """Add or update a working memory item.
        
        Args:
            key: The key to store the value under
            value: The value to store
        """
        pass
    
    @abstractmethod
    async def get_working_memory_item(self, key: str, default: Optional[T] = None) -> Union[Any, T]:
        """Get a working memory item.
        
        Args:
            key: The key of the item to retrieve
            default: Default value if the key doesn't exist
            
        Returns:
            The stored value or the default
        """
        pass
    
    @abstractmethod
    async def get_working_memory(self) -> Dict[str, Any]:
        """Get all working memory items.
        
        Returns:
            Dict[str, Any]: All working memory items
        """
        pass
    
    @abstractmethod
    async def clear_working_memory(self) -> None:
        """Clear all working memory items."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all memory (interactions, facts, and working memory)."""
        pass


class MemoryFactory:
    """Factory for creating memory backends based on configuration."""
    
    @staticmethod
    def create_memory(memory_type: str = "in_memory", **kwargs) -> AgentMemoryInterface:
        """Create a memory backend of the specified type.
        
        Args:
            memory_type: Type of memory backend to create ("in_memory", "redis", "file")
            **kwargs: Additional configuration for the memory backend
            
        Returns:
            AgentMemoryInterface: Configured memory backend
            
        Raises:
            ValueError: If memory_type is not supported
        """
        if memory_type == "in_memory":
            from ailf.memory.in_memory import InMemoryAgentMemory
            return InMemoryAgentMemory(**kwargs)
        elif memory_type == "redis":
            from ailf.memory.redis_memory import RedisAgentMemory
            return RedisAgentMemory(**kwargs)
        elif memory_type == "file":
            from ailf.memory.file_memory import FileAgentMemory
            return FileAgentMemory(**kwargs)
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")
