"""Pydantic schemas for ailf.routing."""
from typing import Dict, Any, Optional, List, Literal
from enum import Enum
from pydantic import BaseModel, Field

from ailf.schemas.interaction import AnyInteractionMessage

class TaskStatus(str, Enum):
    """Status values for tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class TaskPriority(str, Enum):
    """Priority values for tasks."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class DelegatedTaskMessage(BaseModel):
    """Message for delegating a task to another agent or worker."""
    task_id: str = Field(description="Unique ID for the delegated task.")
    target_agent_id: Optional[str] = Field(default=None, description="ID of the target agent/worker.")
    task_name: str = Field(description="Name or type of the task to be performed.")
    task_input: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for the task.")
    source_agent_id: Optional[str] = Field(default=None, description="ID of the agent delegating the task.")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Priority of the task.")
    timeout: Optional[float] = Field(default=None, description="Optional timeout in seconds.")
    execution_constraints: Optional[Dict[str, Any]] = Field(default=None, description="Optional constraints for task execution.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the task.")

class TaskResultMessage(BaseModel):
    """Message containing the result of a delegated task."""
    task_id: str = Field(description="Unique ID of the task this result corresponds to.")
    status: TaskStatus = Field(description="Status of the task.")
    result: Optional[Any] = Field(default=None, description="The output or result of the task.")
    error_message: Optional[str] = Field(default=None, description="Error message if the task failed.")
    processing_time: Optional[float] = Field(default=None, description="Time taken to process the task in seconds.")
    execution_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Optional metrics about the execution.")
    source_agent_id: Optional[str] = Field(default=None, description="ID of the agent that completed the task.")

class RouteDecision(BaseModel):
    """Represents a decision made by the AgentRouter."""
    target_handler: Optional[str] = Field(default=None, description="Name of the internal handler or function to route to.")
    target_agent_id: Optional[str] = Field(default=None, description="ID of another agent to delegate/forward the request to.")
    # action: str # e.g., "handle_internally", "delegate_externally", "reject"
    confidence: float = Field(default=1.0, description="Confidence score for this routing decision.")
    reasoning: Optional[str] = Field(default=None, description="Explanation for the routing decision (if LLM-driven).")

class RouteDecisionContext(BaseModel):
    """Context provided to an LLM for making a routing decision."""
    incoming_message: AnyInteractionMessage # Changed from StandardMessage (which was BaseMessage)
    available_internal_handlers: List[str] = Field(default_factory=list)
    known_external_agents: List[Dict[str, Any]] = Field(default_factory=list, description="List of known external agents and their capabilities.")
    routing_rules: Optional[Dict[str, Any]] = Field(default=None, description="Predefined routing rules.")
    historical_context: Optional[List[Dict]] = Field(default_factory=list, description="Recent interaction history.")
