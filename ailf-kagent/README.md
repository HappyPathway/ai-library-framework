# AILF-Kagent Integration

This package provides integration components between the Agentic AI Library Framework (AILF) and Kagent, enabling a powerful combination of AILF's agent building blocks with Kagent's orchestration capabilities.

## Overview

AILF provides robust building blocks for developing sophisticated AI agents with structured LLM interactions, tool registration, and cognitive processing. Kagent offers agent orchestration, execution, and management capabilities. This integration creates a powerful end-to-end solution for building and operating advanced AI agents.

## Features

- **Tool Integration**: Use AILF tools within Kagent agents
- **Agent Enhancement**: Enhance Kagent agents with AILF's cognitive capabilities like ReAct reasoning
- **Memory Sharing**: Share memory between AILF and Kagent components
- **Schema Translation**: Map between AILF's and Kagent's schema definitions

## Installation

```bash
# Install from PyPI (once published)
pip install ailf-kagent

# Install from source
git clone https://github.com/your-org/ailf-kagent.git
cd ailf-kagent
pip install -e .
```

## Quick Start

### Basic Tool Integration

```python
from ailf.tooling import ToolDescription
from ailf_kagent.adapters.tools import AILFToolAdapter
from kagent.agents import Agent as KAgent

# Define an AILF tool
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
response = await agent.run("Calculate 5 + 3")
```

### Enhanced Agent with Reasoning

```python
from ailf_kagent.adapters.agents import AILFEnabledAgent

# Create a Kagent agent with AILF's reasoning capabilities
agent = AILFEnabledAgent(
    use_react_for_complex=True,
    reasoning_threshold=0.7
)

# The agent will automatically use ReAct reasoning for complex queries
response = await agent.run("Explain step by step how to solve this problem...")
```

### Memory Sharing

```python
from ailf_kagent.adapters.memory import SharedMemoryManager

# Create a shared memory manager
memory = SharedMemoryManager(namespace="my_agent")

# Use it in your workflow
await memory.kagent_memory.set("user_preference", "dark_mode")
value = await memory.ailf_memory.get("user_preference")  # Returns "dark_mode"
```

## Advanced Usage

See the [examples directory](examples/) for more detailed usage examples:

- `basic_integration.py` - Simple tool adaptation
- `advanced_usage.py` - ReAct reasoning and memory sharing

## Quick Start

```python
import asyncio
from kagent.agents import Agent as KAgent
from ailf.tooling import ToolDescription
from ailf_kagent.adapters.tools import AILFToolAdapter

# Create an AILF tool
my_tool_description = ToolDescription(
    id="my_tool",
    name="My Tool",
    description="A useful tool",
    function=my_tool_function,
    input_schema=MyInputSchema,
    output_schema=MyOutputSchema
)

# Create a Kagent-compatible adapter
tool_adapter = AILFToolAdapter(my_tool_description)

# Use the adapted tool in a Kagent agent
agent = KAgent(tools=[tool_adapter])

# Run the agent
async def main():
    response = await agent.run("Use my tool to perform a task")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Usage

For advanced usage examples including ReAct reasoning, memory sharing, and more sophisticated integrations, see the examples directory.

## Components

### Adapters

- **tools.py**: Adapters for using AILF tools with Kagent
- **agents.py**: Enhanced Kagent agents with AILF cognitive capabilities
- **memory.py**: Memory bridges between the two frameworks
- **schemas.py**: Schema translation utilities

## Development

### Prerequisites

- Python 3.8+
- Kagent
- AILF

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/ailf-kagent.git
cd ailf-kagent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

## License

MIT

## Acknowledgements

This integration was developed as part of the AILF project to bridge advanced agent capabilities with robust deployment options.
