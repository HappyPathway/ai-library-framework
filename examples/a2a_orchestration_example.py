"""Example showing how to use the A2A orchestration module.

This example demonstrates how to set up and use the A2A orchestration module to
coordinate multiple agents in various patterns including:
- Sequential routing between agents
- Conditional routing based on message content
- Parallel task processing
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_orchestration import (
    A2AOrchestrator,
    AgentRoute,
    OrchestrationConfig,
    ParallelTaskGroup,
    RouteCondition,
    RouteType,
    SequentialTaskChain,
)
from ailf.communication.a2a_registry import A2ARegistryManager, A2ARegistry, A2ARegistryClient, RegistryEntry
from ailf.schemas.a2a import Message, MessagePart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def setup_registry():
    """Set up a registry with some test agents."""
    # Create a local registry
    registry = A2ARegistry()
    
    # Register some agents
    registry.register_agent(RegistryEntry(
        id="general-agent",
        name="General Assistant",
        description="A general-purpose agent that can handle a variety of tasks",
        url="http://localhost:8001",
        provider={"name": "AILF", "url": "https://example.com"},
        capabilities={"streaming": True}
    ))
    
    registry.register_agent(RegistryEntry(
        id="calculator-agent",
        name="Calculator",
        description="An agent specialized in mathematical calculations",
        url="http://localhost:8002",
        provider={"name": "AILF", "url": "https://example.com"},
        capabilities={"streaming": False},
        skills=[{"name": "calculator", "description": "Mathematical calculations"}]
    ))
    
    registry.register_agent(RegistryEntry(
        id="search-agent",
        name="Search Agent",
        description="An agent specialized in searching and retrieving information",
        url="http://localhost:8003",
        provider={"name": "AILF", "url": "https://example.com"},
        capabilities={"streaming": True},
        skills=[{"name": "search", "description": "Information retrieval and search"}]
    ))
    
    registry.register_agent(RegistryEntry(
        id="summarization-agent",
        name="Summarization Agent",
        description="An agent specialized in summarizing text",
        url="http://localhost:8004",
        provider={"name": "AILF", "url": "https://example.com"},
        capabilities={"streaming": False},
        skills=[{"name": "summarize", "description": "Text summarization"}]
    ))
    
    # Create a registry manager with the local registry
    registry_manager = A2ARegistryManager(local_registry=registry)
    
    return registry_manager


async def setup_orchestrator(registry_manager):
    """Set up an orchestrator with routing rules."""
    # Define routing configuration
    config = OrchestrationConfig(
        routes=[
            # Route from general agent to specialized agents based on content
            AgentRoute(
                source_agent="general-agent",
                type=RouteType.CONDITIONAL,
                conditions=[
                    RouteCondition(
                        field="messages[-1].parts[0].content",
                        operator="contains",
                        value="calculate",
                        route_to="calculator-agent"
                    ),
                    RouteCondition(
                        field="messages[-1].parts[0].content",
                        operator="contains",
                        value="search",
                        route_to="search-agent"
                    ),
                    RouteCondition(
                        field="messages[-1].parts[0].content",
                        operator="contains",
                        value="summarize",
                        route_to="summarization-agent"
                    )
                ]
            ),
            # Route from calculator back to general agent
            AgentRoute(
                source_agent="calculator-agent",
                type=RouteType.SEQUENTIAL,
                destination_agents=["general-agent"]
            ),
            # Route from search agent to summarization agent
            AgentRoute(
                source_agent="search-agent",
                type=RouteType.SEQUENTIAL,
                destination_agents=["summarization-agent"]
            )
        ],
        entry_points=["general-agent"]
    )
    
    # Create orchestrator with the config and registry
    orchestrator = A2AOrchestrator(config, registry_manager=registry_manager)
    
    return orchestrator


async def demo_conditional_routing(orchestrator):
    """Demonstrate conditional routing between agents."""
    logging.info("Starting conditional routing demo")
    
    # Create a task at the general agent (entry point)
    task = await orchestrator.create_task("general-agent")
    logging.info(f"Created task {task.id} at general-agent")
    
    # Send a message that should route to the calculator agent
    message = Message(
        role="user",
        parts=[MessagePart(type="text", content="Can you calculate 123 * 456 for me?")]
    )
    
    logging.info("Sending message requiring calculation...")
    response = await orchestrator.send_message(task.id, message)
    
    # At this point, the task should have been routed to the calculator agent
    handler = orchestrator.task_handlers[task.id]
    logging.info(f"Task is now with agent: {handler.current_agent}")
    logging.info(f"Routing history: {handler.history}")
    
    # Print the last message from the response
    if response.messages:
        last_message = response.messages[-1]
        content = last_message.parts[0].content if last_message.parts else ""
        logging.info(f"Last message: {content}")
    
    return task.id


async def demo_sequential_chain(orchestrator):
    """Demonstrate a sequential chain of agents."""
    logging.info("\nStarting sequential chain demo")
    
    # Create a sequence of agents
    agent_sequence = ["general-agent", "search-agent", "summarization-agent"]
    
    # Create a sequential chain
    chain = SequentialTaskChain(orchestrator, agent_sequence)
    
    # Start the chain at the first agent
    task = await chain.start_chain()
    logging.info(f"Created sequential task chain with ID {task.id}")
    
    # Send a message that will be processed by all agents in sequence
    message = Message(
        role="user",
        parts=[MessagePart(
            type="text", 
            content="Please search for information about A2A protocol and summarize it"
        )]
    )
    
    logging.info("Sending message through the agent chain...")
    response = await chain.send_message(message)
    
    # Print the chain's progression
    logging.info(f"Chain progressed to index {chain.current_index} of {len(agent_sequence)}")
    
    # Print conversation history
    history = chain.get_conversation_history()
    logging.info("Conversation history across agents:")
    for i, entry in enumerate(history):
        agent = entry.get("agent_id", "unknown")
        role = entry.get("role", "unknown")
        content = entry.get("content", [""])[0]
        logging.info(f"[{agent}] {role}: {content[:50]}...")  # Truncate for brevity
    
    return task.id


async def demo_parallel_tasks(orchestrator):
    """Demonstrate parallel task processing with multiple agents."""
    logging.info("\nStarting parallel tasks demo")
    
    # Create a parallel task group
    group = ParallelTaskGroup(orchestrator)
    
    # Create tasks on multiple specialized agents
    agents = ["calculator-agent", "search-agent", "summarization-agent"]
    tasks = await group.create_tasks(agents)
    
    logging.info(f"Created {len(tasks)} parallel tasks")
    
    # Send the same query to all agents
    message = Message(
        role="user",
        parts=[MessagePart(type="text", content="What can you help me with?")]
    )
    
    logging.info("Sending message to all agents in parallel...")
    results = await group.send_message_to_all(message)
    
    # Collect results from all agents
    logging.info("Collecting results from all agents...")
    all_results = await group.collect_results()
    
    # Print results from each agent
    for agent_id, agent_results in all_results.items():
        logging.info(f"\nResults from {agent_id}:")
        for result in agent_results:
            content = result.get("content", [""])[0]
            logging.info(f"Response: {content[:100]}...")  # Truncate for brevity
    
    return group


async def main():
    """Run the orchestration examples."""
    # Set up registry and orchestrator
    registry_manager = await setup_registry()
    orchestrator = await setup_orchestrator(registry_manager)
    
    # Mock the A2AClient to simulate agent responses
    # In a real implementation, these would be actual A2A agents
    with patch("ailf.communication.a2a_orchestration.A2AClient") as mock_client_class:
        # Create a mock client that returns appropriate responses
        mock_client = MagicMock()
        
        # Define behavior for create_task
        mock_client.create_task = AsyncMock(side_effect=[
            # For conditional routing demo
            Task(id="task1", state="created", messages=[]),
            # For sequential chain demo
            Task(id="task2", state="created", messages=[]),
            # For parallel tasks demo (3 agents)
            Task(id="task3", state="created", messages=[]),
            Task(id="task4", state="created", messages=[]),
            Task(id="task5", state="created", messages=[]),
        ])
        
        # Define behavior for send_message
        mock_client.send_message = AsyncMock(side_effect=[
            # For conditional routing demo - general agent response
            Task(
                id="task1", 
                state="completed", 
                messages=[
                    Message(
                        role="user",
                        parts=[MessagePart(type="text", content="Can you calculate 123 * 456 for me?")]
                    ),
                    Message(
                        role="assistant",
                        parts=[MessagePart(type="text", content="I'll route you to our calculator agent")]
                    )
                ]
            ),
            # Calculator agent response
            Task(
                id="task1-calc", 
                state="completed", 
                messages=[
                    Message(
                        role="user",
                        parts=[MessagePart(type="text", content="Can you calculate 123 * 456 for me?")]
                    ),
                    Message(
                        role="assistant",
                        parts=[MessagePart(type="text", content="123 * 456 = 56,088")]
                    )
                ]
            ),
            # For sequential chain - general agent
            Task(
                id="task2", 
                state="completed", 
                messages=[
                    Message(
                        role="user",
                        parts=[MessagePart(type="text", content="Please search for information about A2A protocol and summarize it")]
                    ),
                    Message(
                        role="assistant",
                        parts=[MessagePart(type="text", content="I'll search for information on A2A protocol")]
                    )
                ]
            ),
            # Search agent
            Task(
                id="task2-search", 
                state="completed", 
                messages=[
                    Message(
                        role="user",
                        parts=[MessagePart(type="text", content="Please search for information about A2A protocol and summarize it")]
                    ),
                    Message(
                        role="assistant",
                        parts=[MessagePart(type="text", content="Here is detailed information about A2A protocol: [lengthy content about A2A]")]
                    )
                ]
            ),
            # Summarization agent
            Task(
                id="task2-summary", 
                state="completed", 
                messages=[
                    Message(
                        role="user",
                        parts=[MessagePart(type="text", content="Please search for information about A2A protocol and summarize it")]
                    ),
                    Message(
                        role="assistant",
                        parts=[MessagePart(type="text", content="Summary: A2A (Agent-to-Agent) protocol is a standard for enabling interoperability between AI agents...")]
                    )
                ]
            ),
            # For parallel tasks - calculator
            Task(
                id="task3", 
                state="completed", 
                messages=[
                    Message(
                        role="user",
                        parts=[MessagePart(type="text", content="What can you help me with?")]
                    ),
                    Message(
                        role="assistant",
                        parts=[MessagePart(type="text", content="I can help with mathematical calculations including arithmetic, algebra, and more.")]
                    )
                ]
            ),
            # Search agent
            Task(
                id="task4", 
                state="completed", 
                messages=[
                    Message(
                        role="user",
                        parts=[MessagePart(type="text", content="What can you help me with?")]
                    ),
                    Message(
                        role="assistant",
                        parts=[MessagePart(type="text", content="I can search for information and retrieve relevant facts and data.")]
                    )
                ]
            ),
            # Summarization agent
            Task(
                id="task5", 
                state="completed", 
                messages=[
                    Message(
                        role="user",
                        parts=[MessagePart(type="text", content="What can you help me with?")]
                    ),
                    Message(
                        role="assistant",
                        parts=[MessagePart(type="text", content="I can summarize long texts into concise, easy-to-understand summaries.")]
                    )
                ]
            ),
        ])
        
        # Mock get_task to return the same as send_message
        mock_client.get_task = mock_client.send_message
        
        # Configure the mock client to be returned when A2AClient is instantiated
        mock_client_class.return_value = mock_client
        
        # Run the demos
        try:
            # Run conditional routing demo
            task_id1 = await demo_conditional_routing(orchestrator)
            logging.info(f"Conditional routing demo completed with task {task_id1}\n")
            
            # Run sequential chain demo
            task_id2 = await demo_sequential_chain(orchestrator)
            logging.info(f"Sequential chain demo completed with task {task_id2}\n")
            
            # Run parallel tasks demo
            group = await demo_parallel_tasks(orchestrator)
            logging.info(f"Parallel tasks demo completed with {len(group.tasks)} tasks\n")
            
            logging.info("All demos completed successfully")
            
        except Exception as e:
            logging.error(f"Error during demos: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # For this example, we need to mock responses since we don't have actual A2A agents running
    from unittest.mock import AsyncMock, MagicMock, patch
    from ailf.schemas.a2a import Task
    
    # Run the async main function
    asyncio.run(main())
