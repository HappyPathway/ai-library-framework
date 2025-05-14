"""MCP Server Base Module.

DEPRECATED: This module has been moved to ailf.mcp.base.
Please update your imports to: from ailf.mcp.base import BaseMCP, Tool, Resource

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
import warnings

# Add deprecation warning
warnings.warn(
    "The utils.base_mcp module is deprecated. Use ailf.mcp.base instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all symbols from the new module location
from ailf.mcp.base import *
