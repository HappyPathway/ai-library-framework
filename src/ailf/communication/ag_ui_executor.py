"""Simple implementation of the AG-UI executor.

This module provides a simple implementation of the AG-UI executor
that integrates with AILF's AI engine.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from ailf.schemas.ag_ui import (
    AgentEvent,
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    StateSnapshotEvent,
)
from ailf.communication.ag_ui_server import AGUIExecutor, AGUIRequestContext
from ailf.schemas.interaction import StandardMessage

logger = logging.getLogger(__name__)

# Import AIEngine conditionally to avoid errors if it's not available
try:
    from ailf.ai.engine import AIEngine
except ImportError:
    # Create a placeholder AIEngine class for type checking
    class AIEngine:  # type: ignore
        """Placeholder for AIEngine."""
        async def generate_stream(self, prompt: str, **kwargs):
            """Placeholder for generate_stream method."""
            yield "This is a placeholder response."


class SimpleAGUIExecutor(AGUIExecutor):
    """A simple implementation of the AG-UI executor using AILF's AI engine."""
    
    def __init__(
        self, 
        ai_engine: AIEngine,
        delay: float = 0.01,  # Small delay between chunks for realistic streaming
    ):
        """Initialize the executor.
        
        Args:
            ai_engine: The AI engine to use for generating responses
            delay: Delay between text chunks in seconds
        """
        self.ai_engine = ai_engine
        self.delay = delay
    
    async def execute(self, context: AGUIRequestContext) -> AsyncIterator[AgentEvent]:
        """Execute the agent logic for an AG-UI request.
        
        Args:
            context: The request context
            
        Yields:
            AG-UI events
        """
        try:
            # Emit run started event
            yield RunStartedEvent(
                type=EventType.RUN_STARTED,
                run_id=context.run_id,
                timestamp=int(datetime.now().timestamp() * 1000),
            )
            
            # Emit initial state snapshot (empty state)
            yield StateSnapshotEvent(
                type=EventType.STATE_SNAPSHOT,
                state={},
                timestamp=int(datetime.now().timestamp() * 1000),
            )
            
            # Convert AG-UI messages to AILF standard messages
            ailf_messages = await self.convert_messages_to_standard(
                context.input_data.messages
            )
            
            # Construct a prompt from the messages
            prompt = "\n".join([
                f"{msg.metadata.get('role', 'unknown')}: {msg.payload.text}"
                for msg in ailf_messages
            ])
            
            # Start a message
            message_id = str(uuid.uuid4())
            yield TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=message_id,
                role="assistant",
                timestamp=int(datetime.now().timestamp() * 1000),
            )
            
            # Generate and stream the response
            try:
                async for chunk in self.ai_engine.generate_stream(prompt):
                    # Check if chunk contains a tool call pattern
                    if chunk.startswith("[[") and "::" in chunk and chunk.endswith("]]"):
                        # Extract tool call information
                        tool_info = chunk.strip("[]").split("::", 1)
                        if len(tool_info) == 2:
                            tool_name, args_str = tool_info
                            
                            try:
                                # Parse tool arguments
                                tool_args = json.loads(args_str)
                                
                                # Generate a tool call
                                tool_call_id = str(uuid.uuid4())
                                
                                # Emit tool call start
                                yield ToolCallStartEvent(
                                    type=EventType.TOOL_CALL_START,
                                    tool_call_id=tool_call_id,
                                    name=tool_name,
                                    timestamp=int(datetime.now().timestamp() * 1000),
                                )
                                
                                # Emit tool call args
                                yield ToolCallArgsEvent(
                                    type=EventType.TOOL_CALL_ARGS,
                                    tool_call_id=tool_call_id,
                                    args=tool_args,
                                    timestamp=int(datetime.now().timestamp() * 1000),
                                )
                                
                                # For this simple implementation, just return success
                                # In a real implementation, you would actually call the tool
                                yield ToolCallEndEvent(
                                    type=EventType.TOOL_CALL_END,
                                    tool_call_id=tool_call_id,
                                    output={"result": "Tool execution simulated"},
                                    timestamp=int(datetime.now().timestamp() * 1000),
                                )
                                
                                # Skip emitting this chunk as text
                                continue
                            except json.JSONDecodeError:
                                # If JSON parsing fails, treat as regular text
                                pass
                    
                    # Emit the text chunk
                    yield TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=message_id,
                        content=chunk,
                        timestamp=int(datetime.now().timestamp() * 1000),
                    )
                    
                    # Small delay to simulate realistic streaming
                    await asyncio.sleep(self.delay)
                    
            except Exception as e:
                logger.exception(f"Error generating response: {e}")
                yield RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    run_id=context.run_id,
                    error=str(e),
                    timestamp=int(datetime.now().timestamp() * 1000),
                )
                return
            
            # End the message
            yield TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END,
                message_id=message_id,
                timestamp=int(datetime.now().timestamp() * 1000),
            )
            
            # Emit run finished event
            yield RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                run_id=context.run_id,
                timestamp=int(datetime.now().timestamp() * 1000),
            )
            
        except Exception as e:
            logger.exception(f"Error in execution: {e}")
            yield RunErrorEvent(
                type=EventType.RUN_ERROR,
                run_id=context.run_id,
                error=str(e),
                timestamp=int(datetime.now().timestamp() * 1000),
            )
