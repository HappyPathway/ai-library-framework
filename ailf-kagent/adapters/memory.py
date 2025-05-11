"""
Memory bridge for integrating AILF memory systems with Kagent.

This module provides adapter classes that allow Kagent agents to use AILF's
memory systems for state management and persistence.
"""

from typing import Any, Dict, List, Optional, Union
import json

# Import Kagent components
# Note: These imports may need adjustment based on actual Kagent structure
from kagent.memory.base import BaseMemory

# Import AILF components
# Note: These imports may need to be adjusted based on actual AILF structure
# Assuming AILF has a MemoryManager class in ailf.memory module
from ailf.memory import MemoryManager as AILFMemory


class AILFMemoryBridge(BaseMemory):
    """Bridge between Kagent memory and AILF memory systems.
    
    This adapter allows Kagent agents to use AILF's memory systems for
    storing and retrieving data, enabling seamless memory sharing between
    frameworks.
    
    Attributes:
        ailf_memory: The AILF memory manager instance
        namespace: The namespace used for memory segregation
    """
    
    def __init__(self, namespace: str = "default"):
        """Initialize the AILF memory bridge.
        
        Args:
            namespace: The namespace to use for memory segregation
        """
        self.ailf_memory = AILFMemory(namespace=namespace)
        self.namespace = namespace
    
    async def get(self, key: str) -> Any:
        """Get a value from AILF memory.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The stored value, or None if not found
        """
        return await self.ailf_memory.get(key)
    
    async def set(self, key: str, value: Any) -> None:
        """Set a value in AILF memory.
        
        Args:
            key: The key to store the value under
            value: The value to store
        """
        await self.ailf_memory.set(key, value)
    
    async def delete(self, key: str) -> None:
        """Delete a value from AILF memory.
        
        Args:
            key: The key to delete
        """
        await self.ailf_memory.delete(key)
    
    async def get_all(self) -> Dict[str, Any]:
        """Get all values from AILF memory.
        
        Returns:
            Dictionary of all stored key-value pairs
        """
        return await self.ailf_memory.get_all()
    
    async def clear(self) -> None:
        """Clear all values in the current namespace."""
        await self.ailf_memory.clear()
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return await self.ailf_memory.exists(key)


class SharedMemoryManager:
    """Manager for sharing memory between AILF and Kagent components.
    
    This higher-level class facilitates memory sharing between AILF and Kagent
    components, managing synchronization and translation where needed.
    
    Attributes:
        kagent_memory: The Kagent memory interface (AILFMemoryBridge)
        ailf_memory: The direct AILF memory manager
        namespace: The shared namespace for memory
    """
    
    def __init__(self, namespace: str = "shared"):
        """Initialize a shared memory manager.
        
        Args:
            namespace: The namespace to use for shared memory
        """
        self.namespace = namespace
        self.kagent_memory = AILFMemoryBridge(namespace=namespace)
        self.ailf_memory = AILFMemory(namespace=namespace)
    
    async def sync(self) -> None:
        """Force synchronization between memory systems.
        
        This is typically only needed in special cases where automatic
        synchronization is insufficient.
        """
        # In most cases, synchronization would be automatic through the bridge
        # This method exists for explicit sync cases or future extension
        pass
    
    async def import_from_json(self, file_path: str) -> None:
        """Import memory contents from a JSON file.
        
        Args:
            file_path: Path to the JSON file to import
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            for key, value in data.items():
                await self.kagent_memory.set(key, value)
        except Exception as e:
            raise RuntimeError(f"Failed to import memory from {file_path}: {str(e)}")
    
    async def export_to_json(self, file_path: str) -> None:
        """Export memory contents to a JSON file.
        
        Args:
            file_path: Path to save the JSON file
        """
        try:
            data = await self.kagent_memory.get_all()
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to export memory to {file_path}: {str(e)}")
