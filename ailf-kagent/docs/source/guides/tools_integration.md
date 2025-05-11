# Tools Integration

This guide explains how to use AILF tools within Kagent agents.

## Basic Tool Adapter

The `AILFToolAdapter` class allows AILF tools to be used within Kagent agents:

```python
from ailf.tooling import ToolDescription
from ailf_kagent import AILFToolAdapter
from kagent.agents import Agent as KAgent

# Create an AILF tool
calculator_tool = ToolDescription(
    id="calculator",
    description="Perform basic arithmetic operations",
    input_schema=CalculatorInput,
    output_schema=CalculatorOutput,
    function=calculate
)

# Adapt it for Kagent
kagent_tool = AILFToolAdapter(calculator_tool)

# Use it with a Kagent agent
agent = KAgent()
agent.add_tool(kagent_tool)
```

## Tool Registry

For managing multiple tools, you can use the `AILFToolRegistry`:

```python
from ailf.tooling import ToolDescription
from ailf_kagent import AILFToolRegistry
from kagent.agents import Agent as KAgent

# Create AILF tools
calculator_tool = ToolDescription(...)
weather_tool = ToolDescription(...)
search_tool = ToolDescription(...)

# Create a tool registry
registry = AILFToolRegistry()
registry.register(calculator_tool)
registry.register(weather_tool)
registry.register(search_tool)

# Add all tools to a Kagent agent
agent = KAgent()
registry.add_tools_to_agent(agent)
```

## Custom Tool Adapter

You can create a custom adapter by extending `AILFToolAdapter`:

```python
from ailf_kagent import AILFToolAdapter

class CustomToolAdapter(AILFToolAdapter):
    """Custom tool adapter with additional functionality."""
    
    async def __call__(self, **kwargs):
        """Override call method to add custom behavior."""
        print(f"Executing tool: {self.name}")
        
        # Add preprocessing logic
        processed_args = self._preprocess_arguments(kwargs)
        
        # Call the base implementation with processed arguments
        result = await super().__call__(**processed_args)
        
        # Add postprocessing logic
        processed_result = self._postprocess_result(result)
        
        return processed_result
        
    def _preprocess_arguments(self, args):
        """Custom argument preprocessing."""
        # Process arguments
        return args
        
    def _postprocess_result(self, result):
        """Custom result postprocessing."""
        # Process result
        return result
```

## Best Practices

1. **Schema Validation**: Ensure your AILF tools have well-defined Pydantic models
2. **Error Handling**: Add proper error handling to tool functions
3. **Documentation**: Provide clear descriptions for tools and parameters
4. **Reusability**: Design tools to be reusable across different agent types
5. **Testing**: Create comprehensive tests for tool functionality
