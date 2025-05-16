"""
Agent module for direct import in tests.

This file allows direct imports from the source directory for testing.
"""
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).resolve().parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Now we can import our agent modules
from ailf.agent.base import Agent, AgentConfig, AgentResult, AgentMemory, PlanningStrategy, AgentStatus, AgentStep
from ailf.agent.patterns import ReactivePlan, DeliberativePlan, TreeOfThoughtsPlan
from ailf.agent.tools import tool, ToolRegistry, execute_tool

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentResult", 
    "AgentMemory",
    "PlanningStrategy",
    "AgentStatus",
    "AgentStep",
    "ReactivePlan",
    "DeliberativePlan", 
    "TreeOfThoughtsPlan",
    "tool",
    "ToolRegistry",
    "execute_tool"
]