#!/usr/bin/env python3
"""
Direct Import Example for the Agent Framework.

This example demonstrates the usage of the agent framework using direct imports
from the source directory rather than relying on the installed package.

This example uses a direct import strategy to ensure it works even if the agent
module hasn't been properly installed yet.
"""

import asyncio
import logging
import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add the src directory to the Python path
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Helper function to check if a module exists and can be imported
def module_exists(module_name):
    """Check if a Python module exists and can be imported.
    
    :param module_name: The name of the module to check
    :type module_name: str
    :return: True if the module can be imported, False otherwise
    :rtype: bool
    """
    return importlib.util.find_spec(module_name) is not None

# Try to import our agent modules directly
try:
    from ailf.agent.base import Agent, AgentConfig, AgentStatus
    from ailf.agent.patterns import ReactivePlan, DeliberativePlan
    from ailf.agent.tools import tool, execute_tool
    print("Successfully imported agent modules directly")
except ImportError as e:
    print(f"Error importing agent modules: {e}")
    print("Using fallback implementation...")
    
    # Define minimal versions of the classes for demonstration
    class AgentStatus:
        """Agent status constants for tracking an agent's operational state.
        
        This class defines the possible states an agent can be in during its lifecycle,
        from idle to completed or failed.
        """
        IDLE = "idle"
        PLANNING = "planning"
        EXECUTING = "executing"
        COMPLETED = "completed"
        FAILED = "failed"
        
    class AgentConfig:
        """Configuration class for Agent initialization.
        
        Holds the core configuration parameters needed to initialize an Agent instance.
        
        :param name: The agent's name identifier
        :type name: str
        :param description: A description of the agent's purpose and capabilities
        :type description: str
        :param model_name: The name of the LLM model to use
        :type model_name: str
        """
        def __init__(self, name, description, model_name):
            """Initialize a new AgentConfig.
            
            :param name: The agent's name identifier
            :type name: str
            :param description: A description of the agent's purpose and capabilities
            :type description: str
            :param model_name: The name of the LLM model to use
            :type model_name: str
            """
            self.name = name
            self.description = description
            self.model_name = model_name
    
    # Basic decorator for tools
    def tool(category=None, name=None, description=None):
        """Decorator to mark a function as an agent tool.
        
        This decorator adds metadata to functions to enable their registration
        and discovery as tools that can be used by an agent.
        
        :param category: The category of the tool (e.g., 'search', 'utilities')
        :type category: str, optional
        :param name: Custom name for the tool, defaults to function name
        :type name: str, optional
        :param description: Custom description, defaults to function docstring
        :type description: str, optional
        :return: The decorated function with tool metadata
        :rtype: callable
        """
        def decorator(func):
            func._tool_category = category
            func._tool_name = name or func.__name__
            func._tool_description = description or func.__doc__
            return func
        return decorator
    
    # Simple agent implementation for demo purposes
    class Agent:
        """Simple agent implementation for demonstration purposes.
        
        This class provides a basic implementation of an agent that can register tools
        and process queries using an AI engine if available.
        
        :param name: The agent's name identifier
        :type name: str
        :param model_name: The name of the LLM model to use
        :type model_name: str
        :param description: A description of the agent's purpose, defaults to "{name} Agent"
        :type description: str, optional
        """
        
        def __init__(self, name, model_name, description=None):
            """Initialize a new Agent instance.
            
            :param name: The agent's name identifier
            :type name: str
            :param model_name: The name of the LLM model to use
            :type model_name: str
            :param description: A description of the agent's purpose, defaults to "{name} Agent"
            :type description: str, optional
            """
            self.name = name
            self.description = description or f"{name} Agent"
            self.model_name = model_name
            self.tools = {}
            self._ai_engine = None
            self.config = AgentConfig(name, self.description, model_name)
            self.status = AgentStatus.IDLE
        
        def add_tool(self, tool_func, name=None):
            """Register a tool function with the agent.
            
            :param tool_func: The function to register as a tool
            :type tool_func: callable
            :param name: Custom name for the tool, defaults to function name
            :type name: str, optional
            """
            tool_name = name or tool_func.__name__
            self.tools[tool_name] = tool_func
        
        async def run(self, query, output_schema=None):
            """Execute a query using the agent.
            
            Processes the query using the AI engine if available, or returns
            a simple response if no AI engine is configured.
            
            :param query: The query to process
            :type query: str
            :param output_schema: Optional schema for structured output
            :type output_schema: Type[BaseModel], optional
            :return: The result of processing the query
            :rtype: Any
            """
            self.status = AgentStatus.EXECUTING
            if self._ai_engine:
                result = await self._ai_engine.analyze(query)
            else:
                result = f"Agent {self.name} processed: {query}"
            self.status = AgentStatus.COMPLETED
            return result
    
    # Placeholder for planning strategies
    class ReactivePlan:
        """Placeholder for reactive planning strategy.
        
        A reactive planning strategy is one where the agent responds directly
        to stimuli without complex deliberation.
        """
        pass
    
    class DeliberativePlan:
        """Placeholder for deliberative planning strategy.
        
        A deliberative planning strategy is one where the agent reasons about
        the best course of action before executing.
        """
        pass
        
    # Placeholder for tool execution
    async def execute_tool(tool_func, **kwargs):
        """Execute a tool function, handling both async and sync functions.
        
        :param tool_func: The tool function to execute
        :type tool_func: callable
        :param kwargs: Keyword arguments to pass to the tool function
        :return: The result of the tool function execution
        :rtype: Any
        """
        return await tool_func(**kwargs) if asyncio.iscoroutinefunction(tool_func) else tool_func(**kwargs)

# Configure logging
# Set up basic configuration for logging with timestamp, logger name, level and message
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Create a logger instance for this module
logger = logging.getLogger(__name__)


# Define a simple output schema
class SearchResult:
    """Simple class to represent search results.
    
    This class encapsulates search results including the query
    and a list of results found.
    
    :param query: The search query
    :type query: str
    :param results: A list of search result items
    :type results: List[Dict[str, str]]
    """
    
    def __init__(self, query: str, results: List[Dict[str, str]]):
        """Initialize a new SearchResult object.
        
        :param query: The search query
        :type query: str
        :param results: A list of search result items
        :type results: List[Dict[str, str]]
        """
        self.query = query
        self.results = results
    
    def __str__(self):
        """Return a string representation of the search results.
        
        :return: A formatted string showing the query and number of results
        :rtype: str
        """
        return f"Search for '{self.query}' found {len(self.results)} results"


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


class MockAIEngine:
    """Mock AI Engine for demonstration purposes.
    
    This implementation simulates different response formats that might be returned
    by various LLM providers to demonstrate the Agent's robust handling capabilities.
    """
    
    async def analyze(self, content, system=None, output_schema=None, temperature=None, **kwargs):
        """Mock analyze method with various return formats.
        
        :param content: The content to analyze
        :type content: str
        :param system: Optional system prompt
        :type system: str, optional
        :param output_schema: Optional Pydantic model for structured output
        :type output_schema: Type[BaseModel], optional
        :param temperature: Optional temperature setting
        :type temperature: float, optional
        :param kwargs: Additional parameters
        :return: Various formats of responses to test agent robustness
        :rtype: Union[str, dict, Any]
        """
        logger.info(f"Mock AI Engine analyzing: {content}")
        logger.info(f"System prompt: {system}")
        logger.info(f"Temperature: {temperature}")
        
        # Simulate different response formats based on content
        if "calculate" in content.lower():
            # Return direct string (like some simple LLM APIs)
            return "The answer is 42"
            
        elif "search" in content.lower():
            # Return dictionary with content field (like Claude/Anthropic format)
            results = await web_search("mock query")
            return {
                "content": f"Found {len(results)} results",
                "model": "mock-model",
                "usage": {"prompt_tokens": 10, "completion_tokens": 15}
            }
            
        elif "pydantic" in content.lower() and output_schema:
            # Return structured output if schema provided (test schema handling)
            logger.info(f"Using output schema: {output_schema.__name__}")
            try:
                # Create a mock instance of the output schema
                if hasattr(output_schema, "model_validate"):
                    # Pydantic V2
                    return output_schema.model_validate({
                        "query": "mock structured query",
                        "results": [{"title": "Structured Result", "snippet": "This is a structured result"}]
                    })
                elif hasattr(output_schema, "parse_obj"):
                    # Pydantic V1
                    return output_schema.parse_obj({
                        "query": "mock structured query",
                        "results": [{"title": "Structured Result", "snippet": "This is a structured result"}]
                    })
                else:
                    # Default fallback
                    return {"error": "Could not create structured output"}
            except Exception as e:
                logger.error(f"Error creating structured output: {str(e)}")
                return {"error": str(e)}
                
        elif "error" in content.lower():
            # Simulate an error case to test error handling
            raise ValueError("Simulated AI engine error for testing")
            
        else:
            # Return a complex nested structure (like OpenAI format)
            return {
                "id": "mock-completion-id",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "I've analyzed your request and here's my response."
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            }


async def run_simple_agent():
    """Run a simple agent example using direct imports.
    
    This function creates an Agent instance, configures it with tools,
    and runs example queries to demonstrate the agent's functionality.
    
    :return: None
    """
    # Create an agent with reactive planning
    agent = Agent(
        name="SimpleAgent",
        model_name="mock-model",
        description="A simple agent for demonstration purposes"
    )
    
    # Override the AI engine with our mock
    agent._ai_engine = MockAIEngine()
    
    # Register tools
    agent.add_tool(web_search)
    agent.add_tool(calculate)
    
    # Run the agent with a query
    logger.info("Running agent with query: 'What is 2 + 2?'")
    result = await agent.run("What is 2 + 2?")
    logger.info(f"Agent result: {result}")
    
    # Run with a different query
    logger.info("Running agent with query: 'Search for information about AI'")
    result = await agent.run("Search for information about AI")
    logger.info(f"Agent result: {result}")
    
    logger.info("Agent demonstration completed successfully!")


if __name__ == "__main__":
    """Main entry point for the direct agent example.
    
    When this script is executed directly (not imported), this block runs the 
    run_simple_agent() function to demonstrate the agent functionality.
    """
    asyncio.run(run_simple_agent())
