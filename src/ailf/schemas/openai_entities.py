"""OpenAI Assistants API entity schemas.

This module provides Pydantic models for OpenAI Assistants API entities.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field


class ToolFunction(BaseModel):
    """Function definition for an Assistant tool."""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class Tool(BaseModel):
    """Tool that can be used by an Assistant."""
    type: str
    function: Optional[ToolFunction] = None


class AssistantFile(BaseModel):
    """A file attached to an Assistant."""
    id: str
    object: str
    created_at: int
    assistant_id: str


class Assistant(BaseModel):
    """OpenAI Assistant entity."""
    id: str
    object: str = "assistant"
    created_at: int
    name: Optional[str] = None
    description: Optional[str] = None
    model: str
    instructions: Optional[str] = None
    tools: List[Tool] = Field(default_factory=list)
    file_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of the Assistant."""
        return f"Assistant(id={self.id}, name={self.name}, model={self.model})"


class ContentTextValue(BaseModel):
    """Text content value."""
    value: str


class ContentText(BaseModel):
    """Text content type."""
    type: str = "text"
    text: ContentTextValue


class ThreadMessage(BaseModel):
    """A message in a Thread."""
    id: str
    object: str = "thread.message"
    created_at: int
    thread_id: str
    role: str
    content: List[Dict[str, Any]]
    file_ids: List[str] = Field(default_factory=list)
    assistant_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    def get_content_text(self) -> str:
        """Extract text content from the message."""
        texts = []
        for item in self.content:
            if item.get("type") == "text":
                texts.append(item.get("text", {}).get("value", ""))
        return "\n".join(texts)


class Thread(BaseModel):
    """OpenAI Thread entity."""
    id: str
    object: str = "thread"
    created_at: int
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of the Thread."""
        return f"Thread(id={self.id})"


class RunStep(BaseModel):
    """A step in a Run execution."""
    id: str
    object: str = "thread.run.step"
    created_at: int
    run_id: str
    assistant_id: str
    thread_id: str
    type: str
    status: str
    step_details: Dict[str, Any]
    last_error: Optional[Dict[str, str]] = None
    expired_at: Optional[int] = None
    cancelled_at: Optional[int] = None
    failed_at: Optional[int] = None
    completed_at: Optional[int] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class Run(BaseModel):
    """OpenAI Run entity."""
    id: str
    object: str = "thread.run"
    created_at: int
    thread_id: str
    assistant_id: str
    status: str
    required_action: Optional[Dict[str, Any]] = None
    last_error: Optional[Dict[str, str]] = None
    expires_at: Optional[int] = None
    started_at: Optional[int] = None
    cancelled_at: Optional[int] = None
    failed_at: Optional[int] = None
    completed_at: Optional[int] = None
    model: str
    instructions: Optional[str] = None
    tools: List[Tool] = Field(default_factory=list)
    file_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, str] = Field(default_factory=dict)

    def __str__(self) -> str:
        """String representation of the Run."""
        return f"Run(id={self.id}, status={self.status})"


class File(BaseModel):
    """OpenAI File entity."""
    id: str
    object: str = "file"
    bytes: int
    created_at: int
    filename: str
    purpose: str
    status: str
    status_details: Optional[str] = None
