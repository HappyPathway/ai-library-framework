"""Tests for A2A interoperability with external implementations.

This module tests the interoperability between AILF's A2A implementation and
other A2A-compatible implementations like LangGraph, CrewAI, or AG2.
"""
import asyncio
import os
import sys
import json
import pytest
from typing import Dict, List, Optional, Any

from ailf.communication.a2a_client import A2AClient
from ailf.schemas.a2a import Message, MessagePart, Task, TaskState


# Skip this test module if the external A2A implementations are not installed
# This is a placeholder for now - implementation will depend on having the external
# libraries properly installed and configured
required_libraries = ["crewai", "langgraph"]
missing_libraries = [lib for lib in required_libraries if lib not in sys.modules]
if missing_libraries:
    pytest.skip(
        f"Skipping A2A interoperability tests due to missing libraries: {', '.join(missing_libraries)}",
        allow_module_level=True,
    )


@pytest.fixture
def external_a2a_server_url():
    """Get the URL of an external A2A server for testing.
    
    This could be a LangGraph, CrewAI, or AG2 server that's running locally
    or in a test environment.
    """
    # For now, we'll check an environment variable, but this could be more sophisticated
    # like spinning up a Docker container with the external A2A implementation
    url = os.environ.get("EXTERNAL_A2A_SERVER_URL")
    if not url:
        pytest.skip("No external A2A server URL provided via EXTERNAL_A2A_SERVER_URL")
    return url


@pytest.mark.interop
@pytest.mark.asyncio
async def test_connect_to_external_a2a_server(external_a2a_server_url):
    """Test that our A2A client can connect to an external A2A server."""
    client = A2AClient(base_url=external_a2a_server_url)
    
    try:
        # Fetch the agent card to verify connectivity
        agent_card = await client.get_agent_card()
        
        # Basic validation
        assert agent_card is not None
        assert agent_card.name is not None
        assert agent_card.description is not None
        
        # Log server info
        print(f"\nConnected to external A2A server: {agent_card.name}")
        print(f"Description: {agent_card.description}")
        print(f"Capabilities: {agent_card.capabilities}")
    except Exception as e:
        pytest.fail(f"Failed to connect to external A2A server: {str(e)}")


@pytest.mark.interop
@pytest.mark.asyncio
async def test_task_lifecycle_with_external_server(external_a2a_server_url):
    """Test the full task lifecycle with an external A2A server."""
    client = A2AClient(base_url=external_a2a_server_url)
    
    try:
        # Create a new task
        task = await client.create_task()
        assert task is not None
        assert task.id is not None
        
        # Send a simple message
        message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Hello, A2A server! What can you do?")]
        )
        
        response = await client.send_message(task.id, message)
        assert response is not None
        assert len(response.messages) >= 1
        
        # Verify the response contains a message from the assistant
        assert any(msg.role == "assistant" for msg in response.messages)
        
        # Get the task again to check its state
        task_info = await client.get_task(task.id)
        assert task_info is not None
        assert task_info.state in [TaskState.READY, TaskState.COMPLETED]
        
        # Cancel the task when done
        await client.cancel_task(task.id)
        
        # Verify task is now cancelled
        task_info = await client.get_task(task.id)
        assert task_info.state == TaskState.CANCELLED
    except Exception as e:
        pytest.fail(f"Task lifecycle with external A2A server failed: {str(e)}")


@pytest.mark.interop
@pytest.mark.asyncio
async def test_streaming_with_external_server(external_a2a_server_url):
    """Test streaming responses with an external A2A server."""
    client = A2AClient(base_url=external_a2a_server_url)
    
    # Check if server supports streaming
    agent_card = await client.get_agent_card()
    if not agent_card.capabilities.streaming:
        pytest.skip("External A2A server does not support streaming")
    
    try:
        # Create a task
        task = await client.create_task()
        
        # Send a message that should trigger a longer response
        message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Give me a detailed explanation of A2A protocol")]
        )
        
        # Stream the response
        chunks = []
        async for chunk in client.stream_message(task.id, message):
            chunks.append(chunk)
            # Just process the first few chunks for testing
            if len(chunks) >= 5:
                break
        
        # Verify we received stream chunks
        assert len(chunks) > 0
        assert all(hasattr(chunk, "parts") for chunk in chunks)
    except Exception as e:
        pytest.fail(f"Streaming with external A2A server failed: {str(e)}")


# Placeholder for tests with specific external implementations
@pytest.mark.skip(reason="External implementation not available")
@pytest.mark.asyncio
async def test_with_langgraph():
    """Test interoperability with LangGraph A2A implementation."""
    # Implementation will depend on LangGraph's A2A interface
    pass


@pytest.mark.skip(reason="External implementation not available")
@pytest.mark.asyncio
async def test_with_crewai():
    """Test interoperability with CrewAI A2A implementation."""
    # Implementation will depend on CrewAI's A2A interface
    pass


@pytest.mark.skip(reason="External implementation not available")
@pytest.mark.asyncio
async def test_with_ag2():
    """Test interoperability with AG2 implementation."""
    # Implementation will depend on AG2's A2A interface
    pass
