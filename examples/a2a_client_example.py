"""Example of an A2A client using AILF.

This example demonstrates how to use the AILF A2A client to interact with
an A2A-compatible agent.
"""
import asyncio
import logging
from typing import Optional

from ailf.communication import A2AClient
from ailf.schemas.a2a import Message, MessagePart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main(agent_url: str, stream: bool = True):
    """Run the example client.
    
    Args:
        agent_url: The URL of the A2A agent to connect to.
        stream: Whether to use streaming or regular responses.
    """
    # Create client
    client = A2AClient(base_url=agent_url)
    
    try:
        # Get agent card
        agent_card = await client.get_agent_card()
        logger.info(f"Connected to agent: {agent_card.name}")
        logger.info(f"Description: {agent_card.description}")
        logger.info(f"Streaming support: {agent_card.capabilities.streaming}")
        
        # Create a new task
        task = await client.create_task()
        logger.info(f"Created task: {task.id}")
        
        # Prepare message
        content = "Hello, agent! Please stream this response." if stream else "Hello, agent!"
        message = Message(
            role="user",
            parts=[
                MessagePart(type="text", content=content)
            ]
        )
        
        if stream and agent_card.capabilities.streaming:
            # Use streaming response
            logger.info("Sending message with streaming response...")
            print("\nAGENT: ", end="", flush=True)
            
            async for delta in client.stream_message(task.id, message):
                if delta.messages and delta.messages[0].parts:
                    for part in delta.messages[0].parts:
                        if part.content:
                            print(part.content, end="", flush=True)
                
                if delta.done:
                    print("\nStreaming complete!")
        else:
            # Use regular response
            logger.info("Sending message...")
            updated_task = await client.send_message(task.id, message)
            
            if updated_task.messages and len(updated_task.messages) > 1:
                response = updated_task.messages[-1]
                content = "".join(part.content for part in response.parts if part.type == "text")
                print(f"\nAGENT: {content}")
            else:
                logger.warning("No response received from agent.")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    # Default to the echo agent example
    agent_url = "http://localhost:8000"
    asyncio.run(main(agent_url))
