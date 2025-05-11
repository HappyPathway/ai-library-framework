# Agents Integration

This guide explains how to use AILF's cognitive capabilities with Kagent agents.

## AILFEnabledAgent

The `AILFEnabledAgent` class extends Kagent's standard agent with AILF's cognitive capabilities:

```python
from ailf_kagent import AILFEnabledAgent

# Create a Kagent agent with AILF capabilities
agent = AILFEnabledAgent(
    use_react_for_complex=True,    # Enable automatic detection of complex queries
    reasoning_threshold=0.7         # Set the complexity threshold
)

# Add tools as normal
agent.add_tool(calculator_tool)

# The agent will automatically use ReAct for complex queries
response = await agent.run("Explain step by step how to solve this problem...")
```

### How It Works

The agent analyzes incoming queries to determine if they would benefit from structured reasoning:

1. **Simple Queries**: For straightforward questions, the standard Kagent agent logic is used
2. **Complex Queries**: For complex or multi-step problems, AILF's ReAct processor is used

The agent determines complexity based on:
- Presence of keywords that indicate reasoning (explain, analyze, compare, etc.)
- Query length and complexity metrics
- Specific topics that typically require reasoning

### Customizing Reasoning Behavior

You can control when reasoning is applied:

```python
# Always use standard Kagent logic
agent = AILFEnabledAgent(use_react_for_complex=False)

# Adjust the reasoning threshold (0.0-1.0)
# Lower values make the agent more likely to use reasoning
agent = AILFEnabledAgent(reasoning_threshold=0.5)
```

## ReActAgent

The `ReActAgent` is a specialized version that *always* uses AILF's ReAct reasoning:

```python
from ailf_kagent import ReActAgent

# Create an agent that always uses ReAct reasoning
agent = ReActAgent()

# Add tools
agent.add_tool(calculator_tool)

# Every query will use ReAct reasoning
response = await agent.run("What's the weather like today?")
```

This agent is useful when:
- Building agents that always need to show their reasoning
- Working on problems that consistently benefit from structured reasoning
- Creating educational agents that explain their process

## Interpreting Results

Both agent types include reasoning traces in their response metadata:

```python
response = await agent.run("Explain how to calculate compound interest")

# Access the response content
print(response.messages[0].content)

# Access the reasoning steps (if reasoning was applied)
if "reasoning_trace" in response.metadata:
    for step in response.metadata["reasoning_trace"]:
        print(f"Step: {step['thought']}")
```

## Best Practices

1. **Appropriate Tool Selection**: Provide agents with appropriate tools for reasoning
2. **Clear Instructions**: Craft system prompts that align with reasoning capabilities
3. **Performance Consideration**: Use reasoning only when necessary, as it increases token usage
4. **Context Management**: Ensure agents have sufficient context for complex reasoning
5. **Fallback Strategies**: Implement fallbacks for when reasoning fails to produce a clear answer
