# Getting Started

This guide will walk you through the basics of using the AILF-Kagent integration.

## Basic Concepts

AILF-Kagent provides adapters that bridge between the AILF and Kagent frameworks:

1. **Tool Adapters**: Allow AILF tools to be used in Kagent agents
2. **Agent Adapters**: Enhance Kagent agents with AILF's cognitive capabilities
3. **Memory Adapters**: Share memory between AILF and Kagent components
4. **Schema Adapters**: Translate between AILF and Kagent schema formats

## Quick Example

Here's a simple example that demonstrates integrating an AILF tool with a Kagent agent:

```python
import asyncio
from typing import Dict
from pydantic import BaseModel, Field

# Import AILF components
from ailf.tooling import ToolDescription

# Import Kagent components
from kagent.agents import Agent as KAgent

# Import the integration adapter
from ailf_kagent import AILFToolAdapter


# Define a simple AILF tool input/output schemas
class CalculatorInput(BaseModel):
    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")
    operation: str = Field(..., description="Operation to perform")

class CalculatorOutput(BaseModel):
    result: float = Field(..., description="Result of the operation")

# Implement the tool function
async def calculate(input_data: CalculatorInput) -> CalculatorOutput:
    a, b = input_data.a, input_data.b
    
    if input_data.operation == "add":
        result = a + b
    elif input_data.operation == "subtract":
        result = a - b
    elif input_data.operation == "multiply":
        result = a * b
    elif input_data.operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
    else:
        raise ValueError(f"Unknown operation: {input_data.operation}")
        
    return CalculatorOutput(result=result)

# Create the AILF tool
calculator_tool = ToolDescription(
    id="calculator",
    description="Perform basic arithmetic operations",
    input_schema=CalculatorInput,
    output_schema=CalculatorOutput,
    function=calculate
)

# Adapt it for Kagent
kagent_calculator = AILFToolAdapter(calculator_tool)

# Create a Kagent agent and add the tool
agent = KAgent()
agent.add_tool(kagent_calculator)

# Use the agent
async def main():
    response = await agent.run("Calculate 5 + 3")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- Learn about the [Tool Integration](tools_integration.md) capabilities
- Explore [Agent Integration](agents_integration.md) features
- Understand how to use [Memory Integration](memory_integration.md)
- Work with [Schema Translation](schema_translation.md) utilities
