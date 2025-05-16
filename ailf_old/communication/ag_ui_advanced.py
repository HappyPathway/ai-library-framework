"""Advanced implementation of the AG-UI executor.

This module provides a more advanced implementation of the AG-UI executor
that integrates with AILF's AI engine, tool manager, and state manager.
"""

import asyncio
import json
import logging
import re
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
    StateSnapshotEvent,
)
from ailf.communication.ag_ui_server import AGUIExecutor, AGUIRequestContext
from ailf.communication.ag_ui_state import AGUIStateManager
from ailf.communication.ag_ui_tools import AGUIToolHandler

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


# Import ToolManager conditionally
try:
    from ailf.tooling.manager import ToolManager
except ImportError:
    # Create a placeholder ToolManager class for type checking
    class ToolManager:  # type: ignore
        """Placeholder for ToolManager."""
        async def execute_tool(self, tool_name: str, **kwargs) -> Any:
            """Placeholder for execute_tool method."""
            return {"result": f"Tool {tool_name} execution simulated"}


class AdvancedAGUIExecutor(AGUIExecutor):
    """An advanced implementation of the AG-UI executor.
    
    Integrates AILF's AI engine, tool manager, and state management.
    """
    
    def __init__(
        self, 
        ai_engine: AIEngine,
        tool_manager: Optional[ToolManager] = None,
        state_manager: Optional[AGUIStateManager] = None,
        delay: float = 0.01,  # Small delay between chunks for realistic streaming
        system_prompt: Optional[str] = None,
    ):
        """Initialize the executor.
        
        Args:
            ai_engine: The AI engine to use for generating responses
            tool_manager: Optional tool manager for tool execution
            state_manager: Optional state manager for state tracking
            delay: Delay between text chunks in seconds
            system_prompt: Optional system prompt to use
        """
        self.ai_engine = ai_engine
        self.tool_manager = tool_manager or ToolManager()
        self.state_manager = state_manager or AGUIStateManager()
        self.delay = delay
        self.system_prompt = system_prompt or (
            "You are an AI assistant integrated with a UI via the AG-UI protocol. "
            "You can respond to users and call tools when needed. "
            "To call a tool, format your response like this: [[tool_name::{'arg1': 'value1'}]]"
        )
        self.tool_handler = AGUIToolHandler(
            tool_manager=self.tool_manager,
            state_manager=self.state_manager,
        )
    
    async def execute(self, context: AGUIRequestContext) -> AsyncIterator[AgentEvent]:
        """Execute the agent logic for an AG-UI request.
        
        Args:
            context: The request context
            
        Yields:
            AG-UI events
        """
        try:
            # Emit run started event
            timestamp = int(datetime.now().timestamp() * 1000)
            yield RunStartedEvent(
                type=EventType.RUN_STARTED,
                run_id=context.run_id,
                timestamp=timestamp,
            )
            
            # Emit initial state snapshot
            yield self.state_manager.create_snapshot_event(timestamp=timestamp)
            
            # Convert AG-UI messages to AILF standard messages
            ailf_messages = await self.convert_messages_to_standard(
                context.input_data.messages
            )
            
            # Construct a prompt from the messages
            message_history = "\n".join([
                f"{msg.metadata.get('role', 'unknown')}: {msg.payload.text}"
                for msg in ailf_messages
            ])
            
            prompt = f"{self.system_prompt}\n\nMessage History:\n{message_history}\n\nassistant:"
            
            # Start a message
            message_id = str(uuid.uuid4())
            yield TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START,
                message_id=message_id,
                role="assistant",
                timestamp=timestamp,
            )
            
            # Generate and stream the response
            buffer = ""
            tool_pattern = r'\[\[([^:]+)::(\{.*?\})\]\]'
            
            try:
                async for chunk in self.ai_engine.generate_stream(prompt):
                    buffer += chunk
                    
                    # Check for complete tool calls in the buffer
                    match = re.search(tool_pattern, buffer)
                    if match:
                        # Extract pre-tool text
                        pre_tool_text = buffer[:match.start()]
                        if pre_tool_text:
                            # Emit the text before the tool call
                            yield TextMessageContentEvent(
                                type=EventType.TEXT_MESSAGE_CONTENT,
                                message_id=message_id,
                                content=pre_tool_text,
                                timestamp=int(datetime.now().timestamp() * 1000),
                            )
                        
                        # Extract tool call information
                        tool_name = match.group(1)
                        args_str = match.group(2)
                        
                        try:
                            # Parse tool arguments
                            tool_args = json.loads(args_str)
                            
                            # Execute the tool and yield events
                            async for event in self.tool_handler.execute_tool(
                                tool_name=tool_name,
                                args=tool_args,
                                context=context,
                            ):
                                yield event
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse tool args: {e}")
                            # Emit the raw text if JSON parsing fails
                            yield TextMessageContentEvent(
                                type=EventType.TEXT_MESSAGE_CONTENT,
                                message_id=message_id,
                                content=match.group(0),
                                timestamp=int(datetime.now().timestamp() * 1000),
                            )
                        
                        # Remove the processed part from the buffer
                        buffer = buffer[match.end():]
                    else:
                        # Process partial chunks that don't contain tool calls
                        # Only emit text up to the last complete sentence if tool pattern might be starting
                        if "[[" in buffer:
                            last_sentence_end = max(
                                buffer.rfind(". "), 
                                buffer.rfind("! "), 
                                buffer.rfind("? ")
                            )
                            
                            if last_sentence_end > 0:
                                # Emit text up to the last sentence end
                                yield TextMessageContentEvent(
                                    type=EventType.TEXT_MESSAGE_CONTENT,
                                    message_id=message_id,
                                    content=buffer[:last_sentence_end + 1],
                                    timestamp=int(datetime.now().timestamp() * 1000),
                                )
                                buffer = buffer[last_sentence_end + 1:]
                        else:
                            # No tool call starting, emit the whole buffer
                            yield TextMessageContentEvent(
                                type=EventType.TEXT_MESSAGE_CONTENT,
                                message_id=message_id,
                                content=buffer,
                                timestamp=int(datetime.now().timestamp() * 1000),
                            )
                            buffer = ""
                    
                    # Small delay to simulate realistic streaming
                    await asyncio.sleep(self.delay)
                
                # Emit any remaining buffer content
                if buffer:
                    yield TextMessageContentEvent(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        message_id=message_id,
                        content=buffer,
                        timestamp=int(datetime.now().timestamp() * 1000),
                    )
                    
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
            
            # Emit final state snapshot
            yield self.state_manager.create_snapshot_event(
                timestamp=int(datetime.now().timestamp() * 1000)
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
