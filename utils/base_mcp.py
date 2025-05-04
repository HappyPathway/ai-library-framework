"""MCP Server Base Module.

This module provides a base implementation of Model Context Protocol (MCP) server
functionality for building AI agent interfaces with tools, resources, and prompts.

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
    Basic usage registering a tool:
        >>> from utils.base_mcp import BaseMCP
        >>> 
        >>> mcp = BaseMCP(name="MyAssistant")
        >>> 
        >>> @mcp.tool()
        ... def add(a: int, b: int) -> int:
        ...     \"\"\"Add two numbers together.\"\"\"
        ...     return a + b

    Using resource templates and context:
        >>> from utils.base_mcp import BaseMCP, Context
        >>> 
        >>> mcp = BaseMCP(name="DataServer")
        >>> 
        >>> @mcp.resource("data://{dataset}/stats")
        ... def get_dataset_stats(dataset: str) -> dict:
        ...     \"\"\"Get statistics for a dataset.\"\"\"
        ...     return {"dataset": dataset, "count": 100}
        >>> 
        >>> @mcp.tool()
        ... async def analyze_data(ctx: Context, query: str) -> dict:
        ...     \"\"\"Analyze data based on query.\"\"\"
        ...     await ctx.info(f"Processing query: {query}")
        ...     return {"result": "Analysis complete"}
"""
import asyncio
import inspect
import logging
from contextlib import asynccontextmanager
from enum import Enum
from functools import wraps
from typing import (Any, AsyncIterator, Callable, Dict, List, Literal,
                    Optional, Set, Type, TypeVar, Union, get_type_hints,
                    overload)

from pydantic import BaseModel, ConfigDict, Field, create_model

from .schemas.mcp import (DuplicateHandling, MCPSettings, PromptMetadata,
                          ResourceMetadata, ToolAnnotations, ToolMetadata)

# Configure module logger
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')
R = TypeVar('R')


class Context:
    """Context object for MCP operations.

    This class provides access to request context and utility functions
    within tool, resource, and prompt implementations.

    Attributes:
        request_id: Unique identifier for the current request
        client_id: Identifier for the client making the request
        server: Reference to the server handling the request

    Methods:
        info: Log an informational message
        warning: Log a warning message
        error: Log an error message
        debug: Log a debug message
        report_progress: Report progress for long-running operations
        read_resource: Read the contents of a resource
        error: Create and raise an MCP protocol error
    """

    def __init__(self, request_id: str, client_id: Optional[str] = None):
        """Initialize context with request and client identifiers.

        Args:
            request_id: Unique identifier for the request
            client_id: Optional identifier for the client
        """
        self.request_id = request_id
        self.client_id = client_id
        self.server = None

    async def info(self, message: str) -> None:
        """Log an informational message.

        Args:
            message: The message to log
        """
        logger.info(f"[{self.request_id}] {message}")

    async def warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message: The warning message to log
        """
        logger.warning(f"[{self.request_id}] {message}")

    async def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: The error message to log
        """
        logger.error(f"[{self.request_id}] {message}")

    async def debug(self, message: str) -> None:
        """Log a debug message.

        Args:
            message: The debug message to log
        """
        logger.debug(f"[{self.request_id}] {message}")

    async def report_progress(self, progress: int, total: int) -> None:
        """Report progress for a long-running operation.

        Args:
            progress: Current progress value
            total: Total expected value representing completion
        """
        if not (0 <= progress <= total):
            await self.warning(f"Progress value {progress} out of range [0, {total}]")

        percentage = int(100 * progress / total) if total > 0 else 0
        await self.info(f"Progress: {progress}/{total} ({percentage}%)")

    async def read_resource(self, uri: str) -> Optional[List[Dict[str, Any]]]:
        """Read the contents of a resource.

        Args:
            uri: The URI of the resource to read

        Returns:
            Resource contents if found, None otherwise
        """
        # In a real implementation, this would access the resource system
        await self.debug(f"Reading resource: {uri}")
        return None

    def create_error(self, message: str, code: str = "tool_error") -> Exception:
        """Create an MCP protocol error.

        Args:
            message: Human-readable error message
            code: Error code for programmatic handling

        Returns:
            Exception object that can be raised
        """
        return Exception(f"[{code}] {message}")


class Tool:
    """Container for tool metadata and implementation.

    Attributes:
        name: Name of the tool
        description: Description of the tool's functionality
        func: The function implementing the tool
        tags: Set of tags for categorizing the tool
        annotations: Optional annotations for client applications
    """

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        annotations: Optional[Dict[str, Any]] = None
    ):
        """Initialize a tool with its metadata and implementation function.

        Args:
            func: The function implementing the tool
            name: Optional name override (defaults to function name)
            description: Optional description (defaults to function docstring)
            tags: Optional set of tags for categorization
            annotations: Optional annotations for client applications
        """
        self.func = func
        self.name = name or func.__name__
        self.description = description or inspect.getdoc(func) or ""
        self.tags = tags or set()
        self.annotations = annotations or {}

        # Extract schema information from function signature
        self.signature = inspect.signature(func)
        self.type_hints = get_type_hints(func)

    async def __call__(self, *args, **kwargs):
        """Execute the tool function with the provided arguments.

        Returns:
            The result of the tool function
        """
        if inspect.iscoroutinefunction(self.func):
            return await self.func(*args, **kwargs)
        else:
            return self.func(*args, **kwargs)

    def get_metadata(self) -> ToolMetadata:
        """Get the tool's metadata.

        Returns:
            ToolMetadata object containing the tool's metadata
        """
        return ToolMetadata(
            name=self.name,
            description=self.description,
            tags=list(self.tags),
            annotations=self.annotations
        )


class Resource:
    """Container for resource metadata and implementation.

    Attributes:
        uri: URI of the resource
        description: Description of the resource's contents
        func: The function implementing the resource
        tags: Set of tags for categorizing the resource
    """

    def __init__(
        self,
        uri: str,
        func: Callable,
        description: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ):
        """Initialize a resource with its metadata and implementation function.

        Args:
            uri: The URI of the resource
            func: The function implementing the resource
            description: Optional description (defaults to function docstring)
            tags: Optional set of tags for categorization
        """
        self.uri = uri
        self.func = func
        self.description = description or inspect.getdoc(func) or ""
        self.tags = tags or set()

        # Track if this is a template resource
        self.is_template = '{' in uri and '}' in uri

        # Extract parameters from URI template if applicable
        self.parameters = []
        if self.is_template:
            # Simple parameter extraction, a real implementation would use a proper template parser
            parts = uri.split('{')
            for part in parts[1:]:
                if '}' in part:
                    param = part.split('}')[0]
                    self.parameters.append(param)

    async def __call__(self, *args, **kwargs):
        """Execute the resource function with the provided arguments.

        Returns:
            The result of the resource function
        """
        if inspect.iscoroutinefunction(self.func):
            return await self.func(*args, **kwargs)
        else:
            return self.func(*args, **kwargs)

    def get_metadata(self) -> ResourceMetadata:
        """Get the resource's metadata.

        Returns:
            ResourceMetadata object containing the resource's metadata
        """
        return ResourceMetadata(
            uri=self.uri,
            description=self.description,
            tags=list(self.tags),
            is_template=self.is_template,
            parameters=self.parameters
        )


class Prompt:
    """Container for prompt metadata and implementation.

    Attributes:
        name: Name of the prompt
        description: Description of the prompt's purpose
        func: The function implementing the prompt
        tags: Set of tags for categorizing the prompt
    """

    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ):
        """Initialize a prompt with its metadata and implementation function.

        Args:
            func: The function implementing the prompt
            name: Optional name override (defaults to function name)
            description: Optional description (defaults to function docstring)
            tags: Optional set of tags for categorization
        """
        self.func = func
        self.name = name or func.__name__
        self.description = description or inspect.getdoc(func) or ""
        self.tags = tags or set()

        # Extract schema information from function signature
        self.signature = inspect.signature(func)
        self.type_hints = get_type_hints(func)

    async def __call__(self, *args, **kwargs):
        """Execute the prompt function with the provided arguments.

        Returns:
            The result of the prompt function, typically a message or list of messages
        """
        if inspect.iscoroutinefunction(self.func):
            return await self.func(*args, **kwargs)
        else:
            return self.func(*args, **kwargs)

    def get_metadata(self) -> PromptMetadata:
        """Get the prompt's metadata.

        Returns:
            PromptMetadata object containing the prompt's metadata
        """
        return PromptMetadata(
            name=self.name,
            description=self.description,
            tags=list(self.tags)
        )


class BaseMCP:
    """Base class for implementing MCP server capabilities.

    This class provides the core functionality for registering and managing
    tools, resources, and prompts for MCP-based AI agents.

    Attributes:
        name: Human-readable name of the server
        instructions: Instructions for interacting with this server
        settings: Configuration settings for the server
        state: Dictionary for storing server state
    """

    def __init__(
        self,
        name: str = "MCP Server",
        instructions: str = "",
        lifespan: Optional[Callable] = None,
        **settings
    ):
        """Initialize an MCP server with the given configuration.

        Args:
            name: Human-readable name for the server
            instructions: Instructions for interacting with this server
            lifespan: Optional async context manager for server lifecycle
            **settings: Additional settings for server configuration
        """
        self.name = name
        self.instructions = instructions
        self.lifespan = lifespan
        self.settings = MCPSettings(**settings)

        # Component containers
        self._tools: Dict[str, Tool] = {}
        self._resources: Dict[str, Resource] = {}
        self._prompts: Dict[str, Prompt] = {}

        # Server state storage
        self.state = {}

        logger.info(f"Initialized {self.name} MCP server")

    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        annotations: Optional[Dict[str, Any]] = None
    ):
        """Register a function as a tool.

        Args:
            name: Optional name override (defaults to function name)
            description: Optional description (defaults to function docstring)
            tags: Optional set of tags for categorization
            annotations: Optional annotations for client applications

        Returns:
            Decorator function that registers the decorated function as a tool
        """
        def decorator(func):
            tool_name = name or func.__name__

            # Check for duplicate tools
            if tool_name in self._tools:
                self._handle_duplicate(
                    "tool",
                    tool_name,
                    self.settings.on_duplicate_tools
                )

            # Register the tool
            self._tools[tool_name] = Tool(
                func=func,
                name=tool_name,
                description=description,
                tags=tags,
                annotations=annotations
            )

            logger.debug(f"Registered tool: {tool_name}")
            return func

        return decorator

    def resource(
        self,
        uri: str,
        description: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ):
        """Register a function as a resource.

        Args:
            uri: The URI for accessing this resource
            description: Optional description (defaults to function docstring)
            tags: Optional set of tags for categorization

        Returns:
            Decorator function that registers the decorated function as a resource
        """
        def decorator(func):
            # Check for duplicate resources
            if uri in self._resources:
                self._handle_duplicate(
                    "resource",
                    uri,
                    self.settings.on_duplicate_resources
                )

            # Register the resource
            self._resources[uri] = Resource(
                uri=uri,
                func=func,
                description=description,
                tags=tags
            )

            is_template = '{' in uri and '}' in uri
            resource_type = "resource template" if is_template else "resource"
            logger.debug(f"Registered {resource_type}: {uri}")
            return func

        return decorator

    def prompt(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ):
        """Register a function as a prompt.

        Args:
            name: Optional name override (defaults to function name)
            description: Optional description (defaults to function docstring)
            tags: Optional set of tags for categorization

        Returns:
            Decorator function that registers the decorated function as a prompt
        """
        def decorator(func):
            prompt_name = name or func.__name__

            # Check for duplicate prompts
            if prompt_name in self._prompts:
                self._handle_duplicate(
                    "prompt",
                    prompt_name,
                    self.settings.on_duplicate_prompts
                )

            # Register the prompt
            self._prompts[prompt_name] = Prompt(
                func=func,
                name=prompt_name,
                description=description,
                tags=tags
            )

            logger.debug(f"Registered prompt: {prompt_name}")
            return func

        return decorator

    def _handle_duplicate(
        self,
        component_type: str,
        name: str,
        behavior: DuplicateHandling
    ) -> bool:
        """Handle duplicate component registration based on configured behavior.

        Args:
            component_type: Type of the component ('tool', 'resource', 'prompt')
            name: Name of the component
            behavior: Configured behavior for handling duplicates

        Returns:
            True if the registration should proceed, False otherwise

        Raises:
            ValueError: If behavior is 'error' and a duplicate is detected
        """
        if behavior == DuplicateHandling.ERROR:
            raise ValueError(
                f"Duplicate {component_type} '{name}' detected with "
                f"on_duplicate_{component_type}s='error'"
            )
        elif behavior == DuplicateHandling.WARN:
            logger.warning(
                f"Duplicate {component_type} '{name}' detected. "
                f"Replacing existing {component_type}."
            )
            return True
        elif behavior == DuplicateHandling.REPLACE:
            # Silently replace
            return True
        elif behavior == DuplicateHandling.IGNORE:
            logger.debug(
                f"Duplicate {component_type} '{name}' detected. "
                f"Keeping existing {component_type}."
            )
            return False

        return True

    async def get_tools(self) -> Dict[str, Tool]:
        """Get all registered tools.

        Returns:
            Dictionary mapping tool names to Tool objects
        """
        return self._tools

    async def get_resources(self) -> Dict[str, Resource]:
        """Get all registered resources.

        Returns:
            Dictionary mapping resource URIs to Resource objects
        """
        return self._resources

    async def get_prompts(self) -> Dict[str, Prompt]:
        """Get all registered prompts.

        Returns:
            Dictionary mapping prompt names to Prompt objects
        """
        return self._prompts

    async def import_server(
        self,
        prefix: str,
        server: 'BaseMCP',
        tool_separator: str = "_",
        resource_separator: str = "+",
        prompt_separator: str = "_"
    ):
        """Import components from another server with a prefix.

        This performs a one-time copy of all components from the source server
        into this server, prefixing their names/URIs to avoid conflicts.

        Args:
            prefix: The prefix to add to imported component names/URIs
            server: The server to import components from
            tool_separator: Separator between prefix and tool name
            resource_separator: Separator between prefix and resource URI
            prompt_separator: Separator between prefix and prompt name
        """
        # Import tools
        source_tools = await server.get_tools()
        for tool_name, tool in source_tools.items():
            prefixed_name = f"{prefix}{tool_separator}{tool_name}"

            # Skip if duplicate and behavior is ignore
            if prefixed_name in self._tools and \
               self.settings.on_duplicate_tools == DuplicateHandling.IGNORE:
                continue

            # Import the tool with prefixed name
            self._tools[prefixed_name] = Tool(
                func=tool.func,
                name=prefixed_name,
                description=tool.description,
                tags=tool.tags,
                annotations=tool.annotations
            )
            logger.debug(f"Imported tool: {tool_name} as {prefixed_name}")

        # Import resources
        source_resources = await server.get_resources()
        for uri, resource in source_resources.items():
            prefixed_uri = f"{prefix}{resource_separator}{uri}"

            # Skip if duplicate and behavior is ignore
            if prefixed_uri in self._resources and \
               self.settings.on_duplicate_resources == DuplicateHandling.IGNORE:
                continue

            # Import the resource with prefixed URI
            self._resources[prefixed_uri] = Resource(
                uri=prefixed_uri,
                func=resource.func,
                description=resource.description,
                tags=resource.tags
            )

            resource_type = "resource template" if resource.is_template else "resource"
            logger.debug(f"Imported {resource_type}: {uri} as {prefixed_uri}")

        # Import prompts
        source_prompts = await server.get_prompts()
        for prompt_name, prompt in source_prompts.items():
            prefixed_name = f"{prefix}{prompt_separator}{prompt_name}"

            # Skip if duplicate and behavior is ignore
            if prefixed_name in self._prompts and \
               self.settings.on_duplicate_prompts == DuplicateHandling.IGNORE:
                continue

            # Import the prompt with prefixed name
            self._prompts[prefixed_name] = Prompt(
                func=prompt.func,
                name=prefixed_name,
                description=prompt.description,
                tags=prompt.tags
            )
            logger.debug(f"Imported prompt: {prompt_name} as {prefixed_name}")

    def mount(
        self,
        prefix: str,
        server: 'BaseMCP',
        tool_separator: str = "_",
        resource_separator: str = "+",
        prompt_separator: str = "_",
        as_proxy: Optional[bool] = None
    ):
        """Mount another server under this server with a prefix.

        This creates a live link where requests matching the prefix
        are delegated to the mounted server.

        Args:
            prefix: The prefix to identify the mounted server components
            server: The server to mount
            tool_separator: Separator between prefix and tool name
            resource_separator: Separator between prefix and resource URI
            prompt_separator: Separator between prefix and prompt name
            as_proxy: Whether to use proxy mounting (True) or direct mounting (False)
                     If None, will use proxy mounting if server has a custom lifespan
        """
        # In a real implementation, this would set up the delegation logic
        # For our base implementation, we'll just log that mounting would occur
        use_proxy = as_proxy if as_proxy is not None else (
            server.lifespan is not None)
        mount_type = "proxy" if use_proxy else "direct"
        logger.info(
            f"Mounting server '{server.name}' under prefix '{prefix}' "
            f"using {mount_type} mounting"
        )

    def run(
        self,
        transport: str = "stdio",
        **transport_kwargs
    ):
        """Run the server with the specified transport.

        This is a synchronous entry point that delegates to the appropriate
        transport-specific run method.

        Args:
            transport: Type of transport to use ("stdio" or "sse")
            **transport_kwargs: Additional arguments for the transport
        """
        if transport == "stdio":
            # In a real implementation, this would run the stdio transport
            logger.info(f"Running {self.name} with stdio transport")
        elif transport == "sse":
            # In a real implementation, this would run the SSE transport
            host = transport_kwargs.get("host", "0.0.0.0")
            port = transport_kwargs.get("port", 8000)
            logger.info(
                f"Running {self.name} with SSE transport on {host}:{port}")
        else:
            logger.error(f"Unknown transport: {transport}")
            raise ValueError(f"Unknown transport: {transport}")

    async def run_stdio_async(self, **kwargs):
        """Run the server with stdio transport asynchronously.

        Args:
            **kwargs: Additional arguments for the stdio transport
        """
        logger.info(f"Running {self.name} with stdio transport (async)")
        # In a real implementation, this would handle stdin/stdout communication

    async def run_sse_async(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        log_level: str = "INFO",
        **kwargs
    ):
        """Run the server with SSE transport asynchronously.

        Args:
            host: Host to bind to
            port: Port to bind to
            log_level: Logging level
            **kwargs: Additional arguments for the SSE transport
        """
        logger.info(
            f"Running {self.name} with SSE transport on {host}:{port} (async)")
        # In a real implementation, this would start an HTTP server with SSE endpoints
