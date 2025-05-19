"""
Agent Framework.

This module provides a unified framework for building AI agents with different capabilities
and architectural patterns. It serves as the central integration point between different
components like AI engines, tools, memory systems, and communication protocols.

Key Components:
    Agent: Base agent class with essential agent capabilities
    ReactivePlan: Reactive agent planning pattern
    DeliberativePlan: Deliberative agent planning pattern
    AgentWithTools: Mixin for tool-using capabilities

Example:
    >>> from ailf.agent import Agent
    >>> from ailf.agent.patterns import DeliberativePlan
    >>> 
    >>> # Create a deliberative agent
    >>> agent = Agent(
    ...     name="ResearchAssistant",
    ...     model_name="openai:gpt-4-turbo",
    ...     planning_strategy=DeliberativePlan()
    ... )
    >>> 
    >>> # Add tools to the agent
    >>> agent.add_tool(web_search)
    >>> agent.add_tool(document_reader)
    >>> 
    >>> # Run the agent
    >>> result = await agent.run("Research the impact of quantum computing on cryptography")
"""

from ailf.agent.base import Agent, AgentConfig, AgentResult, AgentMemory
from ailf.agent.patterns import ReactivePlan, DeliberativePlan, TreeOfThoughtsPlan

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentResult",
    "AgentMemory",
    "ReactivePlan",
    "DeliberativePlan",
    "TreeOfThoughtsPlan",
]
