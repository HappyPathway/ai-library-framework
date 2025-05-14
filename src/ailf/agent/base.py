"""
Base Agent Implementation.

This module provides the foundation for all agents in the system, including the core Agent
class and supporting models for configuration, results, and memory management.

The Agent class is designed for extension through composition rather than inheritance,
using well-defined interfaces for components like planning strategies, tools, and memory systems.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Type, Union, Callable, TypeVar

from pydantic import BaseModel, Field

from ailf.ai.engine import AIEngine

logger = logging.getLogger(__name__)

# Type definitions
T = TypeVar('T', bound=BaseModel)


class AgentStatus(str, Enum):
    """Status of an agent execution."""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentConfig(BaseModel):
    """Configuration for an agent."""
    name: str = Field(description="Name of the agent")
    description: str = Field(description="Description of the agent's purpose and capabilities")
    model_name: str = Field(description="Model name for the agent's primary AI engine")
    max_iterations: int = Field(default=10, description="Maximum number of execution iterations")
    temperature: float = Field(default=0.1, description="Temperature for agent's reasoning")
    enable_memory: bool = Field(default=True, description="Whether agent has memory")
    timeout_seconds: Optional[float] = Field(default=None, description="Timeout for agent execution")
    verbose: bool = Field(default=False, description="Enable verbose logging")


class AgentStep(BaseModel):
    """A single step in an agent's execution."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    action: str = Field(description="Action taken by the agent")
    observation: Optional[str] = Field(default=None, description="Result of the action")
    reasoning: Optional[str] = Field(default=None, description="Agent's reasoning")
    status: str = Field(default="completed", description="Status of this step")


class AgentResult(BaseModel):
    """Result of an agent execution."""
    agent_id: str = Field(description="ID of the agent")
    status: AgentStatus = Field(description="Final status of the execution")
    output: Any = Field(description="Final output of the agent")
    steps: List[AgentStep] = Field(default_factory=list, description="Steps taken by the agent")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    elapsed_time: float = Field(description="Execution time in seconds")
    started_at: datetime = Field(description="When execution started")
    completed_at: datetime = Field(description="When execution completed")


class PlanningStrategy(ABC):
    """Abstract base class for agent planning strategies."""
    
    @abstractmethod
    async def plan(self, agent: 'Agent', query: str) -> List[AgentStep]:
        """Generate a plan for the agent to follow.
        
        Args:
            agent: The agent that will execute the plan
            query: The user query/task to plan for
            
        Returns:
            List[AgentStep]: Steps for the agent to execute
        """
        pass


class AgentMemory:
    """Memory system for agents."""
    
    def __init__(self):
        """Initialize an empty memory system."""
        self.interactions: List[Dict[str, Any]] = []
        self.facts: List[str] = []
        self.working_memory: Dict[str, Any] = {}
    
    def add_interaction(self, query: str, result: Any) -> None:
        """Add an interaction to memory.
        
        Args:
            query: User query or instruction
            result: Result of processing the query
        """
        self.interactions.append({
            "timestamp": datetime.now(),
            "query": query,
            "result": result
        })
    
    def add_fact(self, fact: str) -> None:
        """Add a fact to memory.
        
        Args:
            fact: The fact to remember
        """
        if fact not in self.facts:
            self.facts.append(fact)
    
    def get_recent_interactions(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent interactions.
        
        Args:
            count: Number of recent interactions to return
            
        Returns:
            List[Dict[str, Any]]: Recent interactions
        """
        return self.interactions[-count:]
    
    def clear(self) -> None:
        """Clear all memory."""
        self.interactions = []
        self.facts = []
        self.working_memory = {}


class Agent:
    """Base agent class implementing the fundamental agent capabilities."""
    
    def __init__(
        self,
        name: str,
        model_name: str,
        description: Optional[str] = None,
        planning_strategy: Optional[PlanningStrategy] = None,
        config: Optional[AgentConfig] = None
    ):
        """Initialize a new agent.
        
        Args:
            name: Name of the agent
            model_name: Model name for the agent's primary AI engine
            description: Description of the agent's purpose
            planning_strategy: Strategy for planning actions
            config: Additional configuration options
        """
        self.config = config or AgentConfig(
            name=name,
            description=description or f"{name} Agent",
            model_name=model_name
        )
        
        self.name = name
        self.description = description or f"{name} Agent"
        self.agent_id = str(uuid.uuid4())
        self.planning_strategy = planning_strategy
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory() if self.config.enable_memory else None
        self.tools: Dict[str, Callable] = {}
        self._ai_engine: Optional[AIEngine] = None
    
    @property
    def ai_engine(self) -> AIEngine:
        """Get or create the AI engine for this agent."""
        if self._ai_engine is None:
            self._ai_engine = AIEngine(
                feature_name=self.name.lower().replace(" ", "_"),
                model_name=self.config.model_name,
                temperature=self.config.temperature
            )
        return self._ai_engine
    
    def add_tool(self, tool_func: Callable, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """Register a tool with the agent.
        
        Args:
            tool_func: Function implementing the tool
            name: Name of the tool (defaults to function name)
            description: Description of the tool
        """
        tool_name = name or tool_func.__name__
        tool_desc = description or (tool_func.__doc__ or "No description available")
        
        # Store tool metadata
        self.tools[tool_name] = tool_func
        logger.debug(f"Added tool '{tool_name}' to agent '{self.name}'")
    
    async def run(
        self,
        query: str,
        output_schema: Optional[Type[T]] = None,
        **kwargs
    ) -> Union[AgentResult, T]:
        """Run the agent to address a query or task.
        
        Args:
            query: User query or instruction
            output_schema: Optional Pydantic model for structured output
            **kwargs: Additional parameters to pass to the execution
            
        Returns:
            Union[AgentResult, T]: Result of agent execution
        """
        start_time = datetime.now()
        result = AgentResult(
            agent_id=self.agent_id,
            status=AgentStatus.EXECUTING,
            output=None,
            elapsed_time=0.0,
            started_at=start_time,
            completed_at=start_time  # Will be updated
        )
        
        try:
            # Update agent status
            self.status = AgentStatus.PLANNING
            
            # Generate plan if planning strategy exists
            steps = []
            if self.planning_strategy:
                steps = await self.planning_strategy.plan(self, query)
                
            # If no explicit planning steps, create a single execution step
            if not steps:
                steps = [AgentStep(
                    action="direct_execution",
                    reasoning="Direct execution of query without explicit planning"
                )]
            
            # Execute each step in the plan
            self.status = AgentStatus.EXECUTING
            final_output = await self._execute_steps(steps, query, output_schema, **kwargs)
            
            # Record results
            result.steps = steps
            result.status = AgentStatus.COMPLETED
            result.output = final_output
            
            # Update memory if enabled
            if self.memory:
                self.memory.add_interaction(query, final_output)
                
            return final_output if output_schema else result
            
        except Exception as e:
            logger.exception(f"Agent execution failed: {str(e)}")
            self.status = AgentStatus.FAILED
            result.status = AgentStatus.FAILED
            result.error = str(e)
            return result
            
        finally:
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            result.elapsed_time = elapsed
            result.completed_at = end_time
    
    async def _execute_steps(
        self,
        steps: List[AgentStep],
        query: str,
        output_schema: Optional[Type[T]] = None,
        **kwargs
    ) -> Any:
        """Execute a series of steps.
        
        Args:
            steps: Steps to execute
            query: Original user query
            output_schema: Optional Pydantic schema for output
            **kwargs: Additional parameters
            
        Returns:
            Any: Result of execution
        """
        system_prompt = self._get_system_prompt(query)
        
        for i, step in enumerate(steps):
            # Only execute steps without observations (unexecuted steps)
            if step.observation is None:
                try:
                    # If this is the last step and we have an output schema, use it
                    if i == len(steps) - 1 and output_schema:
                        result = await self.ai_engine.analyze(
                            step.action,
                            system=system_prompt,
                            output_schema=output_schema,
                            **kwargs
                        )
                        
                        # Handle structured output
                        if hasattr(result, 'model_dump'):
                            # Handle Pydantic v2 model
                            step.observation = str(result.model_dump())
                        elif hasattr(result, 'dict'):
                            # Handle Pydantic v1 model
                            step.observation = str(result.dict())
                        else:
                            # Direct conversion
                            step.observation = str(result)
                        return result
                    else:
                        # Otherwise just get text output
                        result = await self.ai_engine.analyze(
                            step.action,
                            system=system_prompt,
                            **kwargs
                        )
                        
                        # Handle different return types from AI engines
                        if isinstance(result, dict) and 'content' in result:
                            # Handle dictionary response with content field
                            step.observation = result['content']
                        elif isinstance(result, str):
                            # Handle direct string response
                            step.observation = result
                        else:
                            # Try to convert to string as fallback
                            step.observation = str(result)
                except Exception as e:
                    step.status = "failed"
                    step.observation = f"Error: {str(e)}"
                    raise
        
        # If we have an output schema, parse the final result
        final_step = steps[-1]
        if output_schema:
            try:
                # Check if we already have a parsed model
                if isinstance(final_step.observation, output_schema):
                    return final_step.observation
                
                # For string observations, try parsing as JSON
                if isinstance(final_step.observation, str):
                    try:
                        # Try to parse using model_validate_json for Pydantic V2
                        if hasattr(output_schema, 'model_validate_json'):
                            return output_schema.model_validate_json(final_step.observation)
                        # Try to use parse_raw for Pydantic V1
                        elif hasattr(output_schema, 'parse_raw'):
                            return output_schema.parse_raw(final_step.observation)
                    except Exception:
                        # If JSON parsing fails, try direct parsing
                        if hasattr(output_schema, 'model_validate'):
                            return output_schema.model_validate(final_step.observation)
                        elif hasattr(output_schema, 'parse_obj'):
                            return output_schema.parse_obj(final_step.observation)
                
                # If all parsing attempts fail, return the raw observation
                logger.warning(f"Failed to parse output using schema {output_schema.__name__}")
                return final_step.observation
            except Exception as e:
                logger.error(f"Error parsing output: {str(e)}")
                return final_step.observation
        
        return final_step.observation
    
    def _get_system_prompt(self, query: str) -> str:
        """Generate a system prompt for the agent.
        
        Args:
            query: User query to address
            
        Returns:
            str: System prompt
        """
        tool_descriptions = ""
        if self.tools:
            tool_descriptions = "Available tools:\n\n"
            for name, func in self.tools.items():
                doc = func.__doc__ or "No description"
                tool_descriptions += f"- {name}: {doc}\n"
        
        memory_context = ""
        if self.memory and self.memory.facts:
            memory_context = "Relevant information from memory:\n\n"
            for fact in self.memory.facts:
                memory_context += f"- {fact}\n"
        
        return f"""You are {self.name}, {self.description}.
        
Task: {query}

{tool_descriptions}
{memory_context}

Approach this task step by step, thinking carefully about what information you need
and how to use the available tools most effectively.
"""
