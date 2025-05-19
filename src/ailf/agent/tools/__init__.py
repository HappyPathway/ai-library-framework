"""
Agent Tool Integration.

This module provides mechanisms for integrating tools with agents, including:
- Tool registration and discovery
- Standard tool interfaces
- Tool execution with proper error handling
- Tool result processing

Tools are functions with standardized signatures that agents can use to interact
with external systems, retrieve information, or perform actions.
"""

import asyncio
import functools
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, cast

from pydantic import BaseModel, Field, create_model

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')
ToolFunc = Callable[..., Any]
AsyncToolFunc = Callable[..., Any]


class ToolDescription(BaseModel):
    """Description of a tool for agent use."""
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of the tool's purpose and usage")
    parameters: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Parameters accepted by the tool"
    )
    returns: Dict[str, Any] = Field(
        default_factory=dict,
        description="Description of the tool's return value"
    )
    is_async: bool = Field(default=False, description="Whether the tool is async")
    category: Optional[str] = Field(default=None, description="Tool category")


class ToolResult(BaseModel):
    """Result of a tool execution."""
    success: bool = Field(description="Whether the tool execution succeeded")
    result: Any = Field(description="Result value if successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")


def tool(name: Optional[str] = None, description: Optional[str] = None, category: Optional[str] = None):
    """Decorator to register a function as an agent tool.
    
    Args:
        name: Name of the tool (defaults to function name)
        description: Description of what the tool does
        category: Optional category for the tool
        
    Returns:
        The decorated function with tool metadata
    """
    def decorator(func: ToolFunc) -> ToolFunc:
        tool_name = name or func.__name__
        tool_description = description or inspect.getdoc(func) or "No description provided"
        
        # Extract parameter information from function signature
        sig = inspect.signature(func)
        parameters = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
                
            param_info = {
                "required": param.default is inspect.Parameter.empty,
                "type": str(param.annotation) if param.annotation is not inspect.Parameter.empty else "Any"
            }
            
            # Look for parameter description in docstring if available
            if func.__doc__:
                param_desc_pattern = f":param {param_name}:"
                if param_desc_pattern in func.__doc__:
                    param_desc = func.__doc__.split(param_desc_pattern)[1].split("\n")[0].strip()
                    param_info["description"] = param_desc
            
            parameters[param_name] = param_info
        
        # Get return type information
        return_info = {
            "type": str(sig.return_annotation) if sig.return_annotation is not inspect.Parameter.empty else "Any"
        }
        
        # Look for return description in docstring
        if func.__doc__ and ":return:" in func.__doc__:
            return_desc = func.__doc__.split(":return:")[1].split("\n")[0].strip()
            return_info["description"] = return_desc
        
        # Create tool description
        tool_meta = ToolDescription(
            name=tool_name,
            description=tool_description,
            parameters=parameters,
            returns=return_info,
            is_async=asyncio.iscoroutinefunction(func),
            category=category
        )
        
        # Attach metadata to function
        func._tool_meta = tool_meta  # type: ignore
        
        return func
    
    return decorator


class ToolRegistry:
    """Registry for agent tools."""
    
    def __init__(self):
        """Initialize an empty tool registry."""
        self.tools: Dict[str, ToolFunc] = {}
        self.descriptions: Dict[str, ToolDescription] = {}
    
    def register(
        self, 
        func: ToolFunc,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> ToolFunc:
        """Register a function as a tool.
        
        Args:
            func: The function to register
            name: Optional custom name
            description: Optional description
            category: Optional category
            
        Returns:
            The registered function
        """
        # Use the tool decorator to add metadata
        decorated_func = tool(name=name, description=description, category=category)(func)
        
        # Extract the tool metadata
        tool_meta = getattr(decorated_func, "_tool_meta", None)
        if not tool_meta:
            raise ValueError(f"Failed to register tool: {func.__name__}")
        
        # Register the tool
        self.tools[tool_meta.name] = decorated_func
        self.descriptions[tool_meta.name] = tool_meta
        
        logger.debug(f"Registered tool: {tool_meta.name}")
        return decorated_func
    
    def get(self, name: str) -> Optional[ToolFunc]:
        """Get a tool by name.
        
        Args:
            name: Name of the tool to retrieve
            
        Returns:
            Optional[ToolFunc]: The tool function if found, None otherwise
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[ToolDescription]:
        """List all registered tools.
        
        Returns:
            List[ToolDescription]: Descriptions of all registered tools
        """
        return list(self.descriptions.values())
    
    def get_by_category(self, category: str) -> List[ToolDescription]:
        """Get tools by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List[ToolDescription]: Tools in the specified category
        """
        return [
            desc for desc in self.descriptions.values() 
            if desc.category == category
        ]


async def execute_tool(
    tool_func: Union[ToolFunc, AsyncToolFunc], 
    **kwargs
) -> ToolResult:
    """Execute a tool function with proper error handling.
    
    Args:
        tool_func: The tool function to execute
        **kwargs: Arguments to pass to the tool
        
    Returns:
        ToolResult: Result of the tool execution
    """
    try:
        # Execute the tool function
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**kwargs)
        else:
            result = tool_func(**kwargs)
        
        return ToolResult(success=True, result=result)
    except Exception as e:
        logger.exception(f"Tool execution failed: {str(e)}")
        return ToolResult(success=False, error=str(e))


# Create a global registry instance
registry = ToolRegistry()
