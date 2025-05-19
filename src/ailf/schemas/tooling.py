"""Pydantic schemas for ailf.tooling."""
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, Field
import uuid

class ToolInputSchema(BaseModel):
    """Base model for a tool's input schema. Tools should define their own specific Pydantic models inheriting from this or BaseModel."""
    # Example: query: str
    # Example: items: List[Any]
    pass

class ToolOutputSchema(BaseModel):
    """Base model for a tool's output schema. Tools should define their own specific Pydantic models inheriting from this or BaseModel."""
    # Example: result: str
    # Example: success: bool
    pass

class ToolDescription(BaseModel):
    """Enhanced description for a tool, including detailed metadata."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the tool.")
    name: str = Field(description="Unique name of the tool.")
    description: str = Field(description="Detailed description of what the tool does and its purpose.")
    categories: List[str] = Field(default_factory=list, description="Categories the tool belongs to (e.g., 'data_analysis', 'text_generation').")
    keywords: List[str] = Field(default_factory=list, description="Keywords for searching and discovering the tool.")
    usage_examples: List[str] = Field(default_factory=list, description="Plain language examples of how to use the tool or what queries it can answer.")
    
    input_schema_ref: Optional[str] = Field(
        default=None, 
        description="Fully qualified string reference to the Pydantic model for the tool's input (e.g., 'my_module.schemas.MyToolInput')."
    )
    output_schema_ref: Optional[str] = Field(
        default=None, 
        description="Fully qualified string reference to the Pydantic model for the tool's output (e.g., 'my_module.schemas.MyToolOutput')."
    )
    
    version: str = Field(default="1.0.0", description="Tool version for compatibility tracking.")
    author: Optional[str] = Field(default=None, description="Author or team responsible for the tool.")
    deprecated: bool = Field(default=False, description="Whether this tool is deprecated.")
    deprecation_reason: Optional[str] = Field(default=None, description="If deprecated, explains why and suggests alternatives.")
    
    class Config:
        """Configuration for the ToolDescription model."""
        frozen = False  # Allow modification

class ToolUsageMetadata(BaseModel):
    """Metadata about tool usage for tracking and analytics."""
    tool_id: str = Field(description="ID of the tool that was executed.")
    tool_name: str = Field(description="Name of the tool that was executed.")
    timestamp: str = Field(description="ISO format timestamp of when the tool was executed.")
    execution_time_ms: float = Field(description="Execution time in milliseconds.")
    success: bool = Field(description="Whether the tool execution was successful.")
    error_message: Optional[str] = Field(default=None, description="Error message if the tool execution failed.")
    input_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of the inputs provided.")
    output_summary: Optional[Dict[str, Any]] = Field(default=None, description="Summary of the outputs returned.")
    
    # Additional tracking fields
    user_id: Optional[str] = Field(default=None, description="ID of the user who executed the tool.")
    session_id: Optional[str] = Field(default=None, description="ID of the session in which the tool was executed.")
    request_id: Optional[str] = Field(default=None, description="ID of the request that triggered the tool execution.")
    agent_id: Optional[str] = Field(default=None, description="ID of the agent that executed the tool.")

class ToolRegistryEntry(BaseModel):
    """Entry in the tool registry. Internal model for ailf.tooling.manager."""
    description: ToolDescription
    callable_ref: str = Field(description="Reference to the actual callable function/method.")
    enabled: bool = Field(default=True, description="Whether this tool is enabled.")
    usage_count: int = Field(default=0, description="Number of times this tool has been used.")
    last_used: Optional[str] = Field(default=None, description="ISO format timestamp when the tool was last used.")
