"""AG-UI Protocol client implementation for AILF.

This module provides a client for interacting with AG-UI-compatible agents.
"""
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from uuid import uuid4

import httpx
import asyncio
from pydantic import ValidationError

from ailf.schemas.ag_ui import (
    AgentEvent,
    EventType,
    Message,
    RunAgentInput,
    RunAgentOutput,
    TextMessageContentEvent,
)

logger = logging.getLogger(__name__)


class AGUIClientError(Exception):
    """Base exception for AG-UI client errors."""
    pass


class AGUIHTTPError(AGUIClientError):
    """Exception raised when an HTTP error occurs."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class AGUIJSONError(AGUIClientError):
    """Exception raised when JSON parsing fails."""
    pass


class AGUIClient:
    """Client for interacting with AG-UI compatible agents."""
    
    def __init__(
        self, 
        base_url: str,
        timeout: float = 60.0,
    ):
        """Initialize the AG-UI client.
        
        Args:
            base_url: The base URL of the AG-UI agent
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._http_client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close the client and release resources."""
        await self._http_client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the agent.
        
        Returns:
            Agent information including capabilities.
            
        Raises:
            AGUIHTTPError: If the HTTP request fails
            AGUIJSONError: If JSON parsing fails
        """
        url = f"{self.base_url}/v1/agent"
        
        try:
            response = await self._http_client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise AGUIHTTPError(e.response.status_code, e.response.text) from e
        except json.JSONDecodeError as e:
            raise AGUIJSONError(f"Failed to parse JSON response: {e}") from e
        except httpx.RequestError as e:
            raise AGUIClientError(f"Request failed: {e}") from e
    
    async def run_agent(
        self,
        messages: List[Message],
        metadata: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> Union[RunAgentOutput, AsyncGenerator[AgentEvent, None]]:
        """Run an agent with the specified messages.
        
        Args:
            messages: List of messages to send
            metadata: Optional metadata to include
            stream: Whether to stream the response
            
        Returns:
            If stream is True, returns an async generator of events
            If stream is False, returns the complete response
            
        Raises:
            AGUIHTTPError: If the HTTP request fails
            AGUIJSONError: If JSON parsing fails
        """
        url = f"{self.base_url}/v1/run"
        
        request_data = RunAgentInput(
            messages=messages,
            metadata=metadata or {},
            stream=stream,
        )
        
        try:
            if stream:
                response = await self._http_client.post(
                    url, 
                    json=request_data.model_dump(by_alias=True),
                    headers={"Accept": "text/event-stream"}
                )
                response.raise_for_status()
                return self._parse_event_stream(response)
            else:
                response = await self._http_client.post(
                    url,
                    json=request_data.model_dump(by_alias=True),
                )
                response.raise_for_status()
                return RunAgentOutput.model_validate(response.json())
        except httpx.HTTPStatusError as e:
            raise AGUIHTTPError(e.response.status_code, e.response.text) from e
        except json.JSONDecodeError as e:
            raise AGUIJSONError(f"Failed to parse JSON response: {e}") from e
        except httpx.RequestError as e:
            raise AGUIClientError(f"Request failed: {e}") from e
    
    async def _parse_event_stream(
        self, response: httpx.Response
    ) -> AsyncGenerator[AgentEvent, None]:
        """Parse an event stream from an HTTP response.
        
        Args:
            response: HTTP response containing the event stream
            
        Yields:
            AgentEvent objects parsed from the stream
            
        Raises:
            AGUIJSONError: If JSON parsing fails
        """
        buffer = ""
        
        async for chunk in response.aiter_text():
            buffer += chunk
            
            while "\n\n" in buffer:
                event_text, buffer = buffer.split("\n\n", 1)
                event_lines = event_text.strip().split("\n")
                
                event_data = None
                event_type = None
                
                for line in event_lines:
                    if line.startswith("data: "):
                        event_data = line[len("data: "):]
                    elif line.startswith("event: "):
                        event_type = line[len("event: "):]
                
                if not event_data or event_data == "[DONE]":
                    continue
                    
                try:
                    event_json = json.loads(event_data)
                    event_type = event_json.get("type")
                    
                    # Convert to the appropriate event model
                    if event_type == EventType.TEXT_MESSAGE_CONTENT:
                        yield TextMessageContentEvent.model_validate(event_json)
                    else:
                        # Generic fallback that will attempt to validate against AgentEvent
                        yield AgentEvent.model_validate(event_json)
                except json.JSONDecodeError as e:
                    raise AGUIJSONError(f"Failed to parse event JSON: {e}") from e
                except ValidationError as e:
                    logger.warning(f"Failed to validate event: {e}")
                    # Continue processing other events even if one fails to validate
                    continue
