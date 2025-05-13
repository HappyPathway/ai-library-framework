"""FastAPI wrapper base classes for A2A servers.

This module provides base classes and utilities for creating A2A-compatible
FastAPI servers that integrate with AILF agents.
"""
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Type, Union

import asyncio
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, ValidationError

from ailf.schemas.a2a import (
    AgentCard,
    Message,
    MessagePart,
    SendMessageRequest,
    SendMessageStreamingRequest,
    Task,
    TaskDelta,
    TaskState,
)
from ailf.schemas.agent import AgentDescription
from ailf.schemas.interaction import StandardMessage

logger = logging.getLogger(__name__)


class A2AServerError(Exception):
    """Base exception for A2A server errors."""
    pass


class TaskStore:
    """Simple in-memory storage for A2A tasks."""
    
    def __init__(self):
        """Initialize an empty task store."""
        self.tasks: Dict[str, Task] = {}
        
    async def create_task(self) -> Task:
        """Create a new task.
        
        Returns:
            The created task.
        """
        task = Task(state=TaskState.CREATED)
        self.tasks[task.id] = task
        return task
        
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            The task if found, None otherwise.
        """
        return self.tasks.get(task_id)
        
    async def update_task(self, task: Task) -> Task:
        """Update a task.
        
        Args:
            task: The task to update.
            
        Returns:
            The updated task.
            
        Raises:
            A2AServerError: If the task doesn't exist.
        """
        if task.id not in self.tasks:
            raise A2AServerError(f"Task {task.id} not found")
            
        task.updatedAt = task.updatedAt  # Update timestamp
        self.tasks[task.id] = task
        return task
        
    async def list_tasks(self, limit: int = 10, skip: int = 0) -> List[Task]:
        """List tasks.
        
        Args:
            limit: Maximum number of tasks to return.
            skip: Number of tasks to skip.
            
        Returns:
            A list of tasks.
        """
        task_list = list(self.tasks.values())
        return task_list[skip:skip+limit]
        
    async def cancel_task(self, task_id: str) -> Task:
        """Cancel a task.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            The cancelled task.
            
        Raises:
            A2AServerError: If the task doesn't exist.
        """
        task = await self.get_task(task_id)
        if not task:
            raise A2AServerError(f"Task {task_id} not found")
            
        task.state = TaskState.CANCELED
        task.updatedAt = task.updatedAt  # Update timestamp
        return await self.update_task(task)


class A2ARequestContext:
    """Context for processing A2A requests."""
    
    def __init__(self, task: Task, message: Optional[Message] = None):
        """Initialize the request context.
        
        Args:
            task: The current task.
            message: The message being processed (if any).
        """
        self.task = task
        self.message = message
        self.metadata: Dict[str, Any] = {}


class A2AAgentExecutor:
    """Base class for executing agent logic in an A2A-compatible way."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute agent logic for a request.
        
        This method should be overridden by subclasses to implement the actual agent logic.
        
        Args:
            context: The request context.
            
        Returns:
            Either a complete Task or an AsyncIterator yielding TaskDelta objects.
            
        Raises:
            NotImplementedError: If not overridden by subclass.
        """
        raise NotImplementedError("Subclasses must implement execute")
    
    async def convert_message_to_standard(self, message: Message) -> StandardMessage:
        """Convert an A2A Message to an AILF StandardMessage.
        
        Args:
            message: The A2A Message to convert.
            
        Returns:
            An AILF StandardMessage.
        """
        # Extract text content from message parts
        text_parts = []
        for part in message.parts:
            if part.type == "text":
                text_parts.append(part.content)
        
        return StandardMessage(
            content="".join(text_parts) if text_parts else "",
            metadata={
                "role": message.role,
                "message_id": message.id,
                "created_at": message.createdAt,
                "a2a_message": message,
            }
        )
        
    async def convert_standard_to_message(self, std_message: StandardMessage, role: str = "assistant") -> Message:
        """Convert an AILF StandardMessage to an A2A Message.
        
        Args:
            std_message: The AILF StandardMessage to convert.
            role: The role of the message sender.
            
        Returns:
            An A2A Message.
        """
        return Message(
            role=role,
            parts=[MessagePart(type="text", content=std_message.content)]
        )


class AILFASA2AServer:
    """Base class for exposing AILF agents as A2A-compatible servers."""
    
    def __init__(self, 
                 agent_description: AgentDescription,
                 executor: A2AAgentExecutor,
                 task_store: Optional[TaskStore] = None):
        """Initialize the A2A server.
        
        Args:
            agent_description: The AILF agent description.
            executor: The agent executor that implements the agent logic.
            task_store: Optional task store implementation.
        """
        self.agent_description = agent_description
        self.executor = executor
        self.task_store = task_store or TaskStore()
        self.agent_card = agent_description.to_a2a_agent_card()
        
    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncIterator[None]:
        """FastAPI lifespan context manager.
        
        Args:
            app: The FastAPI application.
            
        Yields:
            None
        """
        # Startup logic
        logger.info("Starting A2A server")
        app.state.task_store = self.task_store
        app.state.executor = self.executor
        
        yield
        
        # Shutdown logic
        logger.info("Shutting down A2A server")
        
    def create_app(self) -> FastAPI:
        """Create a FastAPI application for the A2A server.
        
        Returns:
            A FastAPI application.
        """
        app = FastAPI(title=self.agent_description.agent_name, lifespan=self.lifespan)
        
        @app.get("/")
        async def get_agent_card() -> AgentCard:
            """Get the agent card."""
            return self.agent_card
            
        @app.post("/tasks")
        async def create_task() -> Dict[str, Any]:
            """Create a new task."""
            task = await self.task_store.create_task()
            return {"task": task.dict()}
            
        @app.get("/tasks")
        async def list_tasks(limit: int = 10, skip: int = 0) -> Dict[str, Any]:
            """List tasks."""
            tasks = await self.task_store.list_tasks(limit, skip)
            return {"tasks": [task.dict() for task in tasks]}
            
        @app.get("/tasks/{task_id}")
        async def get_task(task_id: str) -> Dict[str, Any]:
            """Get a task by ID."""
            task = await self.task_store.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            return {"task": task.dict()}
            
        @app.post("/tasks/{task_id}/cancel")
        async def cancel_task(task_id: str) -> Dict[str, Any]:
            """Cancel a task."""
            try:
                task = await self.task_store.cancel_task(task_id)
                return {"task": task.dict()}
            except A2AServerError as e:
                raise HTTPException(status_code=404, detail=str(e))
                
        @app.post("/tasks/{task_id}/messages")
        async def send_message(task_id: str, request: SendMessageRequest) -> Dict[str, Any]:
            """Send a message to a task."""
            task = await self.task_store.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
                
            # Update task with the new message
            task.messages.append(request.message)
            task.state = TaskState.RUNNING
            await self.task_store.update_task(task)
            
            try:
                # Create context and execute agent
                context = A2ARequestContext(task=task, message=request.message)
                result = await self.executor.execute(context)
                
                if isinstance(result, Task):
                    # Update task with result
                    await self.task_store.update_task(result)
                    return {"task": result.dict()}
                else:
                    # Should not happen for non-streaming endpoint
                    raise HTTPException(status_code=500, detail="Unexpected streaming result")
            except Exception as e:
                logger.exception("Error executing agent")
                task.state = TaskState.FAILED
                await self.task_store.update_task(task)
                raise HTTPException(status_code=500, detail=str(e))
                
        @app.post("/tasks/{task_id}/messages:stream")
        async def stream_message(task_id: str, request: SendMessageStreamingRequest) -> StreamingResponse:
            """Send a message to a task and stream the response."""
            task = await self.task_store.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
                
            # Update task with the new message
            task.messages.append(request.message)
            task.state = TaskState.RUNNING
            await self.task_store.update_task(task)
            
            async def event_generator():
                try:
                    # Create context and execute agent
                    context = A2ARequestContext(task=task, message=request.message)
                    result = await self.executor.execute(context)
                    
                    if isinstance(result, Task):
                        # Convert single result to stream
                        task_delta = TaskDelta(
                            id=result.id,
                            state=result.state,
                            messages=[],
                            done=True
                        )
                        yield {
                            "event": "delta",
                            "data": json.dumps({"task": task_delta.dict()})
                        }
                        # Update task with result
                        await self.task_store.update_task(result)
                    else:
                        # Stream deltas
                        async for delta in result:
                            yield {
                                "event": "delta",
                                "data": json.dumps({"task": delta.dict()})
                            }
                            
                            if delta.done:
                                # Final update to task
                                if delta.state:
                                    task.state = delta.state
                                await self.task_store.update_task(task)
                                break
                except Exception as e:
                    logger.exception("Error executing agent")
                    task.state = TaskState.FAILED
                    await self.task_store.update_task(task)
                    yield {
                        "event": "error",
                        "data": json.dumps({"detail": str(e)})
                    }
            
            return EventSourceResponse(event_generator())
            
        return app
        
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the A2A server.
        
        Args:
            host: The host to bind to.
            port: The port to bind to.
        """
        import uvicorn
        app = self.create_app()
        uvicorn.run(app, host=host, port=port)
