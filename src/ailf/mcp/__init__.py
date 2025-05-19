"""MCP package for Model Context Protocol implementations.

This package provides all the necessary components for building and running
Model Context Protocol (MCP) servers for AI agents.

Key Modules:
- base: Core MCP server implementation
- servers: Pre-built MCP server implementations
- schemas: Data models for MCP components

Example:
    >>> from ailf.mcp.base import BaseMCP
    >>> 
    >>> server = BaseMCP(
    ...     name="My MCP Server", 
    ...     instructions="This is an example server"
    ... )
"""

from ailf.mcp.base import BaseMCP, Tool, Resource, Context, ToolError
