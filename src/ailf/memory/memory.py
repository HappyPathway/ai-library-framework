"""In-memory implementation of the base Memory interface."""
from typing import Any, Dict, List, Optional

from ailf.memory.base import Memory
from ailf.memory.file_memory import FileLongTermMemory

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


# Alias for backwards compatibility
FileMemory = FileLongTermMemory
