"""
Unit tests for AILF-Kagent tool adapters.

These tests verify that AILF tools can be properly adapted for use within Kagent.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field

# Import AILF components
from ailf.tooling import ToolDescription

# Import adapter components
from ailf_kagent.adapters.tools import AILFToolAdapter, AILFToolRegistry


# Define test tool schema
class TestInput(BaseModel):
    """Test input schema"""
    text: str = Field(..., description="Input text")
    number: int = Field(default=0, description="Input number")


class TestOutput(BaseModel):
    """Test output schema"""
    result: str = Field(..., description="Result text")
    processed: bool = Field(default=True, description="Whether processing succeeded")


# Test tool function
async def test_tool_function(input_data: TestInput) -> TestOutput:
    """Test tool implementation"""
    result = f"Processed: {input_data.text} (number={input_data.number})"
    return TestOutput(result=result)


# Create test tool description
test_tool_desc = ToolDescription(
    id="test_tool",
    name="Test Tool",
    description="A test tool for unit testing",
    function=test_tool_function,
    input_schema=TestInput,
    output_schema=TestOutput
)


class TestAILFToolAdapter:
    """Test suite for AILFToolAdapter"""

    @pytest.fixture
    def tool_adapter(self):
        """Create a tool adapter for testing"""
        return AILFToolAdapter(test_tool_desc)

    def test_adapter_initialization(self, tool_adapter):
        """Test that the adapter initializes correctly"""
        # Check that properties are correctly set
        assert tool_adapter.ailf_tool == test_tool_desc
        assert tool_adapter.name == "test_tool"
        assert "test tool" in tool_adapter.description.lower()

    def test_args_schema(self, tool_adapter):
        """Test that the args schema is correctly derived from AILF tool"""
        schema = tool_adapter.args_schema
        assert schema == TestInput
        
        # Verify schema fields
        assert "text" in schema.model_fields
        assert "number" in schema.model_fields
        assert schema.model_fields["text"].description == "Input text"

    @pytest.mark.asyncio
    async def test_run_execution(self, tool_adapter):
        """Test that the adapter correctly executes the AILF tool"""
        result = await tool_adapter._run(text="Hello world", number=42)
        
        # Verify result structure
        assert isinstance(result, TestOutput)
        assert "Hello world" in result.result
        assert "42" in result.result
        assert result.processed is True

    @pytest.mark.asyncio
    async def test_run_with_missing_required_param(self, tool_adapter):
        """Test that the adapter handles missing required parameters"""
        with pytest.raises(Exception):
            # 'text' is required but missing
            await tool_adapter._run(number=10)


class TestAILFToolRegistry:
    """Test suite for AILFToolRegistry"""
    
    @pytest.fixture
    def tool_registry(self):
        """Create a tool registry for testing"""
        return AILFToolRegistry()
    
    def test_register_tool(self, tool_registry):
        """Test registering a tool with the registry"""
        adapter = tool_registry.register_tool(test_tool_desc)
        
        # Check the returned adapter
        assert isinstance(adapter, AILFToolAdapter)
        assert adapter.ailf_tool == test_tool_desc
        
        # Check that the tool is in the registry
        assert tool_registry.get_tool("test_tool") == adapter
    
    def test_register_duplicate_tool(self, tool_registry):
        """Test that registering a duplicate tool raises an error"""
        # Register once
        tool_registry.register_tool(test_tool_desc)
        
        # Second registration should fail
        with pytest.raises(ValueError):
            tool_registry.register_tool(test_tool_desc)
    
    def test_get_all_tools(self, tool_registry):
        """Test getting all registered tools"""
        # Create a second tool for testing
        second_tool = ToolDescription(
            id="second_tool",
            name="Second Test Tool",
            description="Another test tool",
            function=test_tool_function,
            input_schema=TestInput,
            output_schema=TestOutput
        )
        
        # Register both tools
        adapter1 = tool_registry.register_tool(test_tool_desc)
        adapter2 = tool_registry.register_tool(second_tool)
        
        # Get all tools
        all_tools = tool_registry.get_all_tools()
        
        # Verify results
        assert len(all_tools) == 2
        assert adapter1 in all_tools
        assert adapter2 in all_tools
