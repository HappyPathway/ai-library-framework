"""Integration tests for the A2A protocol flow."""
import asyncio
import os
import signal
import subprocess
import time
import unittest
from typing import AsyncIterator, List, Optional, Union
import uuid

import pytest
import requests

from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_server import (
    A2AAgentExecutor,
    A2ARequestContext,
    AILFASA2AServer,
)
from ailf.schemas.a2a import (
    Message,
    MessageDelta,
    MessagePart,
    MessagePartDelta,
    Task,
    TaskDelta,
    TaskState,
)
from ailf.schemas.agent import AgentDescription, CommunicationEndpoint
from ailf.schemas.interaction import StandardMessage


class SimpleAgentExecutor(A2AAgentExecutor):
    """Simple agent executor for testing."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute the agent logic.
        
        Args:
            context: The request context.
            
        Returns:
            Either a Task or an AsyncIterator of TaskDeltas.
        """
        if not context.message:
            return context.task
        
        # Check if streaming is requested
        content = context.message.parts[0].content if context.message.parts else ""
        if "stream" in content.lower():
            return self._stream_response(context, content)
        
        # Standard (non-streaming) response
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=f"Echo: {content}")]
        )
        context.task.messages.append(response)
        context.task.state = TaskState.COMPLETED
        
        return context.task
        
    async def _stream_response(self, context: A2ARequestContext, content: str) -> AsyncIterator[TaskDelta]:
        """Stream a response.
        
        Args:
            context: The request context.
            content: The message content.
            
        Yields:
            TaskDelta objects.
        """
        # Initial delta
        yield TaskDelta(
            id=context.task.id,
            state=TaskState.RUNNING,
            done=False
        )
        
        # Split the response into words and stream them
        words = f"Echo (streaming): {content}".split()
        for i, word in enumerate(words):
            await asyncio.sleep(0.1)  # Simulate processing time
            
            yield TaskDelta(
                messages=[
                    MessageDelta(
                        role="assistant" if i == 0 else None,
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
        
        # Final delta
        yield TaskDelta(
            state=TaskState.COMPLETED,
            done=True
        )


@pytest.mark.asyncio
@pytest.mark.integration
class TestA2AProtocolFlow:
    """Integration tests for A2A protocol flow."""
    
    @classmethod
    def setup_class(cls):
        """Start the A2A server process."""
        # Define server host/port
        cls.server_host = "localhost"
        cls.server_port = 8765
        cls.server_url = f"http://{cls.server_host}:{cls.server_port}"
        
        # Start the server in a separate process
        cls._start_server()
        
        # Wait for server to start
        cls._wait_for_server()
        
    @classmethod
    def teardown_class(cls):
        """Stop the A2A server process."""
        if hasattr(cls, "server_process") and cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait()
    
    @classmethod
    def _start_server(cls):
        """Start the A2A server in a subprocess."""
        # Create a Python script to run the server
        script_path = os.path.join(os.path.dirname(__file__), "run_a2a_server.py")
        
        # Create agent executor, server, and app
        with open(script_path, "w") as f:
            f.write("""#!/usr/bin/env python
import asyncio
import os
import uvicorn
from ailf.communication.a2a_server import A2AAgentExecutor, A2ARequestContext, AILFASA2AServer, TaskDelta
from ailf.schemas.agent import AgentDescription, CommunicationEndpoint
from ailf.schemas.a2a import Message, MessageDelta, MessagePart, MessagePartDelta, Task, TaskState
from typing import AsyncIterator, Union

class SimpleAgentExecutor(A2AAgentExecutor):
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        if not context.message:
            return context.task
        
        content = context.message.parts[0].content if context.message.parts else ""
        if "stream" in content.lower():
            return self._stream_response(context, content)
        
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=f"Echo: {content}")]
        )
        context.task.messages.append(response)
        context.task.state = TaskState.COMPLETED
        
        return context.task
        
    async def _stream_response(self, context: A2ARequestContext, content: str) -> AsyncIterator[TaskDelta]:
        yield TaskDelta(
            id=context.task.id,
            state=TaskState.RUNNING,
            done=False
        )
        
        words = f"Echo (streaming): {content}".split()
        for i, word in enumerate(words):
            await asyncio.sleep(0.05)
            
            yield TaskDelta(
                messages=[
                    MessageDelta(
                        role="assistant" if i == 0 else None,
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
        
        yield TaskDelta(
            state=TaskState.COMPLETED,
            done=True
        )

def main():
    # Create agent description
    agent_description = AgentDescription(
        agent_name="Integration Test Agent",
        agent_type="test",
        description="An agent for integration testing",
        supports_a2a=True,
        communication_endpoints=[
            CommunicationEndpoint(protocol="http", address="http://localhost:8765")
        ]
    )
    
    # Create executor and server
    executor = SimpleAgentExecutor()
    server = AILFASA2AServer(agent_description, executor)
    
    # Run the server
    app = server.create_app()
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")

if __name__ == "__main__":
    main()
""")
        
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        # Start the server
        cls.server_process = subprocess.Popen(
            ["python", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    
    @classmethod
    def _wait_for_server(cls, max_attempts=30, delay=1):
        """Wait for the server to become available.
        
        Args:
            max_attempts: Maximum number of connection attempts.
            delay: Delay between attempts in seconds.
        
        Raises:
            RuntimeError: If the server doesn't start within the specified time.
        """
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{cls.server_url}/")
                if response.status_code == 200:
                    return
            except requests.RequestException:
                pass
                
            time.sleep(delay)
            
        raise RuntimeError(f"Server didn't start within {max_attempts * delay} seconds")
    
    async def test_a2a_protocol_flow(self):
        """Test the complete A2A protocol flow."""
        # Create A2A client
        client = A2AClient(base_url=self.server_url)
        
        # Get agent card
        agent_card = await client.get_agent_card()
        assert agent_card.name == "Integration Test Agent"
        assert agent_card.description == "An agent for integration testing"
        
        # Create a task
        task = await client.create_task()
        assert task.id is not None
        assert task.state == TaskState.CREATED
        
        # Send a message
        message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Hello, agent!")]
        )
        updated_task = await client.send_message(task.id, message)
        
        # Check the response
        assert updated_task.state == TaskState.COMPLETED
        assert len(updated_task.messages) == 2
        assert updated_task.messages[0].role == "user"
        assert updated_task.messages[1].role == "assistant"
        assert updated_task.messages[1].parts[0].content == "Echo: Hello, agent!"
        
        # Stream a message
        streaming_message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Please stream this response")]
        )
        
        # Collect streaming response
        content_parts = []
        async for delta in client.stream_message(task.id, streaming_message):
            if delta.messages and delta.messages[0].parts:
                for part in delta.messages[0].parts:
                    if part.content:
                        content_parts.append(part.content)
        
        # Check the streaming response
        full_content = "".join(content_parts)
        assert "Echo (streaming): Please stream this response" in full_content
        
        # Get task by ID
        retrieved_task = await client.get_task(task.id)
        assert retrieved_task.id == task.id
        
        # List tasks
        tasks = await client.list_tasks()
        assert len(tasks) >= 1
        assert any(t.id == task.id for t in tasks)
        
        # Cancel the task
        cancelled_task = await client.cancel_task(task.id)
        assert cancelled_task.state == TaskState.CANCELED
        
        print("A2A integration test successful!")


if __name__ == "__main__":
    unittest.main()
