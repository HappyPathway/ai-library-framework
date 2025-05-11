"""
Basic integration example showing how to use AILF tools with Kagent.

This example demonstrates the core functionality of the AILF-Kagent integration,
focusing on the basic tool adapter pattern.
"""

import asyncio
from typing import Dict, List

# Import Kagent components
from kagent.agents import Agent as KAgent

# Import AILF components
from ailf.tooling import ToolDescription, ToolManager
from pydantic import BaseModel, Field

# Import the integration adapters
from ailf_kagent.adapters.tools import AILFToolAdapter


# Define a simple AILF tool using Pydantic models
class CalculatorInput(BaseModel):
    """Input for the calculator tool"""
    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")
    operation: str = Field(..., description="Operation to perform (add, subtract, multiply, divide)")


class CalculatorOutput(BaseModel):
    """Output from the calculator tool"""
    result: float = Field(..., description="Result of the calculation")
    operation: str = Field(..., description="Operation performed")


# Create a function for the tool
async def calculator_tool(input_data: CalculatorInput) -> CalculatorOutput:
    """Perform a calculation based on the input"""
    a = input_data.a
    b = input_data.b
    operation = input_data.operation.lower()
    
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")
    
    return CalculatorOutput(
        result=result,
        operation=operation
    )


async def main():
    """Run the basic integration example"""
    print("Starting AILF-Kagent Basic Integration Example")
    
    # Create an AILF tool description
    calculator_tool_desc = ToolDescription(
        id="calculator",
        name="Calculator",
        description="Perform basic arithmetic operations",
        function=calculator_tool,
        input_schema=CalculatorInput,
        output_schema=CalculatorOutput
    )
    
    # Create an AILF-to-Kagent tool adapter
    calculator_adapter = AILFToolAdapter(calculator_tool_desc)
    
    # Create a Kagent agent with the adapted tool
    agent = KAgent(tools=[calculator_adapter])
    
    # Test the agent with a calculation request
    user_query = "Calculate 15 + 27"
    print(f"\nUser query: {user_query}")
    
    response = await agent.run(user_query)
    print("\nAgent response:")
    print(response)
    
    # Test with another operation
    user_query = "What is 144 divided by 12?"
    print(f"\nUser query: {user_query}")
    
    response = await agent.run(user_query)
    print("\nAgent response:")
    print(response)
    
    print("\nExample completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
