"""Unit tests for the A2A client implementation."""
import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import HTTPStatusError, RequestError, Response

from ailf.communication.a2a_client import (
    A2AClient,
    A2AClientError,
    A2AHTTPError,
    A2AJSONError,
)
from ailf.schemas.a2a import (
    AgentCard,
    AgentCapabilities,
    AgentProvider,
    Message,
    MessagePart,
    Task,
    TaskDelta,
    TaskState,
)


class TestA2AClient(unittest.TestCase):
    """Test the A2A client."""

    def setUp(self):
        """Set up the test."""
        self.base_url = "https://example.com/agent"
        self.client = A2AClient(base_url=self.base_url)

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_client.httpx.AsyncClient")
    async def test_get_agent_card(self, mock_client):
        """Test getting the agent card."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Test Agent",
            "description": "A test agent",
            "url": "https://example.com/agent",
            "provider": {
                "name": "Test Provider",
                "url": "https://example.com"
            },
            "version": "1.0.0",
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
                "stateTransitionHistory": False
            }
        }
        
        # Set up mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Call the method
        agent_card = await self.client.get_agent_card()

        # Assert the results
        assert isinstance(agent_card, AgentCard)
        assert agent_card.name == "Test Agent"
        assert agent_card.description == "A test agent"
        assert agent_card.url == "https://example.com/agent"
        assert agent_card.provider.name == "Test Provider"
        assert agent_card.capabilities.streaming is True

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_client.httpx.AsyncClient")
    async def test_create_task(self, mock_client):
        """Test creating a task."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task": {
                "id": "test-task-1",
                "state": "created",
                "messages": [],
                "createdAt": "2023-01-01T00:00:00Z",
                "updatedAt": "2023-01-01T00:00:00Z"
            }
        }
        
        # Set up mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Call the method
        task = await self.client.create_task()

        # Assert the results
        assert isinstance(task, Task)
        assert task.id == "test-task-1"
        assert task.state == TaskState.CREATED
        assert len(task.messages) == 0

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_client.httpx.AsyncClient")
    async def test_get_task(self, mock_client):
        """Test getting a task."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task": {
                "id": "test-task-1",
                "state": "running",
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "parts": [
                            {"type": "text", "content": "Hello agent!"}
                        ],
                        "createdAt": "2023-01-01T00:00:00Z"
                    }
                ],
                "createdAt": "2023-01-01T00:00:00Z",
                "updatedAt": "2023-01-01T00:00:01Z"
            }
        }
        
        # Set up mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Call the method
        task = await self.client.get_task("test-task-1")

        # Assert the results
        assert isinstance(task, Task)
        assert task.id == "test-task-1"
        assert task.state == TaskState.RUNNING
        assert len(task.messages) == 1
        assert task.messages[0].role == "user"
        assert task.messages[0].parts[0].type == "text"
        assert task.messages[0].parts[0].content == "Hello agent!"

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_client.httpx.AsyncClient")
    async def test_send_message(self, mock_client):
        """Test sending a message."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "task": {
                "id": "test-task-1",
                "state": "completed",
                "messages": [
                    {
                        "id": "msg-1",
                        "role": "user",
                        "parts": [
                            {"type": "text", "content": "Hello agent!"}
                        ],
                        "createdAt": "2023-01-01T00:00:00Z"
                    },
                    {
                        "id": "msg-2",
                        "role": "assistant",
                        "parts": [
                            {"type": "text", "content": "Hello user!"}
                        ],
                        "createdAt": "2023-01-01T00:00:01Z"
                    }
                ],
                "createdAt": "2023-01-01T00:00:00Z",
                "updatedAt": "2023-01-01T00:00:01Z"
            }
        }
        
        # Set up mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Create a message to send
        message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Hello agent!")]
        )

        # Call the method
        task = await self.client.send_message("test-task-1", message)

        # Assert the results
        assert isinstance(task, Task)
        assert task.id == "test-task-1"
        assert task.state == TaskState.COMPLETED
        assert len(task.messages) == 2
        assert task.messages[1].role == "assistant"
        assert task.messages[1].parts[0].content == "Hello user!"

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_client.httpx.AsyncClient")
    async def test_stream_message(self, mock_client):
        """Test streaming a message."""
        # Set up the mock response for streaming
        mock_stream_response = AsyncMock()
        mock_stream_response.raise_for_status = MagicMock()
        
        # Create SSE responses
        sse_responses = [
            "data: {\"task\": {\"id\": \"test-task-1\", \"state\": \"running\", \"messages\": [{\"role\": \"assistant\", \"parts\": [{\"type\": \"text\", \"content\": \"Hello\"}]}]}}\n\n",
            "data: {\"task\": {\"messages\": [{\"parts\": [{\"content\": \" world\"}]}]}}\n\n",
            "data: {\"task\": {\"state\": \"completed\", \"done\": true}}\n\n"
        ]
        
        # Set up the aiter_text method to return the SSE responses
        mock_stream_response.aiter_text = AsyncMock()
        mock_stream_response.aiter_text.return_value.__aiter__.return_value = [chunk for chunk in sse_responses]
        
        # Set up mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.stream.return_value.__aenter__.return_value = mock_stream_response
        mock_client.return_value = mock_client_instance

        # Create a message to send
        message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Hello agent!")]
        )

        # Call the method and collect the results
        deltas = []
        async for delta in self.client.stream_message("test-task-1", message):
            deltas.append(delta)

        # Assert the results
        assert len(deltas) == 3
        
        assert deltas[0].id == "test-task-1"
        assert deltas[0].state == TaskState.RUNNING
        assert len(deltas[0].messages) == 1
        assert deltas[0].messages[0].role == "assistant"
        assert deltas[0].messages[0].parts[0].type == "text"
        assert deltas[0].messages[0].parts[0].content == "Hello"
        
        assert len(deltas[1].messages) == 1
        assert deltas[1].messages[0].parts[0].content == " world"
        
        assert deltas[2].state == TaskState.COMPLETED
        assert deltas[2].done is True

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_client.httpx.AsyncClient")
    async def test_http_error(self, mock_client):
        """Test handling HTTP errors."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Task not found"}
        
        # Set up mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.request.side_effect = HTTPStatusError("404 Not Found", request=None, response=mock_response)
        mock_client.return_value = mock_client_instance

        # Call the method and check for exception
        with pytest.raises(A2AHTTPError) as excinfo:
            await self.client.get_task("nonexistent-task")
            
        # Assert the results
        assert "HTTP 404" in str(excinfo.value)
        assert "Task not found" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_client.httpx.AsyncClient")
    async def test_json_error(self, mock_client):
        """Test handling JSON parsing errors."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        # Set up mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Call the method and check for exception
        with pytest.raises(A2AJSONError) as excinfo:
            await self.client.get_agent_card()
            
        # Assert the results
        assert "Failed to parse JSON" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_client.httpx.AsyncClient")
    async def test_request_error(self, mock_client):
        """Test handling request errors."""
        # Set up mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.request.side_effect = RequestError("Connection error")
        mock_client.return_value = mock_client_instance

        # Call the method and check for exception
        with pytest.raises(A2AClientError) as excinfo:
            await self.client.get_agent_card()
            
        # Assert the results
        assert "Request error" in str(excinfo.value)

if __name__ == "__main__":
    unittest.main()
