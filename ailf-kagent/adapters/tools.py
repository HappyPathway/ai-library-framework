"""
Tool adapter for using AILF tools with Kagent.

This module provides adapter classes that allow AILF tools to be used within
the Kagent framework, translating between the two frameworks' tool interfaces.
"""

from typing import Any, Dict, List, Optional, Type, Callable
from pydantic import BaseModel, Field
import kagent.tools
from ailf.tooling import ToolDescription, ToolManager


class AILFToolAdapter(kagent.tools.BaseTool):
    """Adapter for using AILF tools within Kagent.
    
    This adapter wraps AILF tools so they can be used within the Kagent framework.
    It translates between Kagent's tool interface and AILF's tool interface.
    
    Attributes:
        ailf_tool: The AILF tool description to adapt
        ailf_tool_manager: The AILF tool manager for executing tools
        name: The name of the tool (derived from AILF tool id if not provided)
        description: The description of the tool (derived from AILF tool description)
    """
    
    def __init__(
        self, 
        ailf_tool: ToolDescription,
        name: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Initialize the AILF tool adapter.
        
        Args:
            ailf_tool: The AILF tool description to adapt
            name: Optional name override for the tool (defaults to AILF tool id)
            description: Optional description override (defaults to AILF tool description)
        """
        # Initialize the tool manager and register the AILF tool
        self.ailf_tool = ailf_tool
        self.ailf_tool_manager = ToolManager()
        self.ailf_tool_manager.register_tool(ailf_tool)
        
        # Use AILF tool properties if overrides not provided
        tool_name = name or ailf_tool.id
        tool_description = description or ailf_tool.description
        
        # Initialize the Kagent BaseTool with properties from AILF tool
        super().__init__(name=tool_name, description=tool_description)
    
    async def _run(self, **kwargs) -> Any:
        """Execute the AILF tool with the provided parameters.
        
        Args:
            **kwargs: Tool parameters matching the AILF tool's input schema
            
        Returns:
            The result of executing the AILF tool
            
        Raises:
            Exception: If the AILF tool execution fails
        """
        return await self.ailf_tool_manager.execute_tool(
            self.ailf_tool.id,
            kwargs
        )
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        """Get the schema for the tool's arguments.
        
        Returns:
            The AILF tool's input schema as a Pydantic model
        """
        return self.ailf_tool.input_schema


class AILFToolRegistry:
    """Registry for managing multiple AILF tools within Kagent.
    
    This registry manages a collection of AILF tools and makes them available
    as Kagent-compatible tools through adapters.
    
    Attributes:
        _tools: Dictionary mapping tool IDs to AILF tool adapters
    """
    
    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools = {}
        self._ailf_tool_manager = ToolManager()
    
    def register_tool(self, ailf_tool: ToolDescription) -> AILFToolAdapter:
        """Register an AILF tool and create a Kagent adapter for it.
        
        Args:
            ailf_tool: The AILF tool description to register
            
        Returns:
            The created AILFToolAdapter instance
            
        Raises:
            ValueError: If a tool with the same ID is already registered
        """
        if ailf_tool.id in self._tools:
            raise ValueError(f"Tool with ID '{ailf_tool.id}' is already registered")
            
        adapter = AILFToolAdapter(ailf_tool)
        self._tools[ailf_tool.id] = adapter
        return adapter
    
    def get_tool(self, tool_id: str) -> Optional[AILFToolAdapter]:
        """Get a registered tool by ID.
        
        Args:
            tool_id: The ID of the tool to retrieve
            
        Returns:
            The tool adapter if found, None otherwise
        """
        return self._tools.get(tool_id)
    
    def get_all_tools(self) -> List[AILFToolAdapter]:
        """Get all registered tools.
        
        Returns:
            List of all registered tool adapters
        """
        return list(self._tools.values())
    
    def register_ailf_tools(self, tool_ids: List[str] = None) -> List[AILFToolAdapter]:
        """Register multiple AILF tools by their IDs.
        
        Args:
            tool_ids: List of AILF tool IDs to register, or None to register all
            
        Returns:
            List of created adapter instances
            
        Raises:
            ValueError: If any of the specified tools are not found
        """
        adapters = []
        available_tools = self._ailf_tool_manager.list_tools()
        
        # If no specific tools requested, register all available ones
        if tool_ids is None:
            tool_ids = [tool.id for tool in available_tools]
        
        # Register each requested tool
        for tool_id in tool_ids:
            tool = next((t for t in available_tools if t.id == tool_id), None)
            if not tool:
                raise ValueError(f"AILF tool with ID '{tool_id}' not found")
            
            adapters.append(self.register_tool(tool))
        
        return adapters
