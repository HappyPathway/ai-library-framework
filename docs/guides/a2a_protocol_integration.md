# A2A Protocol Integration Guide

This guide explains how to use the Agent-to-Agent (A2A) Protocol integration in AILF.

## Overview

The [A2A Protocol](https://a2ap.org/) is an open standard for agent interoperability. AILF's A2A integration allows your agents to:

1. Connect to other A2A-compatible agents
2. Expose your AILF agents as A2A-compatible services
3. Perform standardized agent-to-agent communication
4. Discover and register agents through registry services
5. Receive real-time updates through push notifications
6. Orchestrate multiple agents in complex workflows

## Key Components

The A2A integration in AILF consists of these main components:

1. **A2A Schemas** (`ailf.schemas.a2a`): Pydantic models mapping to the A2A Protocol specification
2. **A2A Client** (`ailf.communication.A2AClient`): Client for interacting with A2A-compatible agents
3. **A2A Server** (`ailf.communication.AILFASA2AServer`): Base class for exposing AILF agents as A2A servers
4. **Agent Executor** (`ailf.communication.A2AAgentExecutor`): Base class for implementing agent logic
5. **A2A Registry** (`ailf.communication.a2a_registry`): Registry services for agent discovery
6. **Push Notifications** (`ailf.communication.a2a_push`): Real-time update functionality
7. **Multi-Agent Orchestration** (`ailf.communication.a2a_orchestration`): Coordinating multiple agents

## Using the A2A Client

The `A2AClient` allows you to connect to and interact with any A2A-compatible agent:

```python
from ailf.communication import A2AClient
from ailf.schemas.a2a import Message, MessagePart

async def main():
    # Create a client
    client = A2AClient(base_url="https://example.com/agent")
    
    # Get the agent card
    agent_card = await client.get_agent_card()
    print(f"Connected to agent: {agent_card.name}")
    
    # Create a new task
    task = await client.create_task()
    print(f"Created task: {task.id}")
    
    # Send a message
    message = Message(
        role="user",
        parts=[
            MessagePart(type="text", content="Hello, agent!")
        ]
    )
    
    # For non-streaming response
    updated_task = await client.send_message(task.id, message)
    print(f"Agent response: {updated_task.messages[-1].parts[0].content}")
    
    # For streaming response
    async for delta in client.stream_message(task.id, message):
        if delta.messages and delta.messages[0].parts:
            for part in delta.messages[0].parts:
                if part.content:
                    print(part.content, end="", flush=True)
        
        if delta.done:
            print("\nStreaming complete!")
```

## Creating an A2A-Compatible Agent

To expose your AILF agent as an A2A-compatible service:

1. Create an agent executor by extending `A2AAgentExecutor`
2. Create an A2A server using `AILFASA2AServer`

```python
from ailf.communication import A2AAgentExecutor, AILFASA2AServer, A2ARequestContext
from ailf.schemas.agent import AgentDescription
from ailf.schemas.a2a import Task, Message, MessagePart, TaskState

class MyAgentExecutor(A2AAgentExecutor):
    async def execute(self, context: A2ARequestContext):
        # Convert A2A message to AILF message format
        if context.message:
            ailf_message = await self.convert_message_to_standard(context.message)
            
            # Process the message with your AILF agent
            # (Replace this with your actual agent processing logic)
            response_content = f"Echo: {ailf_message.content}"
            
            # Convert response back to A2A format
            a2a_response = await self.convert_standard_to_message(
                std_message=ailf_message.model_copy(update={"content": response_content})
            )
            
            # Add response to task messages
            context.task.messages.append(a2a_response)
            context.task.state = TaskState.COMPLETED
            
        return context.task

# Create agent description
agent_description = AgentDescription(
    agent_name="My A2A Agent",
    agent_type="echo",
    description="A simple echo agent that responds to messages",
    supports_a2a=True,
)

# Create executor and server
executor = MyAgentExecutor()
server = AILFASA2AServer(agent_description, executor)

# Run the server
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8000)
```

## Streaming Responses

To support streaming responses, modify your executor's `execute` method to return an async iterator:

```python
async def execute(self, context: A2ARequestContext):
    if context.message:
        # Initial response with metadata
        yield TaskDelta(
            id=context.task.id,
            state=TaskState.RUNNING,
            done=False
        )
        
        # Stream content word by word
        ailf_message = await self.convert_message_to_standard(context.message)
        words = f"Echo: {ailf_message.content}".split()
        
        for i, word in enumerate(words):
            # In a real implementation, you might get this from your LLM
            await asyncio.sleep(0.2)  # Simulate processing time
            
            # Create a delta update
            yield TaskDelta(
                messages=[
                    MessageDelta(
                        parts=[
                            MessagePartDelta(
                                type="text" if i == 0 else None,
                                content=word + " "
                            )
                        ]
                    )
                ],
                done=(i == len(words) - 1)
            )
            
        # Final update to mark completion
        context.task.state = TaskState.COMPLETED
        yield TaskDelta(
            state=TaskState.COMPLETED,
            done=True
        )
        
        return
    else:
        # Return a regular task if there's no message to process
        return context.task
```

## Converting Between AILF and A2A Formats

The `A2AAgentExecutor` provides helper methods to convert between AILF and A2A message formats:

- `convert_message_to_standard()`: Converts A2A `Message` to AILF `StandardMessage`
- `convert_standard_to_message()`: Converts AILF `StandardMessage` to A2A `Message`

## UX Negotiation

The A2A protocol supports dynamic UX negotiation, allowing agents to agree on input/output capabilities. AILF provides `UXNegotiationMessage` in the ACP schema, aligned with A2A concepts:

```python
from ailf.schemas.acp import (
    UXNegotiationMessage, 
    UXNegotiationPayload, 
    UXCapability, 
    UXNegotiationStatus, 
    ACPMessageHeader,
    ACPMessageType
)

# Create a UX negotiation message
negotiation_message = UXNegotiationMessage(
    header=ACPMessageHeader(
        sender_agent_id="my_agent",
        recipient_agent_id="other_agent",
        message_type=ACPMessageType.UX_NEGOTIATION,
    ),
    payload=UXNegotiationPayload(
        supported_input_modes=[UXCapability.TEXT, UXCapability.IMAGE],
        supported_output_modes=[UXCapability.TEXT, UXCapability.MARKDOWN],
        streaming_support=True,
        negotiation_status=UXNegotiationStatus.REQUEST
    )
)
```

## Using A2A Registry

The A2A Registry allows for discovering and registering agents in both local and remote registries.

### Setting up a Local Registry

```python
from ailf.communication.a2a_registry import A2ARegistry, RegistryEntry

# Create a local registry
registry = A2ARegistry()

# Register an agent
registry.register_agent(RegistryEntry(
    id="my-agent-1",
    name="My First Agent",
    description="A test agent for demonstration",
    url="http://localhost:8000",
    provider={"name": "My Organization", "url": "https://example.com"},
    version="1.0.0",
    capabilities={"streaming": True, "pushNotifications": True}
))

# List all agents
agents = registry.list_agents()
print(f"Found {len(agents)} agents")

# Search for agents with specific capabilities
calculator_agents = registry.search_agents(skills=["calculator"])
```

### Using a Remote Registry

```python
from ailf.communication.a2a_registry import A2ARegistryClient

# Connect to a remote registry
registry_client = A2ARegistryClient(base_url="https://a2a-registry.example.com")

# List available agents
agents = await registry_client.list_agents()
print(f"Found {len(agents)} agents")

# Search for agents by capability
search_agents = await registry_client.search_agents_by_capability({"streaming": True})

# Register your agent
result = await registry_client.register_agent(my_agent_card)
```

### Using the Registry Manager

```python
from ailf.communication.a2a_registry import A2ARegistryManager, A2ARegistry, A2ARegistryClient

# Create a local registry
local_registry = A2ARegistry()

# Create a registry manager with local registry
manager = A2ARegistryManager(local_registry=local_registry)

# Add remote registries
remote_client1 = A2ARegistryClient(base_url="https://registry1.example.com")
remote_client2 = A2ARegistryClient(base_url="https://registry2.example.com")
manager.add_remote_registry(remote_client1, "registry1")
manager.add_remote_registry(remote_client2, "registry2")

# Get agent by ID (checks local then remote)
agent = await manager.get_agent("agent-123")

# List all agents (combines local and remote)
all_agents = await manager.list_agents()

# Search for agents with specific skills
calculator_agents = await manager.search_agents(skills=["calculator"])
```

## Using A2A Push Notifications

Push notifications allow servers to send real-time updates to clients about task state changes.

### Server-Side Push Notifications

```python
from ailf.communication.a2a_push import PushNotificationManager, PushNotificationConfig
from ailf.schemas.a2a import Task, TaskState

# Create a push notification manager
push_manager = PushNotificationManager()

# Register a task for notifications
config = PushNotificationConfig(
    url="https://client.example.com/webhook",
    token="client-auth-token",
    headers={"X-Custom-Header": "value"}
)
push_manager.register_task("task-123", config)

# Send state change notification
await push_manager.notify_task_state_change("task-123", TaskState.RUNNING)

# Send a full task update
task = Task(id="task-123", state=TaskState.COMPLETED, messages=[...])
await push_manager.notify_task_update(task)

# Send a custom notification
await push_manager.send_notification(
    "task-123",
    "progress_update",
    {"progress": 75, "eta": "30 seconds"}
)

# Unregister when done
push_manager.unregister_task("task-123")
```

### Client-Side Push Notifications

```python
from ailf.communication.a2a_push import PushNotificationClient

# Create a notification client
client = PushNotificationClient(
    callback_url="https://my-app.example.com/webhook",
    token="my-auth-token"
)

# Register handlers for specific event types
async def handle_state_change(task_id, data):
    print(f"Task {task_id} state changed to: {data['state']}")

async def handle_task_update(task_id, data):
    print(f"Task {task_id} updated: {data['task']['state']}")

# Register handlers
client.register_handler("task_state_change", handle_state_change)
client.register_handler("task_update", handle_task_update)

# When setting up your web server endpoint, process notifications:
async def webhook_handler(request):
    notification = await request.json()
    await client.process_notification(notification)
    return {"status": "ok"}

# Get config to send to the server
config = client.get_notification_config()
# Pass this config when creating a task that needs notifications
```

## Multi-Agent Orchestration

The A2A orchestration module allows you to coordinate multiple agents in complex workflows.

### Basic Orchestration

```python
from ailf.communication.a2a_orchestration import (
    A2AOrchestrator,
    AgentRoute,
    OrchestrationConfig,
    RouteCondition,
    RouteType
)
from ailf.communication.a2a_registry import A2ARegistryManager
from ailf.schemas.a2a import Message, MessagePart

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
                )
            ]
        ),
        # Return to general agent when done
        AgentRoute(
            source_agent="calculator-agent",
            type=RouteType.SEQUENTIAL,
            destination_agents=["general-agent"]
        )
    ],
    entry_points=["general-agent"]
)

# Create registry manager for agent discovery
registry_manager = A2ARegistryManager()
    
# Create orchestrator
orchestrator = A2AOrchestrator(config, registry_manager=registry_manager)

# Create a task at the entry point
task = await orchestrator.create_task("general-agent")

# Send a message - routing happens automatically
message = Message(
    role="user",
    parts=[MessagePart(type="text", content="Can you calculate 123 * 456?")]
)
response = await orchestrator.send_message(task.id, message)
```

### Sequential Task Chain

```python
from ailf.communication.a2a_orchestration import SequentialTaskChain

# Define an agent sequence for a workflow
agent_sequence = ["intake-agent", "research-agent", "summary-agent"]

# Create a sequential chain
chain = SequentialTaskChain(orchestrator, agent_sequence)

# Start the chain at the first agent
task = await chain.start_chain()

# Send a message through the chain
message = Message(
    role="user",
    parts=[MessagePart(type="text", content="Research quantum computing")]
)
response = await chain.send_message(message)

# Get the full conversation history
history = chain.get_conversation_history()
```

### Parallel Task Processing

```python
from ailf.communication.a2a_orchestration import ParallelTaskGroup

# Create a parallel task group
group = ParallelTaskGroup(orchestrator)

# Create tasks on multiple specialized agents
agents = ["research-agent", "analysis-agent", "summary-agent"]
tasks = await group.create_tasks(agents)

# Send the same message to all agents
message = Message(
    role="user",
    parts=[MessagePart(type="text", content="Analyze this data")]
)
results = await group.send_message_to_all(message)

# Collect all results
all_results = await group.collect_results()
for agent_id, agent_results in all_results.items():
    print(f"Results from {agent_id}: {agent_results[0]['content']}")
```

For more details on orchestration, see the [A2A Orchestration Guide](./a2a_orchestration.md).

## Best Practices

1. **Version Compatibility**: Ensure your A2A implementation stays compatible with the specification
2. **Error Handling**: Properly handle errors and status codes in A2A interactions
3. **Event Streaming**: Use SSE (Server-Sent Events) for streaming responses
4. **Documentation**: Document the capabilities of your A2A agent in its Agent Card
5. **Testing**: Test interoperability with other A2A-compatible agents
6. **Session Handling**: Implement proper session resumption for interrupted conversations
7. **Registry Discovery**: Use registries to discover and connect to appropriate agents
8. **Push Notification Security**: Use proper authentication for push notifications
9. **Orchestration Planning**: Design agent routing carefully to avoid loops and inefficiencies
