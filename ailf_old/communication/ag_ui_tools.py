"""Tool integration for AG-UI protocol.

This module provides utilities for integrating tools with the AG-UI protocol.
"""

import inspect
import logging
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union

from ailf.schemas.ag_ui import (
    AgentEvent,
    EventType,
    ToolCallStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
)
from ailf.communication.ag_ui_server import AGUIRequestContext
from ailf.communication.ag_ui_state import AGUIStateManager

logger = logging.getLogger(__name__)

# Import ToolManager conditionally to avoid errors if it's not available
try:
    from ailf.tooling.manager import ToolManager
except ImportError:
    # Create a placeholder ToolManager class for type checking
    class ToolManager:  # type: ignore
        """Placeholder for ToolManager."""
        async def execute_tool(self, tool_name: str, **kwargs) -> Any:
            """Placeholder for execute_tool method."""
            return {"result": f"Tool {tool_name} execution simulated"}


class AGUIToolHandler:
    """Tool handler for AG-UI protocol.
    
    Integrates the AILF tool system with the AG-UI protocol.
    """
    
    def __init__(
        self, 
        tool_manager: Optional[ToolManager] = None,
        state_manager: Optional[AGUIStateManager] = None,
    ):
        """Initialize the tool handler.
        
        Args:
            tool_manager: Optional tool manager to use
            state_manager: Optional state manager to record tool results
        """
        self.tool_manager = tool_manager or ToolManager()
        self.state_manager = state_manager
    
    async def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: AGUIRequestContext,
    ) -> AsyncIterator[AgentEvent]:
        """Execute a tool and generate appropriate AG-UI events.
        
        Args:
            tool_name: Name of the tool to execute
            args: Arguments to pass to the tool
            context: The AG-UI request context
            
        Yields:
            AG-UI events for the tool execution
        """
        tool_call_id = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp() * 1000)
        
        # Emit tool call start event
        yield ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id=tool_call_id,
            name=tool_name,
            timestamp=timestamp,
        )
        
        # Emit tool call args event
        yield ToolCallArgsEvent(
            type=EventType.TOOL_CALL_ARGS,
            tool_call_id=tool_call_id,
            args=args,
            timestamp=timestamp,
        )
        
        try:
            # Execute the tool
            result = await self.tool_manager.execute_tool(tool_name, **args)
            
            # Update state if a state manager is provided
            if self.state_manager:
                state = self.state_manager.get_state()
                
                # Create a tools section in the state if it doesn't exist
                if "tools" not in state:
                    state["tools"] = {}
                
                # Record the tool result in the state
                if "results" not in state["tools"]:
                    state["tools"]["results"] = {}
                
                state["tools"]["results"][tool_call_id] = {
                    "name": tool_name,
                    "args": args,
                    "result": result,
                    "timestamp": timestamp,
                }
                
                self.state_manager.update_state(state)
                
                # Yield state snapshot event
                yield self.state_manager.create_snapshot_event(timestamp=timestamp)
            
            # Emit tool call end event with result
            yield ToolCallEndEvent(
                type=EventType.TOOL_CALL_END,
                tool_call_id=tool_call_id,
                output=result,
                timestamp=timestamp,
            )
            
        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}: {e}")
            
            # Update state if a state manager is provided
            if self.state_manager:
                state = self.state_manager.get_state()
                
                if "tools" not in state:
                    state["tools"] = {}
                    
                if "errors" not in state["tools"]:
                    state["tools"]["errors"] = {}
                
                state["tools"]["errors"][tool_call_id] = {
                    "name": tool_name,
                    "args": args,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": timestamp,
                }
                
                self.state_manager.update_state(state)
                
                # Yield state snapshot event
                yield self.state_manager.create_snapshot_event(timestamp=timestamp)
            
            # Emit tool call end event with error
            yield ToolCallEndEvent(
                type=EventType.TOOL_CALL_END,
                tool_call_id=tool_call_id,
                output=None,
                error={
                    "message": str(e),
                    "type": type(e).__name__,
                },
                timestamp=timestamp,
            )
