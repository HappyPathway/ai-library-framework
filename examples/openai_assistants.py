#!/usr/bin/env python3
"""
OpenAI Assistants API Example

This example demonstrates how to use the AILF OpenAIEngine factory methods
for creating and interacting with OpenAI Assistants.
"""
import asyncio
import os
from typing import List

from dotenv import load_dotenv

from ailf.ai.openai_engine import OpenAIEngine
from ailf.schemas.openai_entities import Assistant, ThreadMessage


async def main() -> None:
    """Run the OpenAI Assistants API example."""
    # Load API key from environment
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment.")
        return
    
    # Initialize the OpenAI engine
    engine = OpenAIEngine(
        api_key=api_key,
        model="gpt-4o",
        config={
            "temperature": 0.7,
            "max_tokens": 1000
        }
    )
    
    # Create a new assistant
    assistant = await engine.create_assistant(
        name="Research Assistant",
        instructions="You are a helpful research assistant. Provide concise, accurate information with citations when available.",
        tools=[{"type": "code_interpreter"}]
    )
    
    print(f"Created assistant: {assistant}")
    
    # Use the high-level interaction method
    result = await engine.interact_with_assistant(
        assistant_id=assistant.id,
        message="What are the three main branches of machine learning?",
        wait_for_completion=True
    )
    
    # Print the assistant's response
    print_messages(result["messages"])
    
    # Continue the conversation in the same thread
    result = await engine.interact_with_assistant(
        assistant_id=assistant.id,
        message="Can you give me a simple code example of each?",
        thread_id=result["thread_id"],
        wait_for_completion=True
    )
    
    # Print the assistant's new response
    print_messages(result["messages"][:1])  # Just the latest message


def print_messages(messages: List[ThreadMessage]) -> None:
    """Print thread messages in a readable format.
    
    Args:
        messages: List of messages to print
    """
    for msg in messages:
        if msg.role == "assistant":
            print("\n=== Assistant ===")
            print(msg.get_content_text())
            print("================\n")
        elif msg.role == "user":
            print(f"User: {msg.get_content_text()}")


if __name__ == "__main__":
    asyncio.run(main())
