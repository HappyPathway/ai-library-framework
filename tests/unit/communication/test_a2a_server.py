"""Unit tests for the A2A server implementation."""
import asyncio
import json
import unittest
from typing import AsyncIterator, Dict, List, Union
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ailf.communication.a2a_server import (
    A2AAgentExecutor,
    A2ARequestContext,
    A2AServerError,
    AILFASA2AServer,
    TaskStore,
)
from ailf.schemas.a2a import (
    AgentCard,
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


class MockAgentExecutor(A2AAgentExecutor):
    """Mock agent executor for testing."""
    
    def __init__(self, streaming: bool = False):
        """Initialize the mock executor.
        
        Args:
            streaming: Whether to use streaming responses.
        """
        self.streaming = streaming
        self.calls = []
        
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute the mock agent logic.
        
        Args:
            context: The request context.
            
        Returns:
            Either a Task or an AsyncIterator of TaskDelta.
        """
        self.calls.append(context)
        
        if not context.message:
            return context.task
            
        if self.streaming:
            # Return a generator for streaming
            return self._stream_response(context)
        
        # Standard (non-streaming) response
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=f"Echo: {context.message.parts[0].content}")]
        )
        context.task.messages.append(response)
        context.task.state = TaskState.COMPLETED
        return context.task
        
    async def _stream_response(self, context: A2ARequestContext) -> AsyncIterator[TaskDelta]:
        """Stream a mock response.
        
        Args:
            context: The request context.
            
        Yields:
            TaskDelta objects.
        """
        # Initial delta
        yield TaskDelta(
            id=context.task.id,
            state=TaskState.RUNNING,
            done=False
        )
        
        # Content delta
        yield TaskDelta(
            messages=[
                MessageDelta(
                    role="assistant",
                    parts=[
                        MessagePartDelta(
                            type="text",
                            content=f"Echo: {context.message.parts[0].content}"
                        )
                    ]
                )
            ],
            done=False
        )
        
        # Final delta
        yield TaskDelta(
            state=TaskState.COMPLETED,
            done=True
        )


class TestTaskStore(unittest.TestCase):
    """Test the TaskStore class."""

    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test creating a task."""
        store = TaskStore()
        task = await store.create_task()
        assert isinstance(task, Task)
        assert task.id in store.tasks
        assert task.state == TaskState.CREATED
        assert task.createdAt is not None

    @pytest.mark.asyncio
    async def test_get_task(self):
        """Test getting a task."""
        store = TaskStore()
        task = await store.create_task()
        
        # Get the task
        retrieved_task = await store.get_task(task.id)
        assert retrieved_task == task
        
        # Get a nonexistent task
        nonexistent_task = await store.get_task("nonexistent")
        assert nonexistent_task is None

    @pytest.mark.asyncio
    async def test_update_task(self):
        """Test updating a task."""
        store = TaskStore()
        task = await store.create_task()
        
        # Update the task
        task.state = TaskState.RUNNING
        updated_task = await store.update_task(task)
        assert updated_task.state == TaskState.RUNNING
        
        # Try to update a nonexistent task
        nonexistent_task = Task(id="nonexistent")
        with pytest.raises(A2AServerError):
            await store.update_task(nonexistent_task)

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        """Test listing tasks."""
        store = TaskStore()
        
        # Create some tasks
        task1 = await store.create_task()
        task2 = await store.create_task()
        task3 = await store.create_task()
        
        # List all tasks
        tasks = await store.list_tasks()
        assert len(tasks) == 3
        
        # List with limit
        tasks = await store.list_tasks(limit=2)
        assert len(tasks) == 2
        
        # List with skip
        tasks = await store.list_tasks(skip=2)
        assert len(tasks) == 1

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Test canceling a task."""
        store = TaskStore()
        task = await store.create_task()
        
        # Cancel the task
        cancelled_task = await store.cancel_task(task.id)
        assert cancelled_task.state == TaskState.CANCELED
        
        # Try to cancel a nonexistent task
        with pytest.raises(A2AServerError):
            await store.cancel_task("nonexistent")


class TestA2AAgentExecutor(unittest.TestCase):
    """Test the A2AAgentExecutor class."""

    @pytest.mark.asyncio
    async def test_convert_message_to_standard(self):
        """Test converting an A2A Message to a StandardMessage."""
        executor = A2AAgentExecutor()
        
        # Create an A2A Message
        a2a_message = Message(
            role="user",
            parts=[
                MessagePart(type="text", content="Hello, agent!"),
                MessagePart(type="text", content=" How are you?")
            ]
        )
        
        # Convert to StandardMessage
        std_message = await executor.convert_message_to_standard(a2a_message)
        
        # Check the results
        assert isinstance(std_message, StandardMessage)
        assert std_message.content == "Hello, agent! How are you?"
        assert std_message.metadata["role"] == "user"
        assert std_message.metadata["message_id"] == a2a_message.id
        assert std_message.metadata["a2a_message"] == a2a_message

    @pytest.mark.asyncio
    async def test_convert_standard_to_message(self):
        """Test converting a StandardMessage to an A2A Message."""
        executor = A2AAgentExecutor()
        
        # Create a StandardMessage
        std_message = StandardMessage(
            content="Hello, user! I'm doing well.",
            metadata={"source": "test"}
        )
        
        # Convert to A2A Message
        a2a_message = await executor.convert_standard_to_message(std_message, role="assistant")
        
        # Check the results
        assert isinstance(a2a_message, Message)
        assert a2a_message.role == "assistant"
        assert len(a2a_message.parts) == 1
        assert a2a_message.parts[0].type == "text"
        assert a2a_message.parts[0].content == "Hello, user! I'm doing well."


class TestAILFASA2AServer(unittest.TestCase):
    """Test the AILFASA2AServer class."""

    def setUp(self):
        """Set up the test."""
        # Create agent description
        self.agent_description = AgentDescription(
            agent_name="Test Agent",
            agent_type="test",
            description="A test agent",
            supports_a2a=True,
            communication_endpoints=[
                CommunicationEndpoint(protocol="http", address="http://example.com/agent")
            ]
        )
        
        # Create executor and server
        self.executor = MockAgentExecutor()
        self.task_store = TaskStore()
        self.server = AILFASA2AServer(self.agent_description, self.executor, self.task_store)

    @pytest.mark.asyncio
    async def test_create_app(self):
        """Test creating a FastAPI application."""
        app = self.server.create_app()
        assert isinstance(app, FastAPI)
        assert app.title == "Test Agent"

    def test_get_agent_card(self):
        """Test getting the agent card."""
        app = self.server.create_app()
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Agent"
        assert data["description"] == "A test agent"
        assert data["url"] == "http://example.com/agent"

    @pytest.mark.asyncio
    async def test_create_task_endpoint(self):
        """Test the create task endpoint."""
        app = self.server.create_app()
        client = TestClient(app)
        
        response = client.post("/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert data["task"]["state"] == "created"
        assert isinstance(data["task"]["id"], str)

    @pytest.mark.asyncio
    async def test_list_tasks_endpoint(self):
        """Test the list tasks endpoint."""
        # Create some tasks
        await self.task_store.create_task()
        await self.task_store.create_task()
        
        app = self.server.create_app()
        client = TestClient(app)
        
        response = client.get("/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks" in data
        assert len(data["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_get_task_endpoint(self):
        """Test the get task endpoint."""
        # Create a task
        task = await self.task_store.create_task()
        
        app = self.server.create_app()
        client = TestClient(app)
        
        # Get the task
        response = client.get(f"/tasks/{task.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert data["task"]["id"] == task.id
        
        # Get a nonexistent task
        response = client.get("/tasks/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_task_endpoint(self):
        """Test the cancel task endpoint."""
        # Create a task
        task = await self.task_store.create_task()
        
        app = self.server.create_app()
        client = TestClient(app)
        
        # Cancel the task
        response = client.post(f"/tasks/{task.id}/cancel")
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert data["task"]["id"] == task.id
        assert data["task"]["state"] == "canceled"
        
        # Cancel a nonexistent task
        response = client.post("/tasks/nonexistent/cancel")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_send_message_endpoint(self):
        """Test the send message endpoint."""
        # Create a task
        task = await self.task_store.create_task()
        
        app = self.server.create_app()
        client = TestClient(app)
        
        # Send a message
        response = client.post(
            f"/tasks/{task.id}/messages",
            json={
                "message": {
                    "role": "user",
                    "parts": [
                        {"type": "text", "content": "Hello, agent!"}
                    ]
                }
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "task" in data
        assert data["task"]["id"] == task.id
        assert data["task"]["state"] == "completed"
        assert len(data["task"]["messages"]) == 1
        
        # Send a message to a nonexistent task
        response = client.post(
            "/tasks/nonexistent/messages",
            json={
                "message": {
                    "role": "user",
                    "parts": [
                        {"type": "text", "content": "Hello, agent!"}
                    ]
                }
            }
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_streaming_message_endpoint(self):
        """Test the streaming message endpoint."""
        # Create streaming server
        streaming_executor = MockAgentExecutor(streaming=True)
        streaming_server = AILFASA2AServer(
            self.agent_description, 
            streaming_executor,
            self.task_store
        )
        
        # Create a task
        task = await self.task_store.create_task()
        
        app = streaming_server.create_app()
        client = TestClient(app)
        
        # Send a streaming message
        response = client.post(
            f"/tasks/{task.id}/messages:stream",
            json={
                "message": {
                    "role": "user",
                    "parts": [
                        {"type": "text", "content": "Hello, agent!"}
                    ]
                }
            }
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        
        # Parse the SSE response
        events = []
        for line in response.iter_lines():
            if line.startswith(b"data: "):
                data = json.loads(line.decode("utf-8")[6:])  # Remove "data: " prefix
                events.append(data)
        
        assert len(events) == 3
        assert "task" in events[0]
        assert "state" in events[0]["task"]
        assert events[0]["task"]["state"] == "running"
        
        assert "messages" in events[1]["task"]
        assert len(events[1]["task"]["messages"]) == 1
        assert events[1]["task"]["messages"][0]["parts"][0]["content"] == "Echo: Hello, agent!"
        
        assert events[2]["task"]["state"] == "completed"
        assert events[2]["task"]["done"] is True


if __name__ == "__main__":
    unittest.main()
