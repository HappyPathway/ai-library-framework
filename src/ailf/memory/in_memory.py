"""In-memory implementations of Memory interfaces."""
from typing import Any, Dict, List, Optional
import time

from ailf.memory.base import Memory, ShortTermMemory
from ailf.schemas.memory import MemoryItem

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
