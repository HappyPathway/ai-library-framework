# A2A Multi-Agent Orchestration Guide

This guide explains how to use the A2A orchestration functionality to create complex multi-agent workflows using the AILF framework. The orchestration module allows agents to work together by routing tasks between them based on various conditions.

## Introduction

The A2A orchestration module provides several key components for coordinating multiple A2A-compatible agents:

- **A2AOrchestrator**: The core orchestrator that manages task routing between agents
- **SequentialTaskChain**: A utility for creating sequential workflows across multiple agents
- **ParallelTaskGroup**: A utility for executing tasks on multiple agents in parallel

Using these components, you can create sophisticated agent interactions such as:

1. Conditional routing based on message content
2. Sequential workflows with task handoffs between agents
3. Parallel execution across multiple specialized agents
4. Dynamic routing based on custom logic

## Setting Up the Orchestrator

### 1. Define Routing Configuration

First, define the routing rules that determine how tasks flow between agents:

```python
from ailf.communication.a2a_orchestration import (
    A2AOrchestrator, 
    AgentRoute, 
    OrchestrationConfig,
    RouteCondition,
    RouteType
)

# Define routing configuration
config = OrchestrationConfig(
    routes=[
        # Route from general agent to specialized agents based on content
        AgentRoute(
            source_agent="general-agent",
            type=RouteType.CONDITIONAL,
            conditions=[
                RouteCondition(
                    field="messages[-1].parts[0].content",
                    operator="contains",
                    value="calculate",
                    route_to="calculator-agent"
                ),
                RouteCondition(
                    field="messages[-1].parts[0].content",
                    operator="contains",
                    value="search",
                    route_to="search-agent"
                )
            ]
        ),
        # Route from calculator back to general agent
        AgentRoute(
            source_agent="calculator-agent",
            type=RouteType.SEQUENTIAL,
            destination_agents=["general-agent"]
        )
    ],
    entry_points=["general-agent"],  # Agents that can start workflow
    max_routing_depth=5  # Maximum number of routing steps
)
```

### 2. Create the Orchestrator with Registry Integration

For agent discovery, integrate with a registry manager:

```python
from ailf.communication.a2a_registry import A2ARegistryManager

# Set up registry manager (local and/or remote)
registry_manager = A2ARegistryManager()

# Create orchestrator with the config and registry
orchestrator = A2AOrchestrator(config, registry_manager=registry_manager)
```

### 3. Register Dynamic Routers (Optional)

For complex routing logic, register dynamic router functions:

```python
def content_router(task):
    """Route based on content analysis."""
    last_message = task.messages[-1]
    content = last_message.parts[0].content if last_message.parts else ""
    
    # Analyze content and decide where to route
    if "finance" in content.lower():
        return "finance-agent"
    elif "legal" in content.lower():
        return "legal-agent"
    return "general-agent"  # Default routing

# Register the router
orchestrator.register_dynamic_router("content_analysis_router", content_router)

# Add a dynamic route to the config
dynamic_route = AgentRoute(
    source_agent="triage-agent",
    type=RouteType.DYNAMIC,
    dynamic_router="content_analysis_router"  # Must match registered name
)
orchestrator.config.routes.append(dynamic_route)
```

## Orchestration Patterns

### Pattern 1: Conditional Routing

Automatically route tasks based on message content:

```python
# Create a task at an entry point agent
task = await orchestrator.create_task("general-agent")

# Send a message that may trigger routing
message = Message(
    role="user",
    parts=[MessagePart(type="text", content="Can you calculate 123 * 456 for me?")]
)

# The message will be sent and routing will happen automatically if conditions match
response = await orchestrator.send_message(task.id, message)

# Check where the task ended up
handler = orchestrator.task_handlers[task.id]
current_agent = handler.current_agent  # e.g. "calculator-agent"
routing_history = handler.history  # e.g. ["general-agent", "calculator-agent"]
```

### Pattern 2: Sequential Chain

Create a predefined sequence of agents to process a task:

```python
from ailf.communication.a2a_orchestration import SequentialTaskChain

# Define the sequence of agents
agent_sequence = ["intake-agent", "research-agent", "analysis-agent", "summary-agent"]

# Create a sequential chain
chain = SequentialTaskChain(orchestrator, agent_sequence)

# Start the chain at the first agent
task = await chain.start_chain()

# Send a message through the chain
# The message will be processed by each agent in sequence
message = Message(
    role="user",
    parts=[MessagePart(type="text", content="Research quantum computing advances")]
)
response = await chain.send_message(message)

# Get the conversation history across all agents
history = chain.get_conversation_history()
for entry in history:
    print(f"[{entry['agent_id']}] {entry['role']}: {entry['content'][0]}")
```

### Pattern 3: Parallel Task Group

Process tasks on multiple agents simultaneously:

```python
from ailf.communication.a2a_orchestration import ParallelTaskGroup

# Create a parallel task group
group = ParallelTaskGroup(orchestrator)

# Create tasks on multiple specialized agents
agents = ["research-agent", "analysis-agent", "summary-agent"]
tasks = await group.create_tasks(agents)

# Send the same query to all agents
message = Message(
    role="user",
    parts=[MessagePart(type="text", content="Analyze this data from different perspectives")]
)

# The message will be sent to all agents in parallel
results = await group.send_message_to_all(message)

# Collect results from all agents
all_results = await group.collect_results()
for agent_id, agent_results in all_results.items():
    print(f"Results from {agent_id}:")
    for result in agent_results:
        print(f"- {result['content'][0]}")
```

## Working with Task Handlers

The orchestrator keeps track of tasks using `TaskHandler` objects:

```python
# Get the handler for a specific task
handler = orchestrator.task_handlers[task_id]

# Check the task's current status and location
current_agent = handler.current_agent
current_status = handler.status
routing_history = handler.history

# Examine routing metadata
metadata = handler.metadata
if "routing_history" in metadata:
    for route in metadata["routing_history"]:
        print(f"Routed from {route['from']} to {route['to']} at {route['timestamp']}")
```

## Best Practices

1. **Set Reasonable Routing Depth**: Configure `max_routing_depth` to prevent infinite routing loops.

2. **Use Entry Points Carefully**: Only designate agents as entry points if they are designed to handle initial user queries.

3. **Design Clear Routing Conditions**: Ensure routing conditions are specific and don't overlap to prevent ambiguous routing.

4. **Provide Context When Routing**: When tasks are routed between agents, ensure sufficient context is provided so the destination agent understands the task.

5. **Monitor Routing Paths**: Use the task handler's history and metadata to track how tasks flow between agents, which can help identify optimization opportunities.

6. **Test Complex Workflows Thoroughly**: Validate that multi-step workflows route tasks as expected under various conditions.

7. **Handle Routing Failures**: Implement error handling for cases where routing fails or a suitable destination agent isn't available.

## Debugging Routing Issues

If tasks aren't being routed as expected:

1. Check that the source agent matches the route definition
2. Verify route conditions match the actual message content
3. Ensure route destinations are valid agent IDs
4. Confirm registry integration is working for agent discovery
5. Check for route conflicts or ambiguities
6. Examine task routing history to see where tasks actually went
7. Verify dynamic router functions are registered and working properly

## Examples

For complete examples, refer to:
- `/examples/a2a_orchestration_example.py`: Basic orchestration patterns
- `/examples/a2a_content_router.py`: Advanced dynamic routing
- `/examples/a2a_workflow_automation.py`: Building complex agent workflows

## Advanced Usage

### Custom Field Extraction

When creating routing conditions, you can extract specific fields using path notation:

```python
# Check content of the last message from the assistant
RouteCondition(
    field="messages[-1].parts[0].content",  # Last message, first part content
    operator="contains",
    value="finance",
    route_to="finance-agent"
)

# Check task state
RouteCondition(
    field="state",
    operator="eq",
    value="completed",
    route_to="archive-agent"
)

# Check task metadata
RouteCondition(
    field="metadata.priority",
    operator="gt",
    value=5,
    route_to="priority-agent"
)
```

### Custom Task Handlers

You can manually create and register task handlers:

```python
from ailf.communication.a2a_orchestration import TaskHandler

# Create a custom task handler
handler = TaskHandler(
    task_id="custom-task-1",
    current_agent="custom-agent",
    history=["entry-agent", "custom-agent"],
    status="running",
    metadata={"custom_data": {"priority": "high"}}
)

# Register it with the orchestrator
orchestrator.task_handlers[handler.task_id] = handler
```

### Implementing Advanced Routing Logic

For complex routing needs, implement a custom dynamic router:

```python
async def advanced_router(task):
    """Advanced routing with external service calls."""
    # Extract content
    last_message = task.messages[-1]
    content = last_message.parts[0].content
    
    # Call external service for content classification
    classification = await external_classifier_service.classify(content)
    
    # Route based on classification
    if classification.get("category") == "technical":
        # Route to the most appropriate technical agent
        subcategory = classification.get("subcategory", "")
        if subcategory == "programming":
            return "code-agent"
        elif subcategory == "data":
            return "data-agent"
        else:
            return "tech-agent"
    elif classification.get("category") == "business":
        return "business-agent"
    
    # Default routing
    return "general-agent"

# Register the advanced router
orchestrator.register_dynamic_router("advanced_classifier", advanced_router)
```

## Integration with Other AILF Components

The orchestration module integrates with other AILF components:

- **A2A Registry**: Discovers agents and their capabilities
- **A2A Push Notifications**: Can be used to notify clients about routing events
- **Agent Execution**: Works with the standard A2A execution model

This integration allows for building complex, distributed agent systems that can work together seamlessly.
