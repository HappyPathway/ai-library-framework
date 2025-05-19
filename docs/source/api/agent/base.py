"""
This is a wrapper file to help with documentation imports.
It simply re-exports the base agent module from the src structure.
"""

try:
    from ailf.agent.base import *  # Re-export everything
except ImportError:
    # Fallback with minimal info if the import fails
    class AgentStatus:
        """Status of an agent execution."""
        IDLE = "idle"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        
    class Agent:
        """
        Base Agent Implementation.
        
        This class provides the foundation for all agents in the system.
        """
        pass
