# AG-UI Protocol Integration for AILF

This document provides an overview of the AG-UI protocol integration in the AILF framework. The AG-UI (Agent-GUI) protocol is a standardized way for AI agents to communicate with user interfaces, making it easy to create interactive applications with consistent behavior.

## Overview

The AG-UI protocol integration in AILF enables:

1. **Exposing AILF agents as AG-UI-compatible endpoints**: This allows AILF agents to be used with any AG-UI-compatible frontend.
2. **Interacting with AG-UI agents**: AILF can act as a client to other AG-UI-compatible agents.
3. **Streaming responses**: Real-time streaming of AI responses, tool calls, and state updates.
4. **Tool integration**: Seamlessly integrating AILF's tool system with AG-UI's tool call mechanism.
5. **State management**: Tracking and updating state across interactions.

## Components

The AG-UI integration consists of several key components:

### Schemas (`ailf/schemas/ag_ui.py`)

Pydantic models representing AG-UI protocol data structures, including:

- Event types (TextMessages, ToolCalls, State events)
- Message formats (User, Assistant, System, Tool messages)
- Request and response structures

### Server (`ailf/communication/ag_ui_server.py`)

Classes for creating AG-UI-compatible servers:

- `AGUIRequestContext`: Manages request context and state
- `AGUIExecutor`: Base class for handling AG-UI requests
- `AILFAsAGUIServer`: FastAPI router that exposes AILF agents via AG-UI protocol

### Client (`ailf/communication/ag_ui_client.py`)

Client for interacting with AG-UI-compatible agents:

- `AGUIClient`: Main client class for making requests
- Support for streaming and non-streaming responses
- Error handling for different failure modes

### Executors

Two executor implementations are provided:

1. **Simple Executor** (`ailf/communication/ag_ui_executor.py`):
   - Basic implementation suitable for text-only agents
   - Simple tool handling with minimal dependencies

2. **Advanced Executor** (`ailf/communication/ag_ui_advanced.py`):
   - More sophisticated implementation with state management
   - Advanced tool handling and response generation
   - Buffer management for handling tool calls mid-text

### Utilities

Additional utility classes to support AG-UI functionality:

- `AGUIStateManager` (`ailf/communication/ag_ui_state.py`): Manages state tracking and updates
- `AGUIToolHandler` (`ailf/communication/ag_ui_tools.py`): Integrates AILF tools with AG-UI

## Usage

### Creating a Simple AG-UI Server

```python
from fastapi import FastAPI
from ailf.ai.engine import AIEngine
from ailf.schemas.agent import AgentDescription
from ailf.communication.ag_ui_server import AILFAsAGUIServer
from ailf.communication.ag_ui_executor import SimpleAGUIExecutor

# Create FastAPI app
app = FastAPI()

# Create AI Engine
ai_engine = AIEngine(model_name="gpt-4")

# Define agent description
agent_description = AgentDescription(
    id="my-agent",
    name="My Agent",
    description="A helpful agent",
    supports_tools=False,
)

# Create executor and server
executor = SimpleAGUIExecutor(ai_engine=ai_engine)
ag_ui_server = AILFAsAGUIServer(
    executor=executor,
    agent_description=agent_description,
)

# Include AG-UI routes
app.include_router(ag_ui_server.router, prefix="/api")
```

### Using the AG-UI Client

```python
import asyncio
from ailf.communication.ag_ui_client import AGUIClient
from ailf.schemas.ag_ui import UserMessage, SystemMessage

async def main():
    # Create client
    client = AGUIClient(base_url="http://localhost:8000/api")
    
    try:
        # Get agent info
        agent_info = await client.get_agent_info()
        print(f"Connected to: {agent_info['name']}")
        
        # Prepare messages
        messages = [
            SystemMessage(
                id="sys1",
                role="system",
                content="You are a helpful assistant.",
            ),
            UserMessage(
                id="user1",
                role="user",
                content="Hello! What can you help me with today?",
            ),
        ]
        
        # Stream response
        print("Streaming response:")
        async for event in await client.run_agent(messages=messages, stream=True):
            if event.type == "TEXT_MESSAGE_CONTENT":
                print(event.content, end="", flush=True)
            elif event.type == "TOOL_CALL_START":
                print(f"\n[Tool: {event.name}]", end="", flush=True)
        print("\nDone!")
    finally:
        await client.close()

# Run the async function
asyncio.run(main())
```

### Using the Advanced Executor with Tools

```python
from ailf.ai.engine import AIEngine
from ailf.tooling.manager import ToolManager
from ailf.tooling.registration import tool
from ailf.communication.ag_ui_advanced import AdvancedAGUIExecutor
from ailf.communication.ag_ui_state import AGUIStateManager

# Create tool manager
tool_manager = ToolManager()

# Register tools
@tool(tool_manager)
async def get_weather(location: str) -> dict:
    """Get weather for a location."""
    return {"temperature": 72, "conditions": "sunny"}

# Create components
ai_engine = AIEngine(model_name="gpt-4")
state_manager = AGUIStateManager()

# Create advanced executor
executor = AdvancedAGUIExecutor(
    ai_engine=ai_engine,
    tool_manager=tool_manager,
    state_manager=state_manager,
    system_prompt="You're a helpful assistant that can check weather.",
)
```

## Working Example

See the complete example in `examples/ag_ui_example.py` which demonstrates:

1. Setting up an AG-UI server with tool capabilities
2. Creating a client that connects to the server
3. Handling streaming responses
4. Processing tool calls during interaction

Run the example:
```bash
# Start the server
python examples/ag_ui_example.py server

# In another terminal, run the client
python examples/ag_ui_example.py client
```

## Testing

The integration includes comprehensive tests:

- Unit tests for individual components
- Integration tests for end-to-end protocol flow
- Test utilities for mocking AG-UI components

Run the tests with:
```bash
pytest tests/integration/communication/test_ag_ui_protocol_flow.py -v
```
