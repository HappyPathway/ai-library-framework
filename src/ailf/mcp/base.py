"""MCP Server Base Implementation.

This module provides the foundation for building Model Context Protocol (MCP) servers
with tools, resources, prompts, and other components needed for AI agents.

Key Components:
    BaseMCP: Base class for implementing MCP server capabilities
    MCPSettings: Configuration model for MCP server settings
    Tool: Decorator and container class for tool functionality
    Resource: Decorator and container class for resource functionality
    Prompt: Decorator and container class for prompt functionality
    Context: Class for handling request context in tools and prompts

Features:
    - Tool registration with automatic schema generation
    - Resource and resource template registration
    - Prompt registration with parameterization
    - Context-aware request handling
    - Component composition via importing and mounting
    - Secure authentication support

Example:
    >>> from ailf.mcp.base import BaseMCP, Tool
    >>> 
    >>> # Create a simple MCP server
    >>> server = BaseMCP(
    ...     name="Example Server",
    ...     instructions="This is an example MCP server"
    ... )
    >>> 
    >>> # Register a tool
    >>> @server.tool()
    ... async def hello(name: str) -> str:
    ...     return f"Hello, {name}!"
    >>> 
    >>> # Start the server
    >>> if __name__ == "__main__":
    ...     import uvicorn
    ...     uvicorn.run(server.app, host="0.0.0.0", port=8000)
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, Set, AsyncGenerator
from pydantic import BaseModel, Field
import inspect
import json
import logging
import asyncio
from uuid import uuid4

# Setup logging
from ailf.core.logging import setup_logging

logger = setup_logging("mcp")

class MCPError(Exception):
    """Base exception for MCP errors."""
    
    def __init__(self, message: str, status_code: int = 500):
        self.status_code = status_code
        super().__init__(message)


class ToolError(MCPError):
    """Exception for tool execution errors."""
    
    def __init__(self, message: str, status_code: int = 500, tool_name: Optional[str] = None):
        self.tool_name = tool_name
        super().__init__(message, status_code)


class ResourceError(MCPError):
    """Exception for resource errors."""
    
    def __init__(self, message: str, status_code: int = 404, resource_id: Optional[str] = None):
        self.resource_id = resource_id
        super().__init__(message, status_code)


class AuthError(MCPError):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)


class Context:
    """Request context for tool and resource handling.
    
    This object is passed to tools and resource handlers, providing
    access to the request context and helper methods.
    """
    
    def __init__(self, server: 'BaseMCP', request_id: str):
        self.server = server
        self.request_id = request_id
        self.state: Dict[str, Any] = {}
        
    def error(self, message: str, code: Union[int, str] = 500) -> ToolError:
        """Create a ToolError with the given message and code.
        
        Args:
            message: Error message
            code: Error code, can be an HTTP status code or a string identifier
            
        Returns:
            ToolError instance that can be raised
        """
        if isinstance(code, str):
            # Map string code to status code if needed
            status_code = 500
        else:
            status_code = code
        
        return ToolError(message, status_code)


class ToolType(str, Enum):
    """Type of tool for classification."""
    FUNCTION = "function"
    AGENT = "agent"


class Tool:
    """Tool registration and metadata container."""
    
    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tool_type: ToolType = ToolType.FUNCTION
    ):
        """Initialize a tool.
        
        Args:
            func: The function implementing the tool
            name: Optional custom name for the tool
            description: Optional description (defaults to function docstring)
            tool_type: Type of tool (function or agent)
        """
        self.func = func
        self.name = name or func.__name__
        self.description = description or (func.__doc__ or "").strip()
        self.tool_type = tool_type
        self.schema = self._generate_schema()
        
    def _generate_schema(self) -> Dict[str, Any]:
        """Generate JSON Schema for this tool.
        
        Returns:
            JSON Schema as a dictionary
        """
        parameters = {}
        signature = inspect.signature(self.func)
        
        for name, param in signature.parameters.items():
            # Skip context parameter
            if name == "ctx" or name == "context":
                continue
                
            # Get parameter type annotation
            param_type = param.annotation
            if param_type is inspect.Parameter.empty:
                param_type = Any
                
            # TODO: Implement proper type conversion to JSON Schema
            # For now, just use a simple string representation
            parameters[name] = {
                "type": "string",  # Simplified for now
                "description": f"Parameter {name}"
            }
            
            if param.default is not inspect.Parameter.empty:
                parameters[name]["default"] = param.default
                
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": parameters
            }
        }
        
    async def __call__(self, ctx: Context, **kwargs) -> Any:
        """Execute the tool function.
        
        Args:
            ctx: Request context
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ToolError: If tool execution fails
        """
        try:
            # Check if function expects context
            sig = inspect.signature(self.func)
            if "ctx" in sig.parameters or "context" in sig.parameters:
                return await self.func(ctx, **kwargs)
            else:
                return await self.func(**kwargs)
        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {str(e)}")
            if isinstance(e, MCPError):
                raise
            raise ToolError(f"Tool execution failed: {str(e)}", tool_name=self.name)


class Resource:
    """Resource registration and metadata container."""
    
    def __init__(
        self,
        id: str,
        description: str,
        handler: Optional[Callable] = None,
        schema: Optional[Dict[str, Any]] = None
    ):
        """Initialize a resource.
        
        Args:
            id: Resource identifier
            description: Resource description
            handler: Optional function to handle resource access
            schema: Optional JSON Schema for the resource
        """
        self.id = id
        self.description = description
        self.handler = handler
        self.schema = schema or {}
        
    async def handle(self, ctx: Context, **kwargs) -> Any:
        """Handle resource access.
        
        Args:
            ctx: Request context
            **kwargs: Resource parameters
            
        Returns:
            Resource data
            
        Raises:
            ResourceError: If resource handling fails
        """
        if self.handler is None:
            raise ResourceError("Resource has no handler", resource_id=self.id)
            
        try:
            # Check if handler expects context
            sig = inspect.signature(self.handler)
            if "ctx" in sig.parameters or "context" in sig.parameters:
                return await self.handler(ctx, **kwargs)
            else:
                return await self.handler(**kwargs)
        except Exception as e:
            logger.error(f"Resource {self.id} handling failed: {str(e)}")
            if isinstance(e, MCPError):
                raise
            raise ResourceError(f"Resource handling failed: {str(e)}", resource_id=self.id)


class Prompt:
    """Prompt registration and metadata container."""
    
    def __init__(
        self,
        id: str,
        template: str,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """Initialize a prompt.
        
        Args:
            id: Prompt identifier
            template: Prompt template string
            description: Optional description
            parameters: Optional parameter definitions
        """
        self.id = id
        self.template = template
        self.description = description or "Prompt template"
        self.parameters = parameters or {}
        
    def format(self, **kwargs) -> str:
        """Format the prompt with the given parameters.
        
        Args:
            **kwargs: Parameters to inject into the prompt
            
        Returns:
            Formatted prompt string
        """
        return self.template.format(**kwargs)


class MCPSettings(BaseModel):
    """Configuration settings for an MCP server."""
    
    auth_enabled: bool = False
    auth_token: Optional[str] = None
    cors_origins: List[str] = Field(default_factory=list)
    debug: bool = False
    description: Optional[str] = None


class BaseMCP:
    """Base class for implementing MCP server functionality."""
    
    def __init__(
        self,
        name: str,
        instructions: str,
        settings: Optional[MCPSettings] = None
    ):
        """Initialize the MCP server.
        
        Args:
            name: Server name
            instructions: Server instructions
            settings: Optional configuration settings
        """
        self.name = name
        self.instructions = instructions
        self.settings = settings or MCPSettings()
        
        # Component registries
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, Resource] = {}
        self.prompts: Dict[str, Prompt] = {}
        
        # State
        self.state: Dict[str, Any] = {}
        
    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tool_type: ToolType = ToolType.FUNCTION
    ):
        """Decorator for registering tool functions.
        
        Args:
            name: Optional custom name for the tool
            description: Optional description (defaults to function docstring)
            tool_type: Type of tool (function or agent)
            
        Returns:
            Decorator function
        """
        def decorator(func):
            tool_name = name or func.__name__
            tool = Tool(func, name=tool_name, description=description, tool_type=tool_type)
            self.tools[tool_name] = tool
            return func
        return decorator
        
    def add_tool(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        """Add a tool function directly (non-decorator method).
        
        Args:
            func: Function implementing the tool
            name: Optional custom name for the tool
            description: Optional description
            
        Returns:
            The registered tool
        """
        tool_name = name or func.__name__
        tool = Tool(func, name=tool_name, description=description)
        self.tools[tool_name] = tool
        return tool
        
    def add_resource(
        self,
        id: str,
        description: str,
        handler: Optional[Callable] = None,
        schema: Optional[Dict[str, Any]] = None
    ):
        """Add a resource.
        
        Args:
            id: Resource identifier
            description: Resource description
            handler: Optional function to handle resource access
            schema: Optional JSON Schema for the resource
            
        Returns:
            The registered resource
        """
        resource = Resource(id, description, handler, schema)
        self.resources[id] = resource
        return resource
        
    def add_prompt(
        self,
        id: str,
        template: str,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """Add a prompt template.
        
        Args:
            id: Prompt identifier
            template: Prompt template string
            description: Optional description
            parameters: Optional parameter definitions
            
        Returns:
            The registered prompt
        """
        prompt = Prompt(id, template, description, parameters)
        self.prompts[id] = prompt
        return prompt
        
    def create_context(self, request_id: Optional[str] = None) -> Context:
        """Create a new request context.
        
        Args:
            request_id: Optional request ID (auto-generated if None)
            
        Returns:
            New Context instance
        """
        request_id = request_id or str(uuid4())
        return Context(self, request_id)
        
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information.
        
        Returns:
            Server metadata dictionary
        """
        return {
            "name": self.name,
            "instructions": self.instructions,
            "tools": [tool.schema for tool in self.tools.values()],
            "resources": {id: res.description for id, res in self.resources.items()},
            "prompts": {id: prompt.description for id, prompt in self.prompts.items()}
        }
        
    async def execute_tool(self, tool_name: str, context: Context, **params) -> Any:
        """Execute a tool function.
        
        Args:
            tool_name: Name of the tool to execute
            context: Request context
            **params: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ToolError: If tool is not found or execution fails
        """
        if tool_name not in self.tools:
            raise ToolError(f"Tool '{tool_name}' not found", 404, tool_name)
            
        tool = self.tools[tool_name]
        return await tool(context, **params)
