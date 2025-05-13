"""A2A Protocol client implementation for AILF.

This module provides a client for interacting with A2A-compatible agents.
"""
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from uuid import uuid4

import httpx
from pydantic import ValidationError

from ailf.schemas.a2a import (
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    GetTaskRequest,
    GetTaskResponse,
    Message,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageStreamingRequest,
    SendMessageStreamingResponse,
    Task,
    TaskDelta,
    TaskIdParams,
    TaskState,
)

logger = logging.getLogger(__name__)


class A2AClientError(Exception):
    """Base exception for A2A client errors."""
    pass


class A2AHTTPError(A2AClientError):
    """Exception raised when an HTTP error occurs."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class A2AJSONError(A2AClientError):
    """Exception raised when JSON parsing fails."""
    pass


class A2AClient:
    """Client for interacting with A2A-compatible agents."""

    def __init__(self, 
                 base_url: str, 
                 headers: Optional[Dict[str, str]] = None, 
                 timeout: float = 60.0):
        """Initialize the A2A client.

        Args:
            base_url: The base URL of the A2A agent.
            headers: Optional headers to include in requests.
            timeout: Timeout for HTTP requests in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        
    async def _make_request(self, 
                           method: str, 
                           path: str, 
                           json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an HTTP request to the A2A agent.

        Args:
            method: HTTP method to use.
            path: Path to request.
            json_data: Optional JSON data to send.

        Returns:
            The JSON response from the agent.

        Raises:
            A2AHTTPError: If an HTTP error occurs.
            A2AJSONError: If JSON parsing fails.
        """
        url = f"{self.base_url}{path}"
        logger.debug(f"Making {method} request to {url}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json_data,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                try:
                    return response.json()
                except json.JSONDecodeError as e:
                    raise A2AJSONError(f"Failed to parse JSON response: {e}")
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json().get("detail", str(e))
            except Exception:
                error_detail = str(e)
                
            raise A2AHTTPError(e.response.status_code, error_detail)
        except httpx.RequestError as e:
            raise A2AClientError(f"Request error: {e}")
            
    async def get_agent_card(self) -> AgentCard:
        """Get the agent card.

        Returns:
            The agent card.

        Raises:
            A2AClientError: If the request fails.
        """
        try:
            response = await self._make_request("GET", "/")
            return AgentCard.parse_obj(response)
        except ValidationError as e:
            raise A2AClientError(f"Failed to parse agent card: {e}")
            
    async def create_task(self) -> Task:
        """Create a new task.

        Returns:
            The created task.

        Raises:
            A2AClientError: If the request fails.
        """
        try:
            response = await self._make_request("POST", "/tasks")
            return Task.parse_obj(response.get("task"))
        except ValidationError as e:
            raise A2AClientError(f"Failed to parse task: {e}")
            
    async def get_task(self, task_id: str) -> Task:
        """Get a task by ID.

        Args:
            task_id: The ID of the task.

        Returns:
            The task.

        Raises:
            A2AClientError: If the request fails.
        """
        try:
            response = await self._make_request("GET", f"/tasks/{task_id}")
            return Task.parse_obj(response.get("task"))
        except ValidationError as e:
            raise A2AClientError(f"Failed to parse task: {e}")
            
    async def cancel_task(self, task_id: str) -> Task:
        """Cancel a task.

        Args:
            task_id: The ID of the task.

        Returns:
            The cancelled task.

        Raises:
            A2AClientError: If the request fails.
        """
        try:
            request = CancelTaskRequest()
            response = await self._make_request("POST", f"/tasks/{task_id}/cancel", request.dict())
            return Task.parse_obj(response.get("task"))
        except ValidationError as e:
            raise A2AClientError(f"Failed to parse task: {e}")
            
    async def send_message(self, 
                          task_id: str, 
                          message: Message) -> Task:
        """Send a message to a task.

        Args:
            task_id: The ID of the task.
            message: The message to send.

        Returns:
            The updated task.

        Raises:
            A2AClientError: If the request fails.
        """
        try:
            request = SendMessageRequest(message=message)
            response = await self._make_request(
                "POST", 
                f"/tasks/{task_id}/messages", 
                request.dict(exclude_none=True)
            )
            return Task.parse_obj(response.get("task"))
        except ValidationError as e:
            raise A2AClientError(f"Failed to parse task: {e}")
            
    async def stream_message(self, 
                           task_id: str, 
                           message: Message) -> AsyncGenerator[TaskDelta, None]:
        """Send a message to a task and stream the response.

        Args:
            task_id: The ID of the task.
            message: The message to send.

        Yields:
            Task deltas as they are received.

        Raises:
            A2AClientError: If the request fails.
        """
        request = SendMessageStreamingRequest(message=message)
        url = f"{self.base_url}/tasks/{task_id}/messages:stream"
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    method="POST",
                    url=url,
                    headers={**self.headers, "Accept": "text/event-stream"},
                    json=request.dict(exclude_none=True),
                    timeout=self.timeout
                ) as response:
                    response.raise_for_status()
                    
                    # Parse Server-Sent Events
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        
                        # Process complete events
                        while "\n\n" in buffer:
                            event, buffer = buffer.split("\n\n", 1)
                            lines = event.split("\n")
                            
                            data_line = next((line for line in lines if line.startswith("data: ")), None)
                            if data_line:
                                data_json = data_line[6:]  # Remove "data: " prefix
                                try:
                                    data = json.loads(data_json)
                                    task_delta = TaskDelta.parse_obj(data.get("task"))
                                    yield task_delta
                                    
                                    if task_delta.done:
                                        return
                                except (json.JSONDecodeError, ValidationError) as e:
                                    logger.error(f"Failed to parse streaming response: {e}")
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json().get("detail", str(e))
            except Exception:
                error_detail = str(e)
                
            raise A2AHTTPError(e.response.status_code, error_detail)
        except httpx.RequestError as e:
            raise A2AClientError(f"Streaming request error: {e}")
            
    async def list_tasks(self, 
                         limit: int = 10, 
                         skip: int = 0) -> List[Task]:
        """List tasks.

        Args:
            limit: Maximum number of tasks to return.
            skip: Number of tasks to skip.

        Returns:
            A list of tasks.

        Raises:
            A2AClientError: If the request fails.
        """
        try:
            response = await self._make_request("GET", f"/tasks?limit={limit}&skip={skip}")
            return [Task.parse_obj(task) for task in response.get("tasks", [])]
        except ValidationError as e:
            raise A2AClientError(f"Failed to parse tasks: {e}")
