#!/usr/bin/env python3
"""
Comprehensive Agent Framework Example.

This example demonstrates the complete capabilities of the AILF Agent Framework,
including different planning strategies, tool usage, memory, and structured output.
"""

import asyncio
import logging
import os
import json
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field

from ailf.agent import Agent, ReactivePlan, DeliberativePlan, TreeOfThoughtsPlan
from ailf.agent.tools import tool, ToolRegistry, execute_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Define output schemas for structured agent responses
class WeatherInfo(BaseModel):
    """Weather information for a location."""
    location: str = Field(description="Location for the weather report")
    temperature: float = Field(description="Current temperature in Celsius")
    conditions: str = Field(description="Current weather conditions")
    forecast: List[str] = Field(description="Weather forecast for next few days")


class ResearchSummary(BaseModel):
    """Summary of research on a topic."""
    topic: str = Field(description="Topic of research")
    summary: str = Field(description="Brief summary of findings")
    key_points: List[str] = Field(description="Key points from the research")
    sources: List[Dict[str, str]] = Field(
        description="Sources consulted",
        default_factory=list
    )


class TravelPlan(BaseModel):
    """Travel plan for a destination."""
    destination: str = Field(description="Travel destination")
    best_time_to_visit: str = Field(description="Recommended time to visit")
    attractions: List[str] = Field(description="Must-see attractions")
    transportation: Dict[str, str] = Field(description="Transportation options")
    estimated_budget: str = Field(description="Estimated budget range")


# Define example tools
@tool(category="weather")
async def get_weather(location: str) -> Dict[str, Any]:
    """Get current weather information for a location.
    
    :param location: City or region name
    :return: Weather data including temperature and conditions
    """
    # Simulate API call
    logger.info(f"Fetching weather for: {location}")
    await asyncio.sleep(1)
    
    # Mock weather data
    weather_data = {
        "location": location,
        "temperature": 22.5,
        "conditions": "Partly cloudy",
        "forecast": [
            "Tomorrow: Sunny, 24°C",
            "Day after: Light rain, 20°C",
            "Day 3: Cloudy, 22°C"
        ]
    }
    
    return weather_data


@tool(category="search")
async def web_search(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    """Search the web for information.
    
    :param query: Search query
    :param num_results: Number of results to return
    :return: List of search results with titles and snippets
    """
    # Simulate search API call
    logger.info(f"Searching for: {query}")
    await asyncio.sleep(1.5)
    
    # Mock search results
    results = []
    for i in range(1, num_results + 1):
        results.append({
            "title": f"Result {i} for {query}",
            "url": f"https://example.com/result{i}",
            "snippet": f"This is a snippet from result {i} about {query}..."
        })
    
    return results


@tool(category="travel")
def get_destination_info(destination: str) -> Dict[str, Any]:
    """Get travel information about a destination.
    
    :param destination: Name of city or country
    :return: Travel information about the destination
    """
    # Simulate database lookup
    logger.info(f"Getting travel info for: {destination}")
    
    # Mock destination data
    destinations = {
        "paris": {
            "best_time_to_visit": "April to June or September to October",
            "attractions": [
                "Eiffel Tower",
                "Louvre Museum",
                "Notre-Dame Cathedral",
                "Arc de Triomphe"
            ],
            "transportation": {
                "local": "Metro, bus, or bicycle rental",
                "arriving": "Charles de Gaulle Airport or Gare du Nord (Eurostar)"
            },
            "estimated_budget": "€150-300 per day"
        },
        "tokyo": {
            "best_time_to_visit": "March to May or September to November",
            "attractions": [
                "Tokyo Tower",
                "Senso-ji Temple",
                "Meiji Shrine",
                "Shibuya Crossing"
            ],
            "transportation": {
                "local": "JR trains, subway, or taxis",
                "arriving": "Narita or Haneda Airports"
            },
            "estimated_budget": "¥15,000-25,000 per day"
        },
        "new york": {
            "best_time_to_visit": "April to June or September to November",
            "attractions": [
                "Empire State Building",
                "Central Park",
                "Statue of Liberty",
                "Times Square"
            ],
            "transportation": {
                "local": "Subway, bus, or taxi",
                "arriving": "JFK, LaGuardia, or Newark Airports"
            },
            "estimated_budget": "$150-300 per day"
        }
    }
    
    dest_lower = destination.lower()
    if dest_lower in destinations:
        result = destinations[dest_lower].copy()
        result["destination"] = destination
        return result
    else:
        return {
            "destination": destination,
            "best_time_to_visit": "Information not available",
            "attractions": ["Research needed"],
            "transportation": {"local": "Unknown", "arriving": "Unknown"},
            "estimated_budget": "Unknown"
        }


@tool(category="utilities")
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


async def demo_reactive_agent():
    """Demonstrate a reactive agent for simple Q&A."""
    logger.info("\n\n=== REACTIVE AGENT DEMO ===\n")
    
    # Create a simple reactive agent
    agent = Agent(
        name="WeatherBot",
        model_name="openai:gpt-3.5-turbo",  # Use a simpler model for reactive tasks
        description="A bot that provides weather information",
        planning_strategy=ReactivePlan()
    )
    
    # Add weather tool
    agent.add_tool(get_weather)
    
    # Run the agent with a simple query
    query = "What's the weather like in Paris today?"
    logger.info(f"Query: {query}")
    
    result = await agent.run(
        query,
        output_schema=WeatherInfo
    )
    
    # Display the structured result
    logger.info(f"Weather for: {result.location}")
    logger.info(f"Temperature: {result.temperature}°C")
    logger.info(f"Conditions: {result.conditions}")
    logger.info("Forecast:")
    for day in result.forecast:
        logger.info(f"  - {day}")
    
    return result


async def demo_deliberative_agent():
    """Demonstrate a deliberative agent for research tasks."""
    logger.info("\n\n=== DELIBERATIVE AGENT DEMO ===\n")
    
    # Create a deliberative agent for research tasks
    agent = Agent(
        name="ResearchAssistant",
        model_name="openai:gpt-4-turbo",
        description="An assistant that performs careful research",
        planning_strategy=DeliberativePlan()
    )
    
    # Add search and calculate tools
    agent.add_tool(web_search)
    agent.add_tool(calculate)
    
    # Add some facts to the agent's memory
    agent.memory.add_fact("Quantum computing uses qubits instead of classical bits")
    agent.memory.add_fact("Quantum entanglement is a key property in quantum computing")
    
    # Run the agent with a research query
    query = "Research the impact of quantum computing on modern cryptography"
    logger.info(f"Query: {query}")
    
    result = await agent.run(
        query,
        output_schema=ResearchSummary
    )
    
    # Display the research results
    logger.info(f"Research Topic: {result.topic}")
    logger.info(f"Summary: {result.summary}")
    logger.info("Key Points:")
    for point in result.key_points:
        logger.info(f"  - {point}")
    
    if result.sources:
        logger.info("Sources:")
        for source in result.sources:
            logger.info(f"  - {source.get('title', 'Unnamed Source')}")
    
    return result


async def demo_tot_agent():
    """Demonstrate a Tree of Thoughts agent for travel planning."""
    logger.info("\n\n=== TREE OF THOUGHTS AGENT DEMO ===\n")
    
    # Create a Tree of Thoughts agent for complex planning
    agent = Agent(
        name="TravelPlanner",
        model_name="openai:gpt-4-turbo",
        description="An assistant that helps plan travel itineraries",
        planning_strategy=TreeOfThoughtsPlan(num_thoughts=3, max_depth=2)
    )
    
    # Add travel and search tools
    agent.add_tool(get_destination_info)
    agent.add_tool(web_search)
    agent.add_tool(get_weather)
    
    # Run the agent with a travel planning query
    destination = "Tokyo"
    query = f"Plan a 5-day trip to {destination}, including major attractions, " \
            f"transportation options, and budget considerations."
    logger.info(f"Query: {query}")
    
    result = await agent.run(
        query,
        output_schema=TravelPlan
    )
    
    # Display the travel plan
    logger.info(f"Travel Plan for: {result.destination}")
    logger.info(f"Best time to visit: {result.best_time_to_visit}")
    logger.info("Attractions:")
    for attraction in result.attractions:
        logger.info(f"  - {attraction}")
    
    logger.info("Transportation:")
    for key, value in result.transportation.items():
        logger.info(f"  - {key}: {value}")
    
    logger.info(f"Estimated Budget: {result.estimated_budget}")
    
    return result


async def run_demos():
    """Run all agent demos."""
    # Check if API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("This example requires an OpenAI API key.")
        logger.error("Please set the OPENAI_API_KEY environment variable and run again.")
        return
    
    try:
        # Run each demo in sequence
        weather_info = await demo_reactive_agent()
        research_summary = await demo_deliberative_agent()
        travel_plan = await demo_tot_agent()
        
        # Save results to file for reference
        results = {
            "reactive_agent_result": weather_info.dict(),
            "deliberative_agent_result": research_summary.dict(),
            "tree_of_thoughts_agent_result": travel_plan.dict()
        }
        
        with open("agent_demo_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("\n\nAll demos completed successfully!")
        logger.info("Results saved to agent_demo_results.json")
    
    except Exception as e:
        logger.exception(f"Error running demos: {str(e)}")


if __name__ == "__main__":
    asyncio.run(run_demos())
