# This file marks ailf.routing as a package
"""
Agent routing and task delegation components for ailf.

This module provides components for routing incoming messages to appropriate handlers
and delegating tasks to other agents or workers.
"""

# Import enhanced implementations
from .agent_router import AgentRouter, RouteRule
from .task_delegator import TaskDelegator, TaskTrackingStore

# Legacy/compatibility imports
from .execution import TaskDelegator as LegacyTaskDelegator
from .execution import AgentRouter as LegacyAgentRouter

__all__ = [
    "TaskDelegator",
    "TaskTrackingStore",
    "AgentRouter",
    "RouteRule",
    "LegacyTaskDelegator",
    "LegacyAgentRouter",
]