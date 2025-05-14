"""A2A protocol multi-agent orchestration.

This module provides utilities for orchestrating multiple A2A-compatible agents,
enabling complex workflows that involve multiple agents working together.
"""
import asyncio
import json
import logging
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, Callable, AsyncIterator

import httpx
from pydantic import BaseModel, Field, validator

from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_registry import A2ARegistryManager, RegistryEntry
from ailf.schemas.a2a import (
    AgentCard,
    Message,
    MessagePart,
    MessageType,
    Task,
    TaskDelta,
    TaskState,
)

logger = logging.getLogger(__name__)


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""
    pass


class RouteType(str, Enum):
    """Types of routes between agents."""
    SEQUENTIAL = "sequential"  # Route from one agent to the next in sequence
    CONDITIONAL = "conditional"  # Route based on conditions
    PARALLEL = "parallel"  # Route to multiple agents in parallel
    DYNAMIC = "dynamic"  # Route determined at runtime


class RouteCondition(BaseModel):
    """A condition for conditional routing."""
    field: str = Field(..., description="The field to check in the task/message")
    operator: str = Field(..., description="The operator (eq, contains, gt, lt, etc.)")
    value: Any = Field(..., description="The value to compare against")
    route_to: str = Field(..., description="The ID of the agent to route to if condition is met")


class AgentRoute(BaseModel):
    """A route between agents in the orchestration."""
    source_agent: str = Field(..., description="ID of the source agent")
    type: RouteType = Field(..., description="Type of routing")
    destination_agents: List[str] = Field(
        default_factory=list,
        description="IDs of destination agents (for sequential and parallel)"
    )
    conditions: Optional[List[RouteCondition]] = Field(
        None,
        description="Conditions for conditional routing"
    )
    dynamic_router: Optional[str] = Field(
        None,
        description="Name of the router function for dynamic routing"
    )
    
    @validator("conditions")
    def validate_conditional_route(cls, v, values):
        """Validate that conditional routes have conditions."""
        if values.get("type") == RouteType.CONDITIONAL and not v:
            raise ValueError("Conditional routes must have conditions")
        return v
    
    @validator("dynamic_router")
    def validate_dynamic_route(cls, v, values):
        """Validate that dynamic routes have a router function."""
        if values.get("type") == RouteType.DYNAMIC and not v:
            raise ValueError("Dynamic routes must have a router function")
        return v
    
    @validator("destination_agents")
    def validate_destination_agents(cls, v, values):
        """Validate destination agents for non-dynamic routes."""
        if values.get("type") in (RouteType.SEQUENTIAL, RouteType.PARALLEL) and not v:
            raise ValueError(f"{values.get('type')} routes must have destination agents")
        return v


class TaskHandler(BaseModel):
    """A handler for a task in the orchestration."""
    task_id: str = Field(..., description="ID of the task")
    current_agent: str = Field(..., description="ID of the current agent")
    history: List[str] = Field(
        default_factory=list,
        description="History of agent IDs that have handled this task"
    )
    status: TaskState = Field(default=TaskState.CREATED, description="Current task status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Task metadata")


class OrchestrationConfig(BaseModel):
    """Configuration for agent orchestration."""
    routes: List[AgentRoute] = Field(..., description="Routes between agents")
    entry_points: List[str] = Field(
        ...,
        description="Agent IDs that can serve as entry points"
    )
    max_routing_depth: int = Field(
        default=10,
        description="Maximum number of routing steps allowed for a task"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for orchestration"
    )


class A2AOrchestrator:
    """Orchestrates multiple A2A-compatible agents to work together.
    
    This class manages the flow of tasks between multiple agents based on defined routes
    and conditions, enabling complex multi-agent workflows.
    """
    
    def __init__(
        self,
        config: OrchestrationConfig,
        registry_manager: Optional[A2ARegistryManager] = None
    ):
        """Initialize the orchestrator.
        
        Args:
            config: Configuration for the orchestration.
            registry_manager: Optional registry manager for agent discovery.
        """
        self.config = config
        self.registry_manager = registry_manager
        self.clients: Dict[str, A2AClient] = {}
        self.task_handlers: Dict[str, TaskHandler] = {}
        self.dynamic_routers: Dict[str, Callable] = {}
    
    def register_dynamic_router(self, name: str, router_func: Callable) -> None:
        """Register a dynamic router function.
        
        Args:
            name: Name of the router function.
            router_func: The function that will determine routing.
                The function should accept a Task and return a string agent ID.
        """
        self.dynamic_routers[name] = router_func
    
    async def setup_client(self, agent_id: str) -> A2AClient:
        """Set up an A2A client for an agent.
        
        Args:
            agent_id: The ID of the agent.
            
        Returns:
            An A2AClient instance.
            
        Raises:
            OrchestratorError: If the agent cannot be found.
        """
        # Return existing client if available
        if agent_id in self.clients:
            return self.clients[agent_id]
        
        # Look up agent in registry if available
        if self.registry_manager:
            try:
                agent = await self.registry_manager.get_agent(agent_id)
                self.clients[agent_id] = A2AClient(base_url=agent.url)
                return self.clients[agent_id]
            except Exception as e:
                raise OrchestratorError(f"Failed to create client for agent {agent_id}: {str(e)}")
        else:
            raise OrchestratorError(f"No registry manager available to look up agent {agent_id}")
    
    async def create_task(self, entry_point_id: str) -> Task:
        """Create a new task at an entry point agent.
        
        Args:
            entry_point_id: ID of the entry point agent.
            
        Returns:
            The created task.
            
        Raises:
            OrchestratorError: If the entry point is invalid.
        """
        if entry_point_id not in self.config.entry_points:
            raise OrchestratorError(f"Agent {entry_point_id} is not a valid entry point")
        
        client = await self.setup_client(entry_point_id)
        task = await client.create_task()
        
        # Create a task handler
        handler = TaskHandler(
            task_id=task.id,
            current_agent=entry_point_id,
            history=[entry_point_id]
        )
        self.task_handlers[task.id] = handler
        
        return task
    
    async def send_message(self, task_id: str, message: Message) -> Task:
        """Send a message to the current agent for a task.
        
        Args:
            task_id: ID of the task.
            message: The message to send.
            
        Returns:
            The updated task after processing.
            
        Raises:
            OrchestratorError: If the task is not found.
        """
        if task_id not in self.task_handlers:
            raise OrchestratorError(f"Task {task_id} not found in orchestrator")
        
        handler = self.task_handlers[task_id]
        client = await self.setup_client(handler.current_agent)
        
        # Send the message to the current agent
        response = await client.send_message(task_id, message)
        
        # If task is completed, check if we need to route to another agent
        if response.state == TaskState.COMPLETED:
            # Check for routes from the current agent
            next_agent = await self._find_next_agent(handler.current_agent, response)
            if next_agent:
                # Route the task to the next agent
                response = await self._route_task(response, handler.current_agent, next_agent)
        
        # Update the task handler with the latest state
        handler.status = response.state
        self.task_handlers[task_id] = handler
        
        return response
    
    async def send_message_streaming(
        self,
        task_id: str,
        message: Message
    ) -> AsyncIterator[TaskDelta]:
        """Send a message to the current agent for a task with streaming response.
        
        Args:
            task_id: ID of the task.
            message: The message to send.
            
        Yields:
            TaskDelta objects as they are received.
            
        Raises:
            OrchestratorError: If the task is not found.
        """
        if task_id not in self.task_handlers:
            raise OrchestratorError(f"Task {task_id} not found in orchestrator")
        
        handler = self.task_handlers[task_id]
        client = await self.setup_client(handler.current_agent)
        
        # Stream the message to the current agent
        final_delta = None
        async for delta in client.send_message_streaming(task_id, message):
            # Keep track of the final delta to check for completion
            if delta.done:
                final_delta = delta
            yield delta
        
        # If task is completed, check if we need to route to another agent
        if final_delta and final_delta.done:
            # Get the complete task to check state
            task = await client.get_task(task_id)
            if task.state == TaskState.COMPLETED:
                # Check for routes from the current agent
                next_agent = await self._find_next_agent(handler.current_agent, task)
                if next_agent:
                    # Route the task to the next agent
                    routed_task = await self._route_task(task, handler.current_agent, next_agent)
                    # Yield a delta indicating the routing
                    yield TaskDelta(
                        id=task_id,
                        metadata={
                            "orchestrator": {
                                "routed_to": next_agent,
                                "timestamp": datetime.now(UTC).isoformat()
                            }
                        }
                    )
        
        # Update the task handler
        task = await client.get_task(task_id)
        handler.status = task.state
        self.task_handlers[task_id] = handler
    
    async def get_task(self, task_id: str) -> Task:
        """Get the current state of a task.
        
        Args:
            task_id: ID of the task.
            
        Returns:
            The current state of the task.
            
        Raises:
            OrchestratorError: If the task is not found.
        """
        if task_id not in self.task_handlers:
            raise OrchestratorError(f"Task {task_id} not found in orchestrator")
        
        handler = self.task_handlers[task_id]
        client = await self.setup_client(handler.current_agent)
        
        # Get the task from the current agent
        return await client.get_task(task_id)
    
    async def _find_next_agent(self, current_agent_id: str, task: Task) -> Optional[str]:
        """Find the next agent to route a task to.
        
        Args:
            current_agent_id: ID of the current agent.
            task: The task to route.
            
        Returns:
            ID of the next agent, or None if there is no next agent.
        """
        # Find routes from the current agent
        routes = [r for r in self.config.routes if r.source_agent == current_agent_id]
        if not routes:
            return None
        
        # Process each route based on its type
        for route in routes:
            if route.type == RouteType.SEQUENTIAL:
                # Simply route to the first destination agent
                return route.destination_agents[0]
            
            elif route.type == RouteType.CONDITIONAL:
                # Check conditions to determine destination
                for condition in route.conditions:
                    if self._evaluate_condition(condition, task):
                        return condition.route_to
            
            elif route.type == RouteType.PARALLEL:
                # In this simple implementation, we just route to the first parallel agent
                # A more sophisticated implementation would clone the task to all destinations
                logger.warning(
                    "Parallel routing is using only the first destination. "
                    "Full parallel routing requires task cloning."
                )
                return route.destination_agents[0]
            
            elif route.type == RouteType.DYNAMIC:
                # Use the dynamic router function
                router_func = self.dynamic_routers.get(route.dynamic_router)
                if not router_func:
                    logger.error(f"Dynamic router '{route.dynamic_router}' not registered")
                    continue
                
                try:
                    next_agent = router_func(task)
                    return next_agent
                except Exception as e:
                    logger.error(f"Error in dynamic router: {str(e)}")
        
        # No route found
        return None
    
    def _evaluate_condition(self, condition: RouteCondition, task: Task) -> bool:
        """Evaluate a routing condition.
        
        Args:
            condition: The condition to evaluate.
            task: The task to check against the condition.
            
        Returns:
            True if the condition is met, False otherwise.
        """
        # Parse the field path (e.g., "messages[-1].parts[0].content")
        value = self._get_field_value(task, condition.field)
        
        # Evaluate based on operator
        op = condition.operator
        if op == "eq":
            return value == condition.value
        elif op == "neq":
            return value != condition.value
        elif op == "contains":
            return condition.value in value if value is not None else False
        elif op == "gt":
            return value > condition.value if value is not None else False
        elif op == "lt":
            return value < condition.value if value is not None else False
        elif op == "ge":
            return value >= condition.value if value is not None else False
        elif op == "le":
            return value <= condition.value if value is not None else False
        else:
            logger.warning(f"Unknown operator: {op}")
            return False
    
    def _get_field_value(self, task: Task, field_path: str) -> Any:
        """Get a value from a task using a field path.
        
        Args:
            task: The task to extract the value from.
            field_path: Path to the field (e.g., "messages[-1].parts[0].content")
            
        Returns:
            The value at the specified path, or None if not found.
        """
        parts = field_path.split(".")
        value = task.model_dump()
        
        try:
            for part in parts:
                # Handle array indexing
                if "[" in part and part.endswith("]"):
                    name, index_str = part.split("[", 1)
                    index_str = index_str[:-1]  # Remove the closing bracket
                    
                    # Handle negative indexing (-1 for last element)
                    if index_str.startswith("-"):
                        index = int(index_str)
                        value = value[name][index]
                    else:
                        value = value[name][int(index_str)]
                else:
                    value = value[part]
            return value
        except (KeyError, IndexError, TypeError) as e:
            logger.debug(f"Field path '{field_path}' not found in task: {str(e)}")
            return None
    
    async def _route_task(self, task: Task, from_agent: str, to_agent: str) -> Task:
        """Route a task from one agent to another.
        
        Args:
            task: The task to route.
            from_agent: ID of the source agent.
            to_agent: ID of the destination agent.
            
        Returns:
            The task after routing to the new agent.
            
        Raises:
            OrchestratorError: If routing fails or maximum depth is reached.
        """
        # Get the task handler
        handler = self.task_handlers[task.id]
        
        # Check routing depth
        if len(handler.history) >= self.config.max_routing_depth:
            raise OrchestratorError(
                f"Maximum routing depth ({self.config.max_routing_depth}) reached for task {task.id}"
            )
        
        # Get clients for both agents
        from_client = await self.setup_client(from_agent)
        to_client = await self.setup_client(to_agent)
        
        # Create a new task on the destination agent
        new_task = await to_client.create_task()
        
        # Add routing metadata
        routing_metadata = {
            "routed_from": from_agent,
            "original_task_id": task.id,
            "routing_timestamp": datetime.now(UTC).isoformat(),
            "routing_step": len(handler.history)
        }
        
        # Combine the content of all messages into a single message for the new agent
        messages_content = []
        for msg in task.messages:
            for part in msg.parts:
                if part.type == MessageType.TEXT:
                    messages_content.append(f"{msg.role}: {part.content}")
        
        # Create a combined message with task history
        combined_content = (
            f"--- Task History ---\n"
            f"This task was routed from agent '{from_agent}' with original task ID '{task.id}'.\n"
            f"Previous agents: {', '.join(handler.history)}\n\n"
            f"--- Messages ---\n"
            f"{chr(10).join(messages_content)}"
        )
        
        # Send the combined message to the new agent
        message = Message(
            role="user",
            parts=[MessagePart(type="text", content=combined_content)],
            metadata={"routing": routing_metadata}
        )
        new_task = await to_client.send_message(new_task.id, message)
        
        # Update the task handler
        handler.current_agent = to_agent
        handler.history.append(to_agent)
        handler.status = new_task.state
        handler.metadata["routing_history"] = handler.metadata.get("routing_history", []) + [{
            "from": from_agent,
            "to": to_agent,
            "timestamp": datetime.now(UTC).isoformat(),
            "original_task_id": task.id,
            "new_task_id": new_task.id
        }]
        self.task_handlers[task.id] = handler
        
        # Also create a handler for the new task ID
        new_handler = TaskHandler(
            task_id=new_task.id,
            current_agent=to_agent,
            history=handler.history.copy(),
            status=new_task.state,
            metadata={
                "original_task_id": task.id,
                "routing": routing_metadata
            }
        )
        self.task_handlers[new_task.id] = new_handler
        
        return new_task


class ParallelTaskGroup:
    """A group of tasks that are processed in parallel.
    
    This class manages a set of tasks that are executed on multiple agents in parallel,
    and provides methods to interact with all of them as a group.
    """
    
    def __init__(self, orchestrator: A2AOrchestrator):
        """Initialize the parallel task group.
        
        Args:
            orchestrator: The orchestrator to use for task management.
        """
        self.orchestrator = orchestrator
        self.tasks: Dict[str, Task] = {}  # task_id -> task
        self.agent_tasks: Dict[str, List[str]] = {}  # agent_id -> list of task_ids
    
    async def create_tasks(self, agent_ids: List[str]) -> List[Task]:
        """Create tasks on multiple agents in parallel.
        
        Args:
            agent_ids: List of agent IDs to create tasks on.
            
        Returns:
            List of created tasks.
        """
        tasks = []
        for agent_id in agent_ids:
            task = await self.orchestrator.create_task(agent_id)
            self.tasks[task.id] = task
            self.agent_tasks.setdefault(agent_id, []).append(task.id)
            tasks.append(task)
        return tasks
    
    async def send_message_to_all(self, message: Message) -> Dict[str, Task]:
        """Send a message to all tasks in the group.
        
        Args:
            message: The message to send.
            
        Returns:
            A dictionary mapping task IDs to updated tasks.
        """
        results = {}
        for task_id in self.tasks:
            task = await self.orchestrator.send_message(task_id, message)
            results[task_id] = task
            self.tasks[task_id] = task
        return results
    
    async def send_message_to_agent(self, agent_id: str, message: Message) -> List[Task]:
        """Send a message to all tasks on a specific agent.
        
        Args:
            agent_id: ID of the agent to send to.
            message: The message to send.
            
        Returns:
            List of updated tasks.
        """
        if agent_id not in self.agent_tasks:
            return []
        
        results = []
        for task_id in self.agent_tasks[agent_id]:
            task = await self.orchestrator.send_message(task_id, message)
            self.tasks[task_id] = task
            results.append(task)
        return results
    
    async def collect_results(self) -> Dict[str, Dict[str, Any]]:
        """Collect results from all tasks.
        
        Returns:
            A dictionary mapping agent IDs to their response data.
        """
        results = {}
        for agent_id, task_ids in self.agent_tasks.items():
            agent_results = []
            for task_id in task_ids:
                task = await self.orchestrator.get_task(task_id)
                # Extract the assistant messages
                messages = [msg for msg in task.messages if msg.role == "assistant"]
                if messages:
                    # Get the content of the last assistant message
                    last_message = messages[-1]
                    content = [part.content for part in last_message.parts if part.type == "text"]
                    agent_results.append({
                        "task_id": task_id,
                        "content": content,
                        "state": task.state,
                        "timestamp": last_message.createdAt.isoformat() if hasattr(last_message, "createdAt") else None
                    })
            results[agent_id] = agent_results
        return results


class SequentialTaskChain:
    """A chain of tasks that are processed sequentially across agents.
    
    This class manages a task that is passed from one agent to another in sequence,
    maintaining the context and conversation history.
    """
    
    def __init__(self, orchestrator: A2AOrchestrator, agent_sequence: List[str]):
        """Initialize the sequential task chain.
        
        Args:
            orchestrator: The orchestrator to use for task management.
            agent_sequence: List of agent IDs to process the task in sequence.
        """
        self.orchestrator = orchestrator
        self.agent_sequence = agent_sequence
        self.current_index = 0
        self.task_id = None
        self.tasks: List[Task] = []
    
    async def start_chain(self) -> Task:
        """Start the task chain with the first agent.
        
        Returns:
            The created task.
        """
        if not self.agent_sequence:
            raise OrchestratorError("No agents in sequence")
        
        # Create task on the first agent
        first_agent = self.agent_sequence[0]
        task = await self.orchestrator.create_task(first_agent)
        self.task_id = task.id
        self.tasks.append(task)
        return task
    
    async def send_message(self, message: Message) -> Task:
        """Send a message to the current agent in the chain.
        
        If the current agent completes the task, it will be automatically
        forwarded to the next agent in the sequence.
        
        Args:
            message: The message to send.
            
        Returns:
            The updated task.
        """
        if not self.task_id:
            raise OrchestratorError("Chain not started. Call start_chain first.")
        
        # Send message to current agent
        task = await self.orchestrator.send_message(self.task_id, message)
        self.tasks.append(task)
        
        # Check if we need to move to the next agent
        if task.state == TaskState.COMPLETED:
            return await self._advance_to_next_agent(task)
        
        return task
    
    async def _advance_to_next_agent(self, task: Task) -> Task:
        """Advance to the next agent in the sequence.
        
        Args:
            task: The current task.
            
        Returns:
            The updated task after forwarding to the next agent.
        """
        self.current_index += 1
        
        # Check if we've reached the end of the sequence
        if self.current_index >= len(self.agent_sequence):
            logger.info("Reached the end of the agent sequence")
            return task
        
        # Get the next agent
        next_agent = self.agent_sequence[self.current_index]
        
        # Get clients
        from_agent = self.agent_sequence[self.current_index - 1]
        
        # Create a routing config for the orchestrator
        route = AgentRoute(
            source_agent=from_agent,
            type=RouteType.SEQUENTIAL,
            destination_agents=[next_agent]
        )
        
        # Route the task
        new_task = await self.orchestrator._route_task(task, from_agent, next_agent)
        self.task_id = new_task.id
        self.tasks.append(new_task)
        
        return new_task
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history across all agents.
        
        Returns:
            A list of message dictionaries with agent context.
        """
        history = []
        for task in self.tasks:
            agent_id = None
            for handler in self.orchestrator.task_handlers.values():
                if handler.task_id == task.id:
                    agent_id = handler.current_agent
                    break
            
            for msg in task.messages:
                history.append({
                    "role": msg.role,
                    "content": [part.content for part in msg.parts if part.type == "text"],
                    "agent_id": agent_id,
                    "task_id": task.id,
                    "timestamp": msg.createdAt.isoformat() if hasattr(msg, "createdAt") else None
                })
        
        return history
