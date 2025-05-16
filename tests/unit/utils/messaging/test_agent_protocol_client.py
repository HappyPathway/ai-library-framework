"""
Unit tests for the Agent Protocol client.
"""

import json
import pytest
import httpx
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from schemas.messaging.agent_protocol import (
    Task, TaskStatus, Step, StepStatus, Artifact, ArtifactType
)
from utils.messaging.agent_protocol_client import (
    AgentProtocolClient, TaskCreationError, StepExecutionError, AgentProtocolError
)


@pytest.fixture
def mock_task():
    """Create a mock task."""
    return Task(
        task_id="task123",
        status=TaskStatus.CREATED,
        input="Test input",
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_step():
    """Create a mock step."""
    return Step(
        step_id="step123",
        task_id="task123",
        status=StepStatus.COMPLETED,
        input="Step input",
        output="Step output",
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )


@pytest.fixture
def mock_artifact():
    """Create a mock artifact."""
    return Artifact(
        artifact_id="artifact123",
        type=ArtifactType.TEXT,
        data="Artifact data",
        created_at=datetime.utcnow()
    )


@pytest.fixture
async def mock_client():
    """Create a mocked Agent Protocol client."""
    with patch("utils.messaging.agent_protocol_client.httpx.AsyncClient") as mock_client_class:
        mock_http_client = AsyncMock()
        mock_client_class.return_value = mock_http_client
        client = AgentProtocolClient("http://test-server:8000")
        yield client, mock_http_client
        await client.close()


@pytest.mark.asyncio
async def test_create_task(mock_client, mock_task):
    """Test creating a task."""
    client, mock_http_client = mock_client
    
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_task.dict()
    mock_http_client.post.return_value = mock_response
    
    # Call the method
    result = await client.create_task("Test input")
    
    # Assert
    assert result.task_id == mock_task.task_id
    assert result.input == mock_task.input
    assert result.status == mock_task.status
    
    # Verify the request was made correctly
    mock_http_client.post.assert_called_once()
    args, kwargs = mock_http_client.post.call_args
    assert args[0] == "/agent/tasks"
    assert "input" in kwargs["json"]
    assert kwargs["json"]["input"] == "Test input"


@pytest.mark.asyncio
async def test_create_task_error(mock_client):
    """Test task creation error handling."""
    client, mock_http_client = mock_client
    
    # Setup mock response for failure
    mock_response = AsyncMock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad request", request=MagicMock(), response=mock_response
    )
    mock_http_client.post.return_value = mock_response
    
    # Call the method and expect exception
    with pytest.raises(TaskCreationError):
        await client.create_task("Test input")


@pytest.mark.asyncio
async def test_execute_step(mock_client, mock_step):
    """Test executing a step."""
    client, mock_http_client = mock_client
    
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_step.dict()
    mock_http_client.post.return_value = mock_response
    
    # Call the method
    result = await client.execute_step("task123", "Step input")
    
    # Assert
    assert result.step_id == mock_step.step_id
    assert result.task_id == mock_step.task_id
    assert result.input == mock_step.input
    assert result.output == mock_step.output
    assert result.status == mock_step.status
    
    # Verify the request was made correctly
    mock_http_client.post.assert_called_once()
    args, kwargs = mock_http_client.post.call_args
    assert args[0] == "/agent/tasks/task123/steps"
    assert "input" in kwargs["json"]
    assert kwargs["json"]["input"] == "Step input"


@pytest.mark.asyncio
async def test_get_task(mock_client, mock_task):
    """Test getting a task."""
    client, mock_http_client = mock_client
    
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_task.dict()
    mock_http_client.get.return_value = mock_response
    
    # Call the method
    result = await client.get_task("task123")
    
    # Assert
    assert result.task_id == mock_task.task_id
    assert result.input == mock_task.input
    assert result.status == mock_task.status
    
    # Verify the request was made correctly
    mock_http_client.get.assert_called_once_with("/agent/tasks/task123")


@pytest.mark.asyncio
async def test_list_steps(mock_client, mock_step):
    """Test listing steps for a task."""
    client, mock_http_client = mock_client
    
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [mock_step.dict()]
    mock_http_client.get.return_value = mock_response
    
    # Call the method
    steps = await client.list_steps("task123")
    
    # Assert
    assert len(steps) == 1
    assert steps[0].step_id == mock_step.step_id
    assert steps[0].task_id == mock_step.task_id
    
    # Verify the request was made correctly
    mock_http_client.get.assert_called_once_with("/agent/tasks/task123/steps")


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test client as context manager."""
    with patch("utils.messaging.agent_protocol_client.httpx.AsyncClient") as mock_client_class:
        mock_http_client = AsyncMock()
        mock_client_class.return_value = mock_http_client
        
        async with AgentProtocolClient("http://test-server:8000") as client:
            assert client._client is mock_http_client
        
        # Context manager should close client
        mock_http_client.aclose.assert_called_once()
