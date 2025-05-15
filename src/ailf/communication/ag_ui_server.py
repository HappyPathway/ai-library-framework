"""FastAPI wrapper base classes for AG-UI servers.

This module provides base classes and utilities for creating AG-UI-compatible
FastAPI servers that integrate with AILF agents.
"""
import json
import logging
import uuid
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Type, Union

from fastapi import FastAPI, HTTPException, Request, Response, Depends, APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ValidationError

from ailf.schemas.agent import AgentDescription
from ailf.schemas.interaction import StandardMessage, TextMessage, TextMessagePayload
from ailf.schemas.ag_ui import (
    AgentEvent,
    EventType,
    Message,
    RunAgentInput,
    RunAgentOutput,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    StateSnapshotEvent,
    StateDeltaEvent,
)

logger = logging.getLogger(__name__)


class AGUIServerError(Exception):
    """Base exception for AG-UI server errors."""
    pass


class AGUIRequestContext:
    """Context for an AG-UI request.
    
    Used to store state between request parsing and response generation.
    """
    
    def __init__(
        self, 
        request_id: str,
        run_id: str,
        input_data: RunAgentInput,
        agent_description: Optional[AgentDescription] = None,
    ):
        """Initialize the request context.
        
        Args:
            request_id: Unique identifier for the request
            run_id: Unique identifier for the run
            input_data: The input data from the client
            agent_description: Optional agent description
        """
        self.request_id = request_id
        self.run_id = run_id
        self.input_data = input_data
        self.agent_description = agent_description
        self.sequence_number = 0
        self.state: Dict[str, Any] = {}
    
    def next_sequence(self) -> int:
        """Get the next sequence number and increment the counter.
        
        Returns:
            The next sequence number
        """
        current = self.sequence_number
        self.sequence_number += 1
        return current


class AGUIExecutor:
    """Base class for AG-UI executors.
    
    Executors handle the actual processing of AG-UI requests and generate
    response events. Custom executors should inherit from this class and
    implement the execute method.
    """
    
    async def execute(self, context: AGUIRequestContext) -> AsyncIterator[AgentEvent]:
        """Execute the agent logic for an AG-UI request.
        
        Args:
            context: The request context
            
        Returns:
            An async iterator of events to send to the client
            
        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        raise NotImplementedError("Subclasses must implement execute")
    
    async def convert_messages_to_standard(
        self, messages: List[Message]
    ) -> List[StandardMessage]:
        """Convert AG-UI messages to AILF StandardMessage format.
        
        Args:
            messages: AG-UI messages to convert
            
        Returns:
            Converted AILF StandardMessage objects
        """
        result = []
        
        for msg in messages:
            if msg.content is not None:
                result.append(TextMessage(
                    payload=TextMessagePayload(text=msg.content),
                    metadata={
                        "role": msg.role,
                        "ag_ui_message_id": msg.id,
                    }
                ))
        
        return result


class AILFAsAGUIServer:
    """Server for exposing AILF agents as AG-UI-compatible endpoints.
    
    This class wraps an AILF agent and exposes it via a FastAPI router
    using the AG-UI protocol.
    """
    
    def __init__(
        self,
        executor: AGUIExecutor,
        agent_description: AgentDescription,
        router: Optional[APIRouter] = None,
    ):
        """Initialize the AG-UI server.
        
        Args:
            executor: The executor to handle AG-UI requests
            agent_description: Description of the agent being exposed
            router: Optional FastAPI router to attach routes to
        """
        self.executor = executor
        self.agent_description = agent_description
        self.router = router or APIRouter()
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up the FastAPI routes for the AG-UI server."""
        
        @self.router.get("/v1/agent")
        async def get_agent():
            """Get information about the agent."""
            supports_tools = getattr(self.agent_description, "supports_tools", False)
            return {
                "id": self.agent_description.id,
                "name": self.agent_description.name,
                "description": self.agent_description.description,
                "capabilities": {
                    "streaming": True,
                    "tools": supports_tools,
                    "file_upload": False,  # Could be configurable in the future
                    "image_generation": False,  # Could be configurable in the future
                },
                "metadata": getattr(self.agent_description, "metadata", {}) or {},
            }
        
        @self.router.post("/v1/run")
        async def run_agent(request: Request):
            """Run the agent with the specified messages."""
            try:
                body = await request.json()
                input_data = RunAgentInput.model_validate(body)
            except ValidationError as e:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Invalid request data: {e}"}
                )
            except Exception as e:
                logger.exception("Error parsing request body")
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Could not parse request body: {e}"}
                )
            
            request_id = str(uuid.uuid4())
            run_id = str(uuid.uuid4())
            
            context = AGUIRequestContext(
                request_id=request_id,
                run_id=run_id,
                input_data=input_data,
                agent_description=self.agent_description,
            )
            
            if input_data.stream:
                return StreamingResponse(
                    self._stream_response(context),
                    media_type="text/event-stream",
                )
            else:
                # Non-streaming response
                return await self._collect_response(context)
    
    async def _stream_response(self, context: AGUIRequestContext) -> AsyncIterator[str]:
        """Stream AG-UI events as server-sent events.
        
        Args:
            context: The request context
            
        Yields:
            Server-sent event strings
        """
        try:
            # Send initial connection event
            yield "event: connected\ndata: {}\n\n"
            
            async for event in self.executor.execute(context):
                event_json = event.model_dump(by_alias=True)
                yield f"data: {json.dumps(event_json)}\n\n"
            
            # Send done event
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception(f"Error in streaming response: {e}")
            error_event = RunErrorEvent(
                type=EventType.RUN_ERROR,
                run_id=context.run_id,
                error=str(e),
                timestamp=int(datetime.now().timestamp() * 1000),
            )
            yield f"data: {json.dumps(error_event.model_dump(by_alias=True))}\n\n"
    
    async def _collect_response(self, context: AGUIRequestContext) -> JSONResponse:
        """Collect all events for a non-streaming response.
        
        Args:
            context: The request context
            
        Returns:
            JSONResponse with the collected response
        """
        messages = []
        current_message = None
        
        try:
            async for event in self.executor.execute(context):
                if event.type == EventType.TEXT_MESSAGE_START:
                    event = event  # type: TextMessageStartEvent
                    current_message = {
                        "id": event.message_id,
                        "role": event.role,
                        "content": "",
                    }
                elif event.type == EventType.TEXT_MESSAGE_CONTENT and current_message:
                    event = event  # type: TextMessageContentEvent
                    current_message["content"] += event.content
                elif event.type == EventType.TEXT_MESSAGE_END and current_message:
                    messages.append(current_message)
                    current_message = None
            
            # Add the last message if it wasn't ended
            if current_message:
                messages.append(current_message)
            
            return JSONResponse({
                "task_id": context.run_id,
                "messages": messages,
                "metadata": context.input_data.metadata,
            })
        except Exception as e:
            logger.exception(f"Error in non-streaming response: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(e),
                    "type": type(e).__name__,
                }
            )
