# Memory Integration

This guide explains how to share memory between AILF and Kagent components.

## AILFMemoryBridge

The `AILFMemoryBridge` class allows Kagent agents to use AILF's memory systems:

```python
from ailf_kagent import AILFMemoryBridge
from kagent.agents import Agent as KAgent

# Create a memory bridge
memory = AILFMemoryBridge(namespace="agent_memory")

# Use it with a Kagent agent
agent = KAgent(memory=memory)

# The agent will now use AILF's memory system
await agent.memory.set("user_preference", "dark_mode")
preference = await agent.memory.get("user_preference")  # Returns "dark_mode"
```

## SharedMemoryManager

The `SharedMemoryManager` provides a unified interface for memory operations:

```python
from ailf_kagent import SharedMemoryManager

# Create a shared memory manager
memory = SharedMemoryManager(namespace="shared_memory")

# Use the memory in both frameworks
# Kagent usage
await memory.kagent_memory.set("conversation_history", history)

# AILF usage
await memory.ailf_memory.set("working_memory", working_data)

# Synchronize memory (if needed)
await memory.sync()
```

## Import/Export Functionality

The `SharedMemoryManager` also provides import/export capabilities:

```python
# Save memory state to a file
await memory.export_to_json("memory_backup.json")

# Load memory state from a file
await memory.import_from_json("memory_backup.json")
```

## Custom Memory Bridge

You can create a custom memory bridge by extending `AILFMemoryBridge`:

```python
from ailf_kagent import AILFMemoryBridge

class PersistentMemoryBridge(AILFMemoryBridge):
    """Memory bridge with additional persistence capabilities."""
    
    async def set(self, key: str, value: Any) -> None:
        """Override set to add persistence."""
        # Use parent implementation
        await super().set(key, value)
        
        # Add persistence logic
        await self._save_to_database(key, value)
    
    async def _save_to_database(self, key: str, value: Any) -> None:
        """Save to external database."""
        # Implementation of database persistence
        pass
```

## Memory Namespaces

Using namespaces helps organize memory:

```python
# Create memories with different namespaces
user_memory = AILFMemoryBridge(namespace="user")
conversation_memory = AILFMemoryBridge(namespace="conversation")
agent_memory = AILFMemoryBridge(namespace="agent")

# Each operates in its own namespace
await user_memory.set("preference", "dark_mode")
await conversation_memory.set("history", [])
await agent_memory.set("tool_results", {})
```

## Best Practices

1. **Memory Segregation**: Use namespaces to segregate different types of memory
2. **Regular Sync**: For critical data, consider explicit sync operations
3. **Persistence**: For important information, implement persistence strategies
4. **Memory Cleaning**: Implement routines to clear stale data
5. **Memory Size**: Be mindful of memory growth in long-running applications
