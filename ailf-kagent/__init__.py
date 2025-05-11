"""
AILF-Kagent Integration Package.

This package provides integration components between the Agentic AI Library Framework (AILF)
and Kagent, enabling AILF tools to be used within Kagent agents and leveraging AILF's
cognitive capabilities in Kagent workflows.
"""

from ailf_kagent.adapters import (
    # Tool adapters
    AILFToolAdapter,
    AILFToolRegistry,
    
    # Agent adapters
    AILFEnabledAgent, 
    ReActAgent,
    
    # Memory adapters
    AILFMemoryBridge,
    SharedMemoryManager,
    
    # Schema adapters
    map_ailf_to_kagent_schema,
    map_kagent_to_ailf_schema,
    SchemaRegistry,
    convert_instance_to_schema
)

__version__ = "0.1.0"
__all__ = [
    # Tool adapters
    "AILFToolAdapter",
    "AILFToolRegistry",
    
    # Agent adapters
    "AILFEnabledAgent", 
    "ReActAgent",
    
    # Memory adapters
    "AILFMemoryBridge",
    "SharedMemoryManager",
    
    # Schema adapters
    "map_ailf_to_kagent_schema",
    "map_kagent_to_ailf_schema",
    "SchemaRegistry",
    "convert_instance_to_schema"
]
