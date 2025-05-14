"""Pydantic schemas for Model Context Protocol (MCP)."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any

class MCPMessage(BaseModel):
    """Schema for MCP messages."""
    protocol: str = Field(default="MCP", description="Protocol name.")
    version: str = Field(default="1.0.0", description="Protocol version.")
    message_id: str = Field(..., description="Unique identifier for the message.")
    capabilities: List[str] = Field(..., description="List of supported capabilities.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload.")
