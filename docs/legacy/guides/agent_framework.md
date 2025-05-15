# Agent Framework User Guide

## Overview

The AILF Agent Framework provides a unified way to build AI agents with different capabilities and architectural patterns. It serves as the central integration point between different components like AI engines, tools, memory systems, and communication protocols.

### Key Components

- **Agent**: Base agent class with essential agent capabilities
- **Planning Strategies**: Different approaches to planning agent actions
  - **ReactivePlan**: Simple stimulus-response planning
  - **DeliberativePlan**: Multi-step planning with reasoning
  - **TreeOfThoughtsPlan**: Branching thought process for complex problems
- **Tools**: System for registering and executing agent tools

## Getting Started

### Creating a Simple Agent

```python
from ailf.agent import Agent

# Create a simple reactive agent
agent = Agent(
    name="SimpleAssistant",
    model_name="openai:gpt-4-turbo",  # Format: provider:model_name
    description="A helpful assistant that answers questions"
)

# Run the agent
result = await agent.run("What is the capital of France?")
print(result)
```

### Using Different Planning Strategies

```python
from ailf.agent import Agent, DeliberativePlan, TreeOfThoughtsPlan

# Create an agent with deliberative planning
deliberative_agent = Agent(
    name="ResearchAssistant",
    model_name="anthropic:claude-3-opus-20240229",
    planning_strategy=DeliberativePlan()
)

# Create an agent with tree of thoughts planning
tot_agent = Agent(
    name="ProblemSolver",
    model_name="openai:gpt-4-turbo",
    planning_strategy=TreeOfThoughtsPlan(num_thoughts=3, max_depth=2)
)
```

### Working with Tools

```python
from ailf.agent import Agent
from ailf.agent.tools import tool

# Define a tool
@tool(category="search")
async def web_search(query: str) -> list:
    """Search the web for information.
    
    :param query: The search query
    :return: List of search results
    """
    # Implementation
    ...

# Create an agent and add tools
agent = Agent(
    name="ResearchAssistant",
    model_name="openai:gpt-4-turbo"
)

# Add tools to the agent
agent.add_tool(web_search)
```

### Structured Output

```python
from pydantic import BaseModel, Field
from typing import List
from ailf.agent import Agent

# Define output schema
class AnalysisResult(BaseModel):
    summary: str = Field(description="Summary of analysis")
    key_points: List[str] = Field(description="Key points identified")
    
# Run agent with structured output
result = await agent.run(
    "Analyze this text and extract key points...",
    output_schema=AnalysisResult
)

print(f"Summary: {result.summary}")
print("Key Points:")
for point in result.key_points:
    print(f"- {point}")
```

## Agent Memory

Agents have built-in memory capabilities that can be used to store and retrieve information across multiple interactions:

```python
from ailf.agent import Agent

agent = Agent(
    name="AssistantWithMemory",
    model_name="openai:gpt-4-turbo"
)

# Add facts to agent memory
agent.memory.add_fact("User's name is Alice")
agent.memory.add_fact("User is interested in machine learning")

# Run the agent with memory
result = await agent.run("What topics might interest me?")
```

## Advanced Usage

### Custom Planning Strategies

You can implement custom planning strategies by extending the `PlanningStrategy` class:

```python
from ailf.agent.base import PlanningStrategy, Agent, AgentStep
from typing import List

class CustomPlanner(PlanningStrategy):
    """Custom planning strategy."""
    
    async def plan(self, agent: Agent, query: str) -> List[AgentStep]:
        """Generate a custom plan.
        
        Args:
            agent: The agent that will execute the plan
            query: The user query/task to plan for
            
        Returns:
            List[AgentStep]: A custom plan
        """
        # Implement your custom planning logic
        steps = [
            AgentStep(
                action="Step 1: Understand the query",
                reasoning="Need to analyze what's being asked"
            ),
            AgentStep(
                action="Step 2: Execute the query",
                reasoning="Process and respond to the user's request"
            )
        ]
        return steps
```

### Tool Registry

For applications with many tools, you can use the ToolRegistry to manage them:

```python
from ailf.agent.tools import ToolRegistry

# Create a registry
registry = ToolRegistry()

# Register tools by category
@registry.register(category="math")
def calculate(expression: str) -> float:
    """Calculate a mathematical expression."""
    return eval(expression)

@registry.register(category="search")
async def search(query: str) -> list:
    """Search for information."""
    # Implementation
    ...

# Get tools by category
math_tools = registry.get_by_category("math")
```

## Best Practices

1. **Use Appropriate Planning Strategies**:
   - ReactivePlan: Best for simple Q&A
   - DeliberativePlan: Good for complex tasks requiring multiple steps
   - TreeOfThoughtsPlan: Useful for problems with multiple possible approaches

2. **Provide Clear Tool Documentation**:
   - Use detailed docstrings for tools
   - Include parameter descriptions with :param tags
   - Document return values with :return tags

3. **Structure Agent Memory**:
   - Add key facts that the agent should remember
   - Clear memory when starting a new session if appropriate
   - Use structured output schemas for consistent responses

4. **Error Handling**:
   - Handle tool execution errors gracefully
   - Provide fallbacks for critical operations
   - Log issues for debugging
