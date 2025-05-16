"""Pydantic schemas for Agent-UI (AG-UI) Protocol Integration.

This module provides Pydantic models that map to the AG-UI Protocol specification,
enabling AILF agents to interoperate with user interfaces using the AG-UI protocol.

References:
    - AG-UI Protocol Specification: https://github.com/langchain-ai/ag-ui
"""
from typing import List, Dict, Any, Optional, Union, Literal, Annotated
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime


class EventType(str, Enum):
    """AG-UI event types."""
    # Run lifecycle events
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"
    
    # Step lifecycle events
    STEP_STARTED = "STEP_STARTED"
    STEP_FINISHED = "STEP_FINISHED"
    
    # Text message events
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
    
    # Tool events
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    
    # State events
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    STATE_DELTA = "STATE_DELTA"
    
    # Other events
    MESSAGES_SNAPSHOT = "MESSAGES_SNAPSHOT"
    RAW = "RAW"
    CUSTOM = "CUSTOM"


class BaseEvent(BaseModel):
    """Base event for all AG-UI events."""
    type: EventType
    timestamp: Optional[int] = Field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    raw_event: Optional[Any] = None


class FunctionCall(BaseModel):
    """Name and arguments of a function call."""
    name: str
    arguments: str


class ToolCall(BaseModel):
    """A tool call, modelled after OpenAI tool calls."""
    id: str
    type: Literal["function"]
    function: FunctionCall


class BaseMessage(BaseModel):
    """A base message, modelled after OpenAI messages."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str
    content: Optional[str] = None
    name: Optional[str] = None


class UserMessage(BaseMessage):
    """A user message."""
    role: Literal["user"]


class AssistantMessage(BaseMessage):
    """An assistant message."""
    role: Literal["assistant"]
    tool_calls: Optional[List[ToolCall]] = None


class SystemMessage(BaseMessage):
    """A system message."""
    role: Literal["system"]


class ToolMessage(BaseMessage):
    """A tool message."""
    role: Literal["tool"]
    tool_call_id: str


Message = Annotated[
    Union[UserMessage, AssistantMessage, SystemMessage, ToolMessage],
    Field(discriminator="role")
]


class TextMessageStartEvent(BaseEvent):
    """Event indicating the start of a text message."""
    type: Literal[EventType.TEXT_MESSAGE_START]
    message_id: str
    role: Literal["assistant"]


class TextMessageContentEvent(BaseEvent):
    """Event containing text message content."""
    type: Literal[EventType.TEXT_MESSAGE_CONTENT]
    message_id: str
    content: str


class TextMessageEndEvent(BaseEvent):
    """Event indicating the end of a text message."""
    type: Literal[EventType.TEXT_MESSAGE_END]
    message_id: str


class RunStartedEvent(BaseEvent):
    """Event indicating the start of a run."""
    type: Literal[EventType.RUN_STARTED]
    run_id: str


class RunFinishedEvent(BaseEvent):
    """Event indicating the end of a run."""
    type: Literal[EventType.RUN_FINISHED]
    run_id: str


class RunErrorEvent(BaseEvent):
    """Event indicating an error in a run."""
    type: Literal[EventType.RUN_ERROR]
    run_id: str
    error: str


class ToolCallStartEvent(BaseEvent):
    """Event indicating the start of a tool call."""
    type: Literal[EventType.TOOL_CALL_START]
    tool_call_id: str
    name: str


class ToolCallArgsEvent(BaseEvent):
    """Event containing tool call arguments."""
    type: Literal[EventType.TOOL_CALL_ARGS]
    tool_call_id: str
    args: Dict[str, Any]


class ToolCallEndEvent(BaseEvent):
    """Event indicating the end of a tool call."""
    type: Literal[EventType.TOOL_CALL_END]
    tool_call_id: str
    output: Any
    error: Optional[Dict[str, str]] = None


class StateSnapshotEvent(BaseEvent):
    """Event containing a snapshot of the current state."""
    type: Literal[EventType.STATE_SNAPSHOT]
    state: Dict[str, Any]


class StateDeltaEvent(BaseEvent):
    """Event containing a delta to apply to the current state."""
    type: Literal[EventType.STATE_DELTA]
    delta: List[Dict[str, Any]]  # JSON Patch format


class MessagesSnapshotEvent(BaseEvent):
    """Event containing a snapshot of all messages."""
    type: Literal[EventType.MESSAGES_SNAPSHOT]
    messages: List[Message]


class CustomEvent(BaseEvent):
    """Custom event with arbitrary data."""
    type: Literal[EventType.CUSTOM]
    name: str
    data: Any


class RunAgentInput(BaseModel):
    """Input schema for running an AG-UI agent."""
    messages: List[Message]
    metadata: Optional[Dict[str, Any]] = None
    stream: bool = True


class RunAgentOutput(BaseModel):
    """Output schema for non-streaming AG-UI agent responses."""
    task_id: str
    messages: List[Message]
    metadata: Optional[Dict[str, Any]] = None


# Union type for all possible events
AgentEvent = Annotated[
    Union[
        TextMessageStartEvent,
        TextMessageContentEvent,
        TextMessageEndEvent,
        RunStartedEvent,
        RunFinishedEvent,
        RunErrorEvent,
        ToolCallStartEvent,
        ToolCallArgsEvent,
        ToolCallEndEvent,
        StateSnapshotEvent,
        StateDeltaEvent,
        MessagesSnapshotEvent,
        CustomEvent,
    ],
    Field(discriminator="type")
]
