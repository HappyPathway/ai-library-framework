"""Pydantic schemas for Agent2Agent (A2A) Protocol Integration.

This module provides Pydantic models that map to the A2A Protocol specification,
enabling AILF agents to interoperate with other agents using the A2A protocol.

References:
    - A2A Protocol Specification: https://a2ap.org/
"""
from typing import List, Dict, Any, Optional, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field, RootModel
from uuid import UUID, uuid4
from datetime import datetime, UTC


class AgentAuthentication(BaseModel):
    """Defines authentication requirements for an agent.
    
    Intended to match OpenAPI authentication structure.
    """
    schemes: List[str] = Field(
        ..., 
        description="Authentication schemes supported (e.g. 'Basic', 'Bearer')"
    )
    credentials: Optional[str] = Field(
        None, 
        description="Credentials a client should use for private cards"
    )


class AgentCapabilities(BaseModel):
    """Defines the capabilities of an A2A agent."""
    streaming: bool = Field(
        default=False, 
        description="Whether the agent supports streaming responses"
    )
    pushNotifications: bool = Field(
        default=False, 
        description="Whether the agent supports push notifications"
    )
    stateTransitionHistory: bool = Field(
        default=False, 
        description="Whether the agent tracks state transition history"
    )


class AgentProvider(BaseModel):
    """Information about the agent provider."""
    name: str = Field(..., description="Name of the provider or organization")
    url: Optional[str] = Field(None, description="URL of the provider")


class InputModes(str, Enum):
    """Valid input modes for an A2A agent."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    STRUCTURED = "structured"


class OutputModes(str, Enum):
    """Valid output modes for an A2A agent."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    STRUCTURED = "structured"


class TaskState(str, Enum):
    """Valid states for an A2A task."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class MessageType(str, Enum):
    """Valid types for A2A message parts."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    FILE = "file"
    STRUCTURED = "structured"


class AgentCard(BaseModel):
    """Agent card information for A2A Protocol."""
    name: str = Field(..., description="Name of the agent")
    description: str = Field(..., description="Description of the agent")
    url: str = Field(..., description="URL where the agent is hosted")
    provider: AgentProvider = Field(..., description="Provider information")
    version: str = Field(..., description="Version of the agent")
    documentationUrl: Optional[str] = Field(
        None, 
        description="URL to the agent's documentation"
    )
    capabilities: AgentCapabilities = Field(
        default_factory=AgentCapabilities, 
        description="Agent capabilities"
    )
    authentication: Optional[AgentAuthentication] = Field(
        None, 
        description="Authentication requirements"
    )
    defaultInputModes: List[InputModes] = Field(
        default_factory=lambda: [InputModes.TEXT], 
        description="Default input modes supported"
    )
    defaultOutputModes: List[OutputModes] = Field(
        default_factory=lambda: [OutputModes.TEXT], 
        description="Default output modes supported"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for the agent"
    )


class MessagePart(BaseModel):
    """A part of a message in the A2A protocol."""
    type: MessageType = Field(..., description="Type of message part")
    content: Any = Field(..., description="Content of the message part")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for this message part"
    )


class Message(BaseModel):
    """A message in the A2A protocol."""
    id: str = Field(
        default_factory=lambda: str(uuid4()), 
        description="Unique identifier for the message"
    )
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    parts: List[MessagePart] = Field(..., description="Message parts")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for the message"
    )
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), 
        description="When the message was created"
    )


class TaskIdParams(BaseModel):
    """Parameters for identifying a task."""
    taskId: str = Field(..., description="ID of the task")


class TaskQueryParams(BaseModel):
    """Query parameters for searching tasks."""
    limit: int = Field(10, description="Maximum number of tasks to return")
    skip: int = Field(0, description="Number of tasks to skip")


class MessageSendParams(BaseModel):
    """Parameters for sending a message."""
    taskId: str = Field(..., description="ID of the task")


class Task(BaseModel):
    """An A2A task."""
    id: str = Field(
        default_factory=lambda: str(uuid4()), 
        description="Unique identifier for the task"
    )
    state: TaskState = Field(
        default=TaskState.CREATED, 
        description="Current state of the task"
    )
    messages: List[Message] = Field(
        default_factory=list, 
        description="Messages in this task"
    )
    inputModes: List[InputModes] = Field(
        default_factory=lambda: [InputModes.TEXT], 
        description="Input modes allowed for this task"
    )
    outputModes: List[OutputModes] = Field(
        default_factory=lambda: [OutputModes.TEXT], 
        description="Output modes allowed for this task"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for this task"
    )
    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), 
        description="When the task was created"
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(UTC), 
        description="When the task was last updated"
    )


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    message: Message = Field(..., description="Message to send")
    inputModes: Optional[List[InputModes]] = Field(
        None, 
        description="Input modes for this message"
    )
    outputModes: Optional[List[OutputModes]] = Field(
        None, 
        description="Output modes for this message"
    )


class SendMessageResponse(BaseModel):
    """Response after sending a message."""
    task: Task = Field(..., description="Updated task with the new message")
    

class GetTaskRequest(BaseModel):
    """Request to get a task."""
    pass


class GetTaskResponse(BaseModel):
    """Response containing a task."""
    task: Task = Field(..., description="The requested task")


class A2ARequest(RootModel):
    """Base for all A2A requests."""
    root: Any


class TaskPushNotificationConfig(BaseModel):
    """Configuration for task push notifications."""
    url: str = Field(..., description="URL to send push notifications to")
    headers: Optional[Dict[str, str]] = Field(
        None, 
        description="Headers to include in the push notification request"
    )


class SetTaskPushNotificationConfigRequest(BaseModel):
    """Request to set task push notification configuration."""
    config: TaskPushNotificationConfig = Field(
        ..., 
        description="Push notification configuration"
    )


class SetTaskPushNotificationConfigResponse(BaseModel):
    """Response after setting task push notification configuration."""
    pass


class GetTaskPushNotificationConfigRequest(BaseModel):
    """Request to get task push notification configuration."""
    pass


class GetTaskPushNotificationConfigResponse(BaseModel):
    """Response containing task push notification configuration."""
    config: Optional[TaskPushNotificationConfig] = Field(
        None, 
        description="Push notification configuration"
    )


class CancelTaskRequest(BaseModel):
    """Request to cancel a task."""
    pass


class CancelTaskResponse(BaseModel):
    """Response after canceling a task."""
    task: Task = Field(..., description="The cancelled task")


# Classes for streaming responses
class SendMessageStreamingRequest(SendMessageRequest):
    """Request to send a message with streaming response."""
    pass


class MessagePartDelta(BaseModel):
    """Delta update for a message part in a streaming response."""
    type: Optional[MessageType] = Field(
        None, 
        description="Type of message part (provided in first delta)"
    )
    content: Any = Field(..., description="Content delta")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for this delta"
    )


class MessageDelta(BaseModel):
    """Delta update for a message in a streaming response."""
    id: Optional[str] = Field(
        None, 
        description="Message ID (provided in first delta)"
    )
    role: Optional[str] = Field(
        None, 
        description="Role (provided in first delta)"
    )
    parts: List[MessagePartDelta] = Field(
        default_factory=list, 
        description="Delta updates to message parts"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for this delta"
    )


class TaskDelta(BaseModel):
    """Delta update for a task in a streaming response."""
    id: Optional[str] = Field(
        None, 
        description="Task ID (provided in first delta)"
    )
    state: Optional[TaskState] = Field(
        None, 
        description="Updated state if changed"
    )
    messages: List[MessageDelta] = Field(
        default_factory=list, 
        description="Delta updates to messages"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata for this delta"
    )
    done: bool = Field(
        default=False, 
        description="Whether this is the last delta in the stream"
    )


class SendMessageStreamingResponse(BaseModel):
    """Streaming response after sending a message."""
    task: TaskDelta = Field(..., description="Delta update to the task")
