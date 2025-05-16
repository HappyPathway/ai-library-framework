"""Example of A2A multi-agent orchestration using the AILF framework.

This example demonstrates how to orchestrate multiple A2A-compatible agents
in a workflow using the A2A orchestration components.
"""
import asyncio
import logging
from typing import List

from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_orchestration import (
    A2AOrchestrator,
    AgentRoute,
    OrchestrationConfig,
    RouteCondition,
    RouteType,
    ParallelTaskGroup,
    SequentialTaskChain,
)
from ailf.communication.a2a_registry import A2ARegistryManager
from ailf.schemas.a2a import Message, MessagePart

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs of our agents (in a real scenario, these would be discovered through a registry)
GENERAL_AGENT_URL = "http://localhost:8000"
RESEARCH_AGENT_URL = "http://localhost:8001"
CALCULATOR_AGENT_URL = "http://localhost:8002"
SUMMARIZATION_AGENT_URL = "http://localhost:8003"

async def demonstrate_conditional_routing():
    """Demonstrate conditional routing between agents based on message content."""
    logger.info("Starting conditional routing example...")
    
    # Define agent routing configuration
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
                        value="research",
                        route_to="research-agent"
                    ),
                ]
            ),
            # Return to general agent when done with calculator
            AgentRoute(
                source_agent="calculator-agent",
                type=RouteType.SEQUENTIAL,
                destination_agents=["general-agent"]
            ),
            # Return to general agent when done with research
            AgentRoute(
                source_agent="research-agent",
                type=RouteType.SEQUENTIAL,
                destination_agents=["general-agent"]
            )
        ],
        entry_points=["general-agent"]
    )
    
    # Set up registry manager with agent URLs
    registry = A2ARegistryManager()
    # In a real implementation, we would discover these agents through a registry
    # For this example, we'll manually map agent names to URLs
    agent_urls = {
        "general-agent": GENERAL_AGENT_URL,
        "calculator-agent": CALCULATOR_AGENT_URL,
        "research-agent": RESEARCH_AGENT_URL,
    }
    
    # Create orchestrator
    orchestrator = A2AOrchestrator(
        config=config,
        registry_manager=registry,
        agent_url_map=agent_urls
    )
    
    # Create a task at the entry point
    task = await orchestrator.create_task("general-agent")
    logger.info(f"Created task {task.id} on the general agent")
    
    # Send a message that will route to the calculator agent
    calc_message = Message(
        role="user",
        parts=[MessagePart(type="text", content="Can you calculate 123 * 456?")]
    )
    response = await orchestrator.send_message(task.id, calc_message)
    logger.info(f"Response from calculation route: {response.messages[-1].parts[0].content}")
    
    # Send another message that will route to the research agent
    research_message = Message(
        role="user",
        parts=[MessagePart(type="text", content="Can you research quantum computing?")]
    )
    response = await orchestrator.send_message(task.id, research_message)
    logger.info(f"Response from research route: {response.messages[-1].parts[0].content}")
    
    return task

async def demonstrate_sequential_chain():
    """Demonstrate a sequential chain of agents processing a task."""
    logger.info("Starting sequential chain example...")
    
    # Set up registry manager with agent URLs
    registry = A2ARegistryManager()
    agent_urls = {
        "research-agent": RESEARCH_AGENT_URL,
        "summarization-agent": SUMMARIZATION_AGENT_URL,
    }
    
    # Define the sequence of agents
    agent_sequence = ["research-agent", "summarization-agent"]
    
    # Create an orchestrator for the sequential chain
    orchestrator = A2AOrchestrator(
        config=OrchestrationConfig(entry_points=["research-agent"]),
        registry_manager=registry,
        agent_url_map=agent_urls
    )
    
    # Create a sequential chain
    chain = SequentialTaskChain(orchestrator, agent_sequence)
    
    # Start the chain
    task = await chain.start_chain()
    logger.info(f"Created sequential chain with task ID {task.id}")
    
    # Send a message that will flow through the chain
    message = Message(
        role="user",
        parts=[MessagePart(
            type="text", 
            content="Research the latest advancements in renewable energy"
        )]
    )
    
    # Process through the chain
    response = await chain.send_message(message)
    logger.info(f"Final response from chain: {response.messages[-1].parts[0].content}")
    
    # Get conversation history across all agents
    history = chain.get_conversation_history()
    logger.info(f"Chain processed through {len(history)} agents")
    
    return response

async def demonstrate_parallel_processing():
    """Demonstrate parallel processing across multiple agents."""
    logger.info("Starting parallel processing example...")
    
    # Set up registry manager with agent URLs
    registry = A2ARegistryManager()
    agent_urls = {
        "research-agent": RESEARCH_AGENT_URL,
        "calculator-agent": CALCULATOR_AGENT_URL,
        "summarization-agent": SUMMARIZATION_AGENT_URL,
    }
    
    # Create an orchestrator
    orchestrator = A2AOrchestrator(
        config=OrchestrationConfig(
            entry_points=["research-agent", "calculator-agent", "summarization-agent"]
        ),
        registry_manager=registry,
        agent_url_map=agent_urls
    )
    
    # Create a parallel task group
    group = ParallelTaskGroup(orchestrator)
    
    # Create tasks on multiple specialized agents
    agents = ["research-agent", "calculator-agent", "summarization-agent"]
    tasks = await group.create_tasks(agents)
    logger.info(f"Created {len(tasks)} parallel tasks across different agents")
    
    # Send the same message to all agents
    message = Message(
        role="user",
        parts=[MessagePart(type="text", content="Analyze the impact of AI on society")]
    )
    
    # Send message to all agents in parallel
    results = await group.send_message_to_all(message)
    logger.info(f"Received {len(results)} parallel responses")
    
    # Collect all results
    all_results = await group.collect_results()
    for agent_id, agent_results in all_results.items():
        if agent_results and agent_results[-1].messages:
            logger.info(f"Results from {agent_id}: {agent_results[-1].messages[-1].parts[0].content[:50]}...")
    
    return all_results

async def main():
    """Run the orchestration examples."""
    # Note: In a real scenario, you would have actual A2A servers running at the URLs.
    # Since we don't have them in this example, we'll just show the orchestration patterns.
    
    try:
        # These would work if you had actual A2A servers running
        # await demonstrate_conditional_routing()
        # await demonstrate_sequential_chain()
        # await demonstrate_parallel_processing()
        
        # For this example, we'll just log the steps to show the patterns
        logger.info("This example demonstrates A2A orchestration patterns.")
        logger.info("To run it with real agents, start A2A servers at the configured URLs.")
        logger.info("See the code for implementation details of:")
        logger.info("1. Conditional routing based on message content")
        logger.info("2. Sequential processing through a chain of agents")
        logger.info("3. Parallel processing across multiple agents")
        
    except Exception as e:
        logger.error(f"Error in orchestration example: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
