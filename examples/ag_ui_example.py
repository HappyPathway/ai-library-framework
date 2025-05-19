"""Example demonstrating AG-UI protocol integration with AILF.

This example shows how to create an AG-UI compatible server and client
using the AILF framework.

To run this example:
1. Start the server: python examples/ag_ui_example.py server
2. In another terminal, run the client: python examples/ag_ui_example.py client
"""

import argparse
import asyncio
import logging
import uvicorn
from typing import Dict, Any, List

from fastapi import FastAPI

from ailf.ai.engine import AIEngine
from ailf.schemas.agent import AgentDescription
from ailf.tooling.manager import ToolManager
from ailf.tooling.registration import tool
from ailf.communication.ag_ui_server import AILFAsAGUIServer
from ailf.communication.ag_ui_advanced import AdvancedAGUIExecutor
from ailf.communication.ag_ui_client import AGUIClient
from ailf.schemas.ag_ui import UserMessage, SystemMessage, Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create a tool manager
tool_manager = ToolManager()

# Register a couple of simple tools
@tool(tool_manager)
async def weather(location: str) -> Dict[str, Any]:
    """Get current weather for a location."""
    # This is a mock implementation
    return {
        "location": location,
        "temperature": 72,
        "conditions": "Sunny",
        "humidity": 45,
    }

@tool(tool_manager)
async def calculator(operation: str, a: float, b: float) -> Dict[str, Any]:
    """Perform a simple calculation."""
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Cannot divide by zero",
    }
    
    if operation not in operations:
        return {"error": f"Unknown operation: {operation}"}
        
    return {
        "operation": operation,
        "a": a,
        "b": b,
        "result": operations[operation],
    }

# Configure the agent
agent_description = AgentDescription(
    id="demo-agent",
    name="AG-UI Demo Agent",
    description="A demonstration agent using the AG-UI protocol",
    supports_tools=True,
    metadata={
        "capabilities": ["text", "tools"],
        "version": "1.0.0",
    },
)

# AI Engine mock for demonstration
class MockAIEngine(AIEngine):
    """Mock AI engine that returns predefined responses."""
    
    async def generate_stream(self, prompt: str, **kwargs):
        """Simulate a streaming response."""
        # Log the prompt for debugging
        logger.info(f"Prompt: {prompt}")
        
        # Check for special queries to demonstrate tool use
        if "weather" in prompt.lower():
            yield "I'll check the weather for you. "
            yield "[[weather::{'location': 'Seattle'}]]"
            yield " Based on the weather information, it's a nice day in Seattle!"
        elif "calculate" in prompt.lower():
            yield "Let me calculate that for you. "
            
            if "add" in prompt.lower() or "sum" in prompt.lower():
                yield "[[calculator::{'operation': 'add', 'a': 5, 'b': 3}]]"
                yield " The result of adding 5 and 3 is 8."
            else:
                yield "[[calculator::{'operation': 'multiply', 'a': 4, 'b': 6}]]"
                yield " The result of multiplying 4 and 6 is 24."
        else:
            # Default response
            await asyncio.sleep(0.2)
            yield "Hello! I'm a demo agent using the AG-UI protocol. "
            await asyncio.sleep(0.2)
            yield "I can demonstrate tool usage if you ask me about the weather "
            await asyncio.sleep(0.2)
            yield "or to calculate something for you."
            await asyncio.sleep(0.2)
            yield " How can I assist you today?"

def create_app():
    """Create the FastAPI application."""
    app = FastAPI(title="AG-UI Demo")
    
    # Create the AI engine
    ai_engine = MockAIEngine()
    
    # Create the AG-UI executor
    executor = AdvancedAGUIExecutor(
        ai_engine=ai_engine,
        tool_manager=tool_manager,
        system_prompt=(
            "You are a helpful assistant that can use tools. "
            "Respond to the user's queries and use tools when appropriate."
        ),
    )
    
    # Create the AG-UI server
    ag_ui_server = AILFAsAGUIServer(
        executor=executor,
        agent_description=agent_description,
    )
    
    # Add the AG-UI routes to the app
    app.include_router(ag_ui_server.router, prefix="/api")
    
    return app

async def run_client():
    """Run a client that interacts with the AG-UI server."""
    client = AGUIClient(base_url="http://localhost:8000/api")
    
    try:
        # Get agent info
        agent_info = await client.get_agent_info()
        print(f"Agent: {agent_info['name']}")
        print(f"Description: {agent_info['description']}")
        print(f"Capabilities: {agent_info['capabilities']}")
        print()
        
        # Create messages
        messages: List[Message] = [
            SystemMessage(
                id="sys1",
                role="system",
                content="You are a helpful assistant.",
            ),
            UserMessage(
                id="user1",
                role="user",
                content="Hello! Can you tell me about the weather?",
            ),
        ]
        
        # Run the agent with streaming
        print("Running agent with streaming...")
        async for event in await client.run_agent(messages=messages, stream=True):
            if event.type == "TEXT_MESSAGE_CONTENT":
                print(f"Assistant: {event.content}", end="", flush=True)
            elif event.type == "TOOL_CALL_START":
                print(f"\n[Tool Call: {event.name}]", end="", flush=True)
            elif event.type == "TOOL_CALL_END":
                print(f" [Tool Result: {event.output}]", end="", flush=True)
        print("\nStreaming complete!")
        
        # Run the agent without streaming
        print("\nRunning agent without streaming...")
        messages.append(UserMessage(
            id="user2",
            role="user",
            content="Can you calculate something for me?",
        ))
        
        response = await client.run_agent(messages=messages, stream=False)
        print(f"Task ID: {response.task_id}")
        for message in response.messages:
            if message['role'] == 'assistant':
                print(f"Assistant: {message['content']}")
    finally:
        await client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AG-UI example")
    parser.add_argument("mode", choices=["server", "client"], help="Run as server or client")
    args = parser.parse_args()
    
    if args.mode == "server":
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        asyncio.run(run_client())
