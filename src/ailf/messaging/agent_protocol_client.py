"""
Agent Protocol client for interacting with compliant agent services.

This module provides a client implementation for the LangChain Agent Protocol,
allowing applications to interact with remote agent services that implement
the protocol specification.

Examples:
    >>> client = AgentProtocolClient(base_url="http://localhost:8000")
    >>> task = await client.create_task("Analyze this data and create a summary")
    >>> step = await client.execute_step(task.task_id, "First, let's look at the data structure")
"""

import asyncio
import logging
import mimetypes
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO

import httpx
from pydantic import HttpUrl

from ailf.schemas.messaging.agent_protocol import (
    Artifact, ArtifactType, ArtifactUploadRequest, ArtifactUploadResponse,
    Task, TaskRequestBody, Step, StepRequestBody, TaskStatus, StepStatus,
    ListTasksResponse
)

logger = logging.getLogger(__name__)


class AgentProtocolError(Exception):
    """Base exception for Agent Protocol errors."""
    pass


class TaskCreationError(AgentProtocolError):
    """Exception raised when task creation fails."""
    pass


class TaskExecutionError(AgentProtocolError):
    """Exception raised when task execution fails."""
    pass


class StepExecutionError(AgentProtocolError):
    """Exception raised when step execution fails."""
    pass


class ArtifactUploadError(AgentProtocolError):
    """Exception raised when artifact upload fails."""
    pass


class AgentProtocolClient:
    """Client for interacting with Agent Protocol compliant services."""
    
    def __init__(
        self, 
        base_url: Union[str, HttpUrl], 
        timeout: float = 60.0,
        api_key: Optional[str] = None
    ):
        """Initialize the Agent Protocol client.
        
        Args:
            base_url: Base URL of the Agent Protocol service
            timeout: Request timeout in seconds
            api_key: Optional API key for authentication
        """
        self.base_url = str(base_url).rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        self._client = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=headers
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """Enter async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.close()
    
    async def list_tasks(self) -> ListTasksResponse:
        """List all tasks.
        
        Returns:
            ListTasksResponse: Response containing the list of tasks
            
        Raises:
            AgentProtocolError: If the request fails
        """
        try:
            response = await self.client.get("/agent/tasks")
            response.raise_for_status()
            return ListTasksResponse.parse_obj(response.json())
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list tasks: {e}")
            raise AgentProtocolError(f"Failed to list tasks: {e}")
        except Exception as e:
            logger.error(f"Unexpected error listing tasks: {e}")
            raise AgentProtocolError(f"Unexpected error: {e}")
    
    async def create_task(
        self, 
        input_data: Union[str, Dict[str, Any]], 
        additional_input: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a new task.
        
        Args:
            input_data: Task input content (string or structured data)
            additional_input: Optional additional parameters
            
        Returns:
            Task: The created task
            
        Raises:
            TaskCreationError: If task creation fails
        """
        try:
            request_body = TaskRequestBody(
                input=input_data,
                additional_input=additional_input
            )
            
            response = await self.client.post(
                "/agent/tasks",
                json=request_body.dict(exclude_none=True)
            )
            response.raise_for_status()
            return Task.parse_obj(response.json())
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create task: {e}")
            raise TaskCreationError(f"Failed to create task: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating task: {e}")
            raise TaskCreationError(f"Unexpected error: {e}")
    
    async def get_task(self, task_id: str) -> Task:
        """Get a task by ID.
        
        Args:
            task_id: The ID of the task to retrieve
            
        Returns:
            Task: The requested task
            
        Raises:
            AgentProtocolError: If the request fails
        """
        try:
            response = await self.client.get(f"/agent/tasks/{task_id}")
            response.raise_for_status()
            return Task.parse_obj(response.json())
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            raise AgentProtocolError(f"Failed to get task {task_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting task {task_id}: {e}")
            raise AgentProtocolError(f"Unexpected error: {e}")
    
    async def execute_step(
        self,
        task_id: str,
        input_data: Optional[Union[str, Dict[str, Any]]] = None,
        additional_input: Optional[Dict[str, Any]] = None
    ) -> Step:
        """Execute a step for a task.
        
        Args:
            task_id: The ID of the parent task
            input_data: Input content for this step
            additional_input: Optional additional parameters
            
        Returns:
            Step: The executed step
            
        Raises:
            StepExecutionError: If step execution fails
        """
        try:
            request_body = StepRequestBody(
                input=input_data,
                additional_input=additional_input
            )
            
            response = await self.client.post(
                f"/agent/tasks/{task_id}/steps",
                json=request_body.dict(exclude_none=True)
            )
            response.raise_for_status()
            return Step.parse_obj(response.json())
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to execute step for task {task_id}: {e}")
            raise StepExecutionError(f"Failed to execute step: {e}")
        except Exception as e:
            logger.error(f"Unexpected error executing step for task {task_id}: {e}")
            raise StepExecutionError(f"Unexpected error: {e}")
    
    async def get_step(self, task_id: str, step_id: str) -> Step:
        """Get a step by ID.
        
        Args:
            task_id: The ID of the parent task
            step_id: The ID of the step to retrieve
            
        Returns:
            Step: The requested step
            
        Raises:
            AgentProtocolError: If the request fails
        """
        try:
            response = await self.client.get(f"/agent/tasks/{task_id}/steps/{step_id}")
            response.raise_for_status()
            return Step.parse_obj(response.json())
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get step {step_id} for task {task_id}: {e}")
            raise AgentProtocolError(f"Failed to get step: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting step {step_id} for task {task_id}: {e}")
            raise AgentProtocolError(f"Unexpected error: {e}")
    
    async def list_steps(self, task_id: str) -> List[Step]:
        """List all steps for a task.
        
        Args:
            task_id: The ID of the parent task
            
        Returns:
            List[Step]: List of steps for the task
            
        Raises:
            AgentProtocolError: If the request fails
        """
        try:
            response = await self.client.get(f"/agent/tasks/{task_id}/steps")
            response.raise_for_status()
            return [Step.parse_obj(step) for step in response.json()]
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list steps for task {task_id}: {e}")
            raise AgentProtocolError(f"Failed to list steps: {e}")
        except Exception as e:
            logger.error(f"Unexpected error listing steps for task {task_id}: {e}")
            raise AgentProtocolError(f"Unexpected error: {e}")
    
    async def upload_artifact(
        self,
        task_id: str,
        step_id: Optional[str],
        file: Union[BinaryIO, Path, str],
        artifact_type: ArtifactType = ArtifactType.FILE,
        file_name: Optional[str] = None
    ) -> ArtifactUploadResponse:
        """Upload an artifact.
        
        Args:
            task_id: The ID of the parent task
            step_id: Optional ID of the associated step
            file: File to upload (file-like object or path)
            artifact_type: Type of artifact
            file_name: Optional name for the file
            
        Returns:
            ArtifactUploadResponse: Response containing uploaded artifact details
            
        Raises:
            ArtifactUploadError: If artifact upload fails
        """
        try:
            # Handle different file input types
            if isinstance(file, (str, Path)):
                path = Path(file)
                file_name = file_name or path.name
                content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
                file_obj = open(path, "rb")
            else:
                if not file_name:
                    raise ValueError("file_name is required when passing a file-like object")
                file_obj = file
                content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
            
            # Prepare upload request
            upload_request = ArtifactUploadRequest(
                file_name=file_name,
                content_type=content_type,
                artifact_type=artifact_type
            )
            
            url = f"/agent/tasks/{task_id}"
            if step_id:
                url += f"/steps/{step_id}"
            url += "/artifacts"
            
            # Perform actual upload
            files = {"file": (file_name, file_obj, content_type)}
            data = {"metadata": upload_request.json()}
            
            response = await self.client.post(url, files=files, data=data)
            response.raise_for_status()
            
            # Close file if we opened it
            if isinstance(file, (str, Path)):
                file_obj.close()
            
            return ArtifactUploadResponse.parse_obj(response.json())
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to upload artifact: {e}")
            raise ArtifactUploadError(f"Failed to upload artifact: {e}")
        except Exception as e:
            logger.error(f"Unexpected error uploading artifact: {e}")
            raise ArtifactUploadError(f"Unexpected error: {e}")
    
    async def get_artifact(
        self,
        task_id: str,
        artifact_id: str,
        step_id: Optional[str] = None
    ) -> bytes:
        """Get an artifact by ID.
        
        Args:
            task_id: The ID of the parent task
            artifact_id: The ID of the artifact to retrieve
            step_id: Optional ID of the associated step
            
        Returns:
            bytes: The artifact content
            
        Raises:
            AgentProtocolError: If the request fails
        """
        try:
            url = f"/agent/tasks/{task_id}"
            if step_id:
                url += f"/steps/{step_id}"
            url += f"/artifacts/{artifact_id}/content"
            
            response = await self.client.get(url)
            response.raise_for_status()
            return response.content
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get artifact {artifact_id}: {e}")
            raise AgentProtocolError(f"Failed to get artifact: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting artifact {artifact_id}: {e}")
            raise AgentProtocolError(f"Unexpected error: {e}")
