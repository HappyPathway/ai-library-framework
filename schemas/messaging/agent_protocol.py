"""
Agent Protocol schemas for client-server interaction.

This module defines Pydantic models based on the LangChain Agent Protocol specification, 
providing type safety and validation for Agent Protocol interactions.

References:
    - Agent Protocol Specification: https://github.com/langchain-ai/agent-protocol
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, HttpUrl


class TaskRequestBody(BaseModel):
    """Request body for creating a new task."""
    
    input: Union[str, dict] = Field(
        ...,
        description="The input content for the task, can be a string or a structured object"
    )
    additional_input: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional parameters for the agent"
    )


class StepRequestBody(BaseModel):
    """Request body for executing a step within a task."""
    
    input: Optional[Union[str, dict]] = Field(
        default=None,
        description="Input for this specific step"
    )
    additional_input: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional parameters for this step"
    )


class ArtifactType(str, Enum):
    """Types of artifacts that can be generated."""
    
    IMAGE = "image"
    TEXT = "text"
    FILE = "file"
    LINK = "link"


class Artifact(BaseModel):
    """An artifact produced during task execution."""
    
    artifact_id: str = Field(..., description="Unique identifier for the artifact")
    type: ArtifactType = Field(..., description="Type of the artifact")
    data: Any = Field(..., description="The artifact data or content")
    media_type: Optional[str] = Field(
        default=None, 
        description="MIME type of the artifact content"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the artifact was created"
    )


class TaskStatus(str, Enum):
    """Possible states of a task."""
    
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Possible states of an execution step."""
    
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Step(BaseModel):
    """A single execution step within a task."""
    
    step_id: str = Field(..., description="Unique identifier for this step")
    task_id: str = Field(..., description="ID of the parent task")
    status: StepStatus = Field(default=StepStatus.CREATED, description="Current status of the step")
    input: Optional[Union[str, dict]] = Field(
        default=None, 
        description="Input provided for this step"
    )
    output: Optional[Union[str, dict]] = Field(
        default=None,
        description="Output produced by this step"
    )
    additional_input: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional parameters provided for this step"
    )
    artifacts: List[Artifact] = Field(
        default_factory=list,
        description="Artifacts produced during this step"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the step was created"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the step was completed"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the step failed"
    )


class Task(BaseModel):
    """A task to be performed by an agent."""
    
    task_id: str = Field(..., description="Unique identifier for the task")
    status: TaskStatus = Field(default=TaskStatus.CREATED, description="Current status of the task")
    input: Union[str, dict] = Field(..., description="Input content for the task")
    additional_input: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional parameters for the agent"
    )
    steps: List[Step] = Field(
        default_factory=list,
        description="List of execution steps for this task"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, 
        description="Timestamp when the task was created"
    )
    completed_at: Optional[datetime] = Field(
        default=None, 
        description="Timestamp when the task was completed"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the task failed"
    )


class ListTasksResponse(BaseModel):
    """Response model for listing tasks."""
    
    tasks: List[Task] = Field(..., description="List of tasks")


class ArtifactUploadRequest(BaseModel):
    """Request for uploading an artifact."""
    
    file_name: str = Field(..., description="Name of the file being uploaded")
    content_type: str = Field(..., description="MIME type of the file")
    artifact_type: ArtifactType = Field(
        default=ArtifactType.FILE,
        description="Type of artifact being uploaded"
    )


class ArtifactUploadResponse(BaseModel):
    """Response for an artifact upload."""
    
    artifact_id: str = Field(..., description="ID of the uploaded artifact")
    artifact: Artifact = Field(..., description="The uploaded artifact details")
