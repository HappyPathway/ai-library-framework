"""In-memory implementations of Memory interfaces."""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, TypeVar
import time
import uuid

from ailf.memory.base import Memory, ShortTermMemory
from ailf.memory.interfaces import AgentMemoryInterface
from ailf.schemas.memory import MemoryItem
from ailf.schemas.agent_memory import Interaction, AgentFact

T = TypeVar('T')

class InMemory(Memory):
    """Simple in-memory implementation of Memory interface."""
    
    def __init__(self):
        """Initialize the memory store."""
        self.items: Dict[str, Any] = {}
    
    async def store(self, item: Any) -> str:
        """Store an item in memory and return its ID."""
        if hasattr(item, 'id'):
            item_id = item.id
        else:
            import uuid
            item_id = str(uuid.uuid4())
            
        self.items[item_id] = item
        return item_id
    
    async def retrieve(self, query: str, **kwargs) -> List[Any]:
        """Retrieve items from memory based on a query."""
        # Simple implementation just returns all items
        # In a real implementation, this would do semantic search
        return list(self.items.values())
    
    async def clear(self) -> None:
        """Clear all items from memory."""
        self.items.clear()


class InMemoryShortTermMemory(ShortTermMemory):
    """In-memory implementation of short-term memory."""

    def __init__(self, max_size: int = 1000):
        """
        Initialize in-memory short-term memory.

        :param max_size: Maximum number of items to store.
        :type max_size: int
        """
        self._memory: Dict[str, MemoryItem] = {}
        self._timestamps: Dict[str, float] = {} # To track item recency
        self.max_size = max_size

    async def add_item(self, item: MemoryItem) -> None:
        """Add an item to short-term memory."""
        if len(self._memory) >= self.max_size:
            # Evict the oldest item if max_size is reached
            oldest_item_id = min(self._timestamps, key=self._timestamps.get)
            del self._memory[oldest_item_id]
            del self._timestamps[oldest_item_id]
        
        self._memory[item.id] = item  # Fix: Use item.id instead of item.item_id
        self._timestamps[item.id] = time.time()

    async def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item from short-term memory by its ID."""
        return self._memory.get(item_id)

    async def get_recent_items(self, count: int) -> List[MemoryItem]:
        """Retrieve a list of the most recent items."""
        if count <= 0:
            return []
        # Sort items by timestamp in descending order (most recent first)
        sorted_item_ids = sorted(self._timestamps, key=self._timestamps.get, reverse=True)
        recent_ids = sorted_item_ids[:count]
        return [self._memory[id] for id in recent_ids if id in self._memory]

    async def clear(self) -> None:
        """Clear all items from short-term memory."""
        self._memory.clear()
        self._timestamps.clear()


class InMemoryAgentMemory(AgentMemoryInterface):
    """Simple in-memory implementation of Agent Memory interface.
    
    This implementation stores all memory components (interactions, facts, working memory)
    in in-memory dictionaries and lists, making it suitable for testing, development,
    and simple applications without persistence requirements.
    """
    
    def __init__(self, max_interactions: int = 1000, max_facts: int = 1000):
        """Initialize the memory store.
        
        Args:
            max_interactions: Maximum number of interactions to store
            max_facts: Maximum number of facts to store
        """
        self.interactions: List[Interaction] = []
        self.facts: List[AgentFact] = []
        self.working_memory: Dict[str, Any] = {}
        self.max_interactions = max_interactions
        self.max_facts = max_facts
    
    async def add_interaction(self, query: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add an interaction to memory.
        
        Args:
            query: User query or instruction
            result: Result of processing the query
            metadata: Additional metadata about the interaction
            
        Returns:
            str: ID of the stored interaction (currently always returns "")
        """
        interaction = Interaction(
            timestamp=datetime.now(),
            query=query,
            result=result,
            metadata=metadata or {}
        )
        
        self.interactions.append(interaction)
        
        # Enforce max size by removing oldest interactions if needed
        while len(self.interactions) > self.max_interactions:
            self.interactions.pop(0)
        
        return str(uuid.uuid4())  # Generate a unique ID for the interaction
    
    async def add_fact(self, fact: str, source: Optional[str] = None, 
                      confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a fact to memory.
        
        Args:
            fact: The fact to remember
            source: Source of the fact
            confidence: Confidence level (0.0-1.0)
            metadata: Additional metadata about the fact
            
        Returns:
            str: ID of the stored fact (empty string in this implementation)
        """
        # Avoid storing duplicate facts
        for existing_fact in self.facts:
            if existing_fact.content.lower() == fact.lower():
                # Update fact's confidence and metadata if needed
                if confidence > existing_fact.confidence:
                    existing_fact.confidence = confidence
                if source and not existing_fact.source:
                    existing_fact.source = source
                if metadata:
                    existing_fact.metadata.update(metadata)
                return ""
        
        agent_fact = AgentFact(
            content=fact,
            source=source,
            confidence=confidence,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.facts.append(agent_fact)
        
        # Enforce max size by removing lowest confidence facts if needed
        while len(self.facts) > self.max_facts:
            # Find and remove fact with lowest confidence
            min_confidence_idx = min(range(len(self.facts)), key=lambda i: self.facts[i].confidence)
            self.facts.pop(min_confidence_idx)
        
        return ""  # In this implementation, facts don't have IDs
    
    async def get_recent_interactions(self, count: int = 5) -> List[Interaction]:
        """Get recent interactions.
        
        Args:
            count: Number of recent interactions to return
            
        Returns:
            List[Interaction]: Recent interactions
        """
        return self.interactions[-count:]
    
    async def get_relevant_facts(self, query: str, count: int = 5) -> List[AgentFact]:
        """Get facts relevant to a query.
        
        Args:
            query: The query to find relevant facts for
            count: Maximum number of facts to return
            
        Returns:
            List[AgentFact]: Relevant facts
            
        Note:
            This simple implementation does basic keyword matching.
            A more sophisticated implementation would use semantic search.
        """
        # Simple relevance scoring by keyword matching
        query_words = set(query.lower().split())
        scored_facts = []
        
        for fact in self.facts:
            # Count matching words
            fact_words = set(fact.content.lower().split())
            match_score = len(query_words.intersection(fact_words))
            # Weight by confidence
            weighted_score = match_score * fact.confidence
            if match_score > 0:
                scored_facts.append((weighted_score, fact))
        
        # Sort by score (highest first) and take top 'count'
        return [fact for _, fact in sorted(scored_facts, reverse=True)[:count]]
    
    async def get_all_facts(self) -> List[AgentFact]:
        """Get all stored facts.
        
        Returns:
            List[AgentFact]: All facts in memory
        """
        return self.facts
    
    async def add_working_memory_item(self, key: str, value: Any) -> None:
        """Add or update a working memory item.
        
        Args:
            key: The key to store the value under
            value: The value to store
        """
        self.working_memory[key] = value
    
    async def get_working_memory_item(self, key: str, default: Optional[T] = None) -> Union[Any, T]:
        """Get a working memory item.
        
        Args:
            key: The key of the item to retrieve
            default: Default value if the key doesn't exist
            
        Returns:
            The stored value or the default
        """
        return self.working_memory.get(key, default)
    
    async def get_working_memory(self) -> Dict[str, Any]:
        """Get all working memory items.
        
        Returns:
            Dict[str, Any]: All working memory items
        """
        return self.working_memory
    
    async def clear_working_memory(self) -> None:
        """Clear all working memory items."""
        self.working_memory.clear()
    
    async def clear(self) -> None:
        """Clear all memory (interactions, facts, and working memory)."""
        self.interactions.clear()
        self.facts.clear()
        self.working_memory.clear()
