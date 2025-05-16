"""Integration tests for AG-UI protocol implementation.

These tests verify that the AG-UI protocol implementation works correctly
by testing client-server interactions.
"""

import pytest
import asyncio
import json
import uuid
from typing import List, Dict, Any, AsyncGenerator

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.testclient import TestClientASGITransport

from ailf.schemas.agent import AgentDescription
from ailf.schemas.ag_ui import (
    UserMessage,
    SystemMessage,
    EventType,
    RunAgentInput,
)
from ailf.communication.ag_ui_server import (
    AGUIExecutor,
    AGUIRequestContext,
    AILFAsAGUIServer,
)
from ailf.communication.ag_ui_client import AGUIClient


class MockAGUIExecutor(AGUIExecutor):
    """Mock executor for testing."""
    
    def __init__(self):
        """Initialize the mock executor."""
        self.calls = []
        
    async def execute(self, context):
        """Mock execution that returns predictable events."""
        self.calls.append(context)
        
        # Emit run started event
        yield {
            "type": EventType.RUN_STARTED,
            "run_id": context.run_id,
            "timestamp": 1620000000000,
        }
        
        # Emit text message events
        message_id = str(uuid.uuid4())
        
        yield {
            "type": EventType.TEXT_MESSAGE_START,
            "message_id": message_id,
            "role": "assistant",
            "timestamp": 1620000001000,
        }
        
        yield {
            "type": EventType.TEXT_MESSAGE_CONTENT,
            "message_id": message_id,
            "content": "This is a mock response.",
            "timestamp": 1620000002000,
        }
        
        yield {
            "type": EventType.TEXT_MESSAGE_END,
            "message_id": message_id,
            "timestamp": 1620000003000,
        }
        
        # Emit run finished event
        yield {
            "type": EventType.RUN_FINISHED,
            "run_id": context.run_id,
            "timestamp": 1620000004000,
        }


@pytest.fixture
def agent_description():
    """Fixture for agent description."""
    return AgentDescription(
        id="test-agent",
        name="Test Agent",
        description="Test agent for AG-UI protocol",
        supports_tools=True,
    )


@pytest.fixture
def mock_executor():
    """Fixture for mock executor."""
    return MockAGUIExecutor()


@pytest.fixture
def ag_ui_server(agent_description, mock_executor):
    """Fixture for AG-UI server."""
    return AILFAsAGUIServer(
        executor=mock_executor,
        agent_description=agent_description,
    )


@pytest.fixture
def fastapi_app(ag_ui_server):
    """Fixture for FastAPI app."""
    app = FastAPI()
    app.include_router(ag_ui_server.router, prefix="/api")
    return app


@pytest.fixture
def client(fastapi_app):
    """Fixture for test client."""
    return TestClient(fastapi_app)


class TestAGUISuite:
    """Test suite for AG-UI protocol implementation."""
    
    def test_get_agent_info(self, client, agent_description):
        """Test getting agent information."""
        response = client.get("/api/v1/agent")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == agent_description.id
        assert data["name"] == agent_description.name
        assert data["description"] == agent_description.description
        assert data["capabilities"]["tools"] is True
        assert data["capabilities"]["streaming"] is True
    
    def test_run_agent_non_streaming(self, client):
        """Test running the agent with non-streaming response."""
        messages = [
            SystemMessage(id="sys1", role="system", content="You are a test assistant"),
            UserMessage(id="user1", role="user", content="Hello"),
        ]
        
        input_data = RunAgentInput(
            messages=messages,
            stream=False,
        )
        
        response = client.post("/api/v1/run", json=input_data.model_dump(by_alias=True))
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "messages" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "assistant"
        assert data["messages"][0]["content"] == "This is a mock response."
    
    def test_run_agent_streaming(self, client):
        """Test running the agent with streaming response."""
        messages = [
            SystemMessage(id="sys1", role="system", content="You are a test assistant"),
            UserMessage(id="user1", role="user", content="Hello"),
        ]
        
        input_data = RunAgentInput(
            messages=messages,
            stream=True,
        )
        
        response = client.post(
            "/api/v1/run", 
            json=input_data.model_dump(by_alias=True),
            headers={"Accept": "text/event-stream"},
            stream=True,
        )
        assert response.status_code == 200
        
        # Collect all events
        events = []
        for chunk in response.iter_lines():
            if not chunk:
                continue
                
            if chunk.startswith(b"data: "):
                data = chunk[len(b"data: "):].decode("utf-8")
                if data == "[DONE]":
                    continue
                    
                try:
                    event = json.loads(data)
                    events.append(event)
                except json.JSONDecodeError:
                    pass
        
        # Check events
        assert len(events) == 4
        assert events[0]["type"] == "RUN_STARTED"
        assert events[1]["type"] == "TEXT_MESSAGE_START"
        assert events[2]["type"] == "TEXT_MESSAGE_CONTENT"
        assert events[2]["content"] == "This is a mock response."
        assert events[3]["type"] == "TEXT_MESSAGE_END"


@pytest.mark.asyncio
async def test_ag_ui_client(fastapi_app):
    """Test the AG-UI client."""
    # Start the app in a separate task
    transport = TestClientASGITransport(app=fastapi_app)
    
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        # Create the AG-UI client
        client = AGUIClient(
            base_url="http://testserver/api",
        )
        client._http_client = http_client  # Replace the HTTP client
        
        try:
            # Get agent info
            agent_info = await client.get_agent_info()
            assert agent_info["id"] == "test-agent"
            assert agent_info["name"] == "Test Agent"
            
            # Test streaming
            messages = [
                SystemMessage(id="sys1", role="system", content="You are a test assistant"),
                UserMessage(id="user1", role="user", content="Hello"),
            ]
            
            events = []
            async for event in await client.run_agent(messages=messages, stream=True):
                events.append(event)
            
            assert len(events) == 2  # TEXT_MESSAGE_CONTENT and other event(s)
            assert any(e.type == EventType.TEXT_MESSAGE_CONTENT for e in events)
            
            # Test non-streaming
            response = await client.run_agent(messages=messages, stream=False)
            assert response.task_id is not None
            assert len(response.messages) == 1
        finally:
            await client.close()
