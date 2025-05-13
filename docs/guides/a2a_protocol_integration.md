# A2A Protocol Integration Guide

This guide explains how to use the Agent-to-Agent (A2A) Protocol integration in AILF.

## Overview

The [A2A Protocol](https://a2ap.org/) is an open standard for agent interoperability. AILF's A2A integration allows your agents to:

1. Connect to other A2A-compatible agents
2. Expose your AILF agents as A2A-compatible services
3. Perform standardized agent-to-agent communication

## Key Components

The A2A integration in AILF consists of these main components:

1. **A2A Schemas** (`ailf.schemas.a2a`): Pydantic models mapping to the A2A Protocol specification
2. **A2A Client** (`ailf.communication.A2AClient`): Client for interacting with A2A-compatible agents
3. **A2A Server** (`ailf.communication.AILFASA2AServer`): Base class for exposing AILF agents as A2A servers
4. **Agent Executor** (`ailf.communication.A2AAgentExecutor`): Base class for implementing agent logic

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

## Best Practices

1. **Version Compatibility**: Ensure your A2A implementation stays compatible with the specification
2. **Error Handling**: Properly handle errors and status codes in A2A interactions
3. **Event Streaming**: Use SSE (Server-Sent Events) for streaming responses
4. **Documentation**: Document the capabilities of your A2A agent in its Agent Card
5. **Testing**: Test interoperability with other A2A-compatible agents
6. **Session Handling**: Implement proper session resumption for interrupted conversations
