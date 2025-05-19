#!/usr/bin/env python3
"""
Agent Framework Example.

This example demonstrates the usage of the unified agent framework,
including different planning strategies and tool integration.
"""

import asyncio
import logging
import os
from typing import List, Optional, Dict, Any

from ailf.agent import Agent, AgentConfig, DeliberativePlan, ReactivePlan, TreeOfThoughtsPlan
from ailf.agent.tools import tool
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Define example tools
@tool(category="search")
async def web_search(query: str) -> List[Dict[str, str]]:
    """Search the web for information.
    
    :param query: The search query
    :return: List of search results
    """
    # Simulate web search
    logger.info(f"Searching web for: {query}")
    await asyncio.sleep(1)  # Simulate API call
    
    # Return mock results
    return [
        {"title": f"Result 1 for {query}", "snippet": "This is the first result"},
        {"title": f"Result 2 for {query}", "snippet": "This is the second result"},
        {"title": f"Result 3 for {query}", "snippet": "This is the third result"}
    ]


@tool(category="knowledge")
def calculate(expression: str) -> float:
    """Calculate the result of a mathematical expression.
    
    :param expression: A mathematical expression to evaluate
    :return: The calculation result
    """
    # Simple and safe evaluation
    logger.info(f"Calculating: {expression}")
    try:
        # Restrict to basic operations for safety
        allowed_chars = set("0123456789.+-*/() ")
        if any(c not in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        
        result = eval(expression, {"__builtins__": {}})
        return float(result)
    except Exception as e:
        logger.error(f"Calculation error: {str(e)}")
        raise ValueError(f"Could not calculate: {str(e)}")


# Define output schema for structured responses
class ResearchResult(BaseModel):
    """Structured research result."""
    topic: str = Field(description="The research topic")
    summary: str = Field(description="Summary of findings")
    key_points: List[str] = Field(description="Key points from the research")
    sources: List[Dict[str, str]] = Field(
        description="Sources used", 
        default_factory=list
    )


async def run_agents_comparison():
    """Run a comparison of different agent types."""
    # Only proceed if we have required API keys
    model_name = os.environ.get("OPENAI_API_KEY") and "openai:gpt-3.5-turbo" or "mock:default"
    
    # 1. Create a reactive agent (simple stimulus-response)
    reactive_agent = Agent(
        name="QuickBot",
        model_name=model_name,
        description="A simple reactive agent",
        planning_strategy=ReactivePlan(),
    )
    
    # 2. Create a deliberative agent (careful planning)
    deliberative_agent = Agent(
        name="Research Assistant",
        model_name=model_name,
        description="An assistant that helps with research tasks",
        planning_strategy=DeliberativePlan()
    )
    
    # Register tools with the deliberative agent
    deliberative_agent.add_tool(web_search)
    deliberative_agent.add_tool(calculate)
    
    # 3. Create a tree-of-thoughts agent (exploratory thinking)
    tot_agent = Agent(
        name="ExplorerBot",
        model_name=model_name,
        description="An agent that explores multiple solution paths",
        planning_strategy=TreeOfThoughtsPlan(num_thoughts=2, max_depth=2),
        config=AgentConfig(
            name="ExplorerBot",
            model_name=model_name,
            temperature=0.7,  # Higher temperature for creative thinking
            verbose=True
        )
    )
    
    # Simple query for reactive agent
    simple_query = "What is the agent framework?"
    logger.info(f"Running reactive agent with query: {simple_query}")
    reactive_result = await reactive_agent.run(simple_query)
    logger.info(f"Reactive agent result: {reactive_result.output}")
    
    # Research query for deliberative agent
    research_query = "Research the impact of quantum computing on cryptography"
    logger.info(f"Running deliberative agent with query: {research_query}")
    deliberative_result = await deliberative_agent.run(
        research_query,
        output_schema=ResearchResult
    )
    
    # Display the structured research result
    logger.info("Research complete")
    if hasattr(deliberative_result, 'topic'):
        # Structured output successfully parsed
        logger.info(f"Topic: {deliberative_result.topic}")
        logger.info(f"Summary: {deliberative_result.summary}")
        logger.info("Key Points:")
        for point in deliberative_result.key_points:
            logger.info(f"- {point}")
        
        if deliberative_result.sources:
            logger.info("Sources:")
            for source in deliberative_result.sources:
                logger.info(f"- {source.get('title', 'Unnamed Source')}")
    else:
        # Fallback for unstructured output
        logger.info(f"Result: {deliberative_result}")
    
    # Creative problem for tree-of-thoughts agent
    creative_query = "Design a solution for reducing energy consumption in data centers"
    logger.info(f"Running tree-of-thoughts agent with query: {creative_query}")
    tot_result = await tot_agent.run(creative_query)
    logger.info(f"Tree of thoughts result: {tot_result.output}")


if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        # Print a message for running the example
        logger.warning("No OpenAI API key detected. Example will run in mock mode.")
        print("\nTo run with a real API key:")
        print("export OPENAI_API_KEY=your_api_key_here")
        print("python examples/agent_example.py")
    
    # Run the agent examples
    asyncio.run(run_agents_comparison())
