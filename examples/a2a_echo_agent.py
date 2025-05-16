"""Example of an A2A-compatible agent using AILF.

This example demonstrates how to create an A2A-compatible agent using the AILF framework.
The agent simply echoes back any messages it receives.
"""
import asyncio
import logging
from typing import AsyncIterator, Optional, Union

from ailf.communication import A2AAgentExecutor, A2ARequestContext, AILFASA2AServer
from ailf.schemas.agent import AgentDescription, CommunicationEndpoint
from ailf.schemas.a2a import (
    AgentCapabilities,
    MessageDelta,
    MessagePartDelta,
    Task,
    TaskDelta,
    TaskState,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EchoAgentExecutor(A2AAgentExecutor):
    """Example agent executor that echoes back messages."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute the agent logic.
        
        Args:
            context: The request context.
            
        Returns:
            Either a complete Task or an AsyncIterator yielding TaskDelta objects.
        """
        if not context.message:
            return context.task
            
        # Convert A2A message to AILF StandardMessage format
        ailf_message = await self.convert_message_to_standard(context.message)
        
        # For demonstration purposes, show both streaming and non-streaming responses
        # based on message content
        if "stream" in ailf_message.content.lower():
            # Return a generator for streaming response
            return self._stream_response(context, ailf_message.content)
        else:
            # Process the message
            response_content = f"Echo: {ailf_message.content}"
            logger.info(f"Responding with: {response_content}")
            
            # Convert response back to A2A message format
            a2a_response = await self.convert_standard_to_message(
                std_message=ailf_message.model_copy(update={"content": response_content})
            )
            
            # Add response to task messages
            context.task.messages.append(a2a_response)
            context.task.state = TaskState.COMPLETED
            
            return context.task
    
    async def _stream_response(self, context: A2ARequestContext, original_content: str) -> AsyncIterator[TaskDelta]:
        """Stream a response word by word.
        
        Args:
            context: The request context.
            original_content: The original message content.
            
        Yields:
            TaskDelta objects representing the streaming response.
        """
        # Initial response with metadata
        yield TaskDelta(
            id=context.task.id,
            state=TaskState.RUNNING,
            done=False
        )
        
        # Prepare streaming response
        response_text = f"Echo (streaming): {original_content}"
        words = response_text.split()
        
        for i, word in enumerate(words):
            # Simulate some processing time
            await asyncio.sleep(0.2)
            
            # Create a delta update
            yield TaskDelta(
                messages=[
                    MessageDelta(
                        role="assistant" if i == 0 else None,
                        parts=[
                            MessagePartDelta(
                                type="text" if i == 0 else None,
                                content=word + " "
                            )
                        ]
                    )
                ],
                done=(i == len(words) - 1)
            )
            
        # Final update to mark completion
        yield TaskDelta(
            state=TaskState.COMPLETED,
            done=True
        )

async def main():
    """Run the example agent."""
    # Create agent description
    agent_description = AgentDescription(
        agent_name="AILF Echo Agent",
        agent_type="echo",
        description="A simple echo agent that demonstrates A2A integration with AILF",
        supports_a2a=True,
        a2a_capabilities=AgentCapabilities(streaming=True),
        communication_endpoints=[
            CommunicationEndpoint(
                protocol="http",
                address="http://localhost:8000",
                details={"authentication": {"schemes": ["none"]}}
            )
        ]
    )
    
    # Create executor and server
    executor = EchoAgentExecutor()
    server = AILFASA2AServer(agent_description, executor)
    
    # Run the server
    server.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # We can't use asyncio.run() because server.run() is blocking
    # and doesn't return until the server is stopped
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(asyncio.gather(main()))
