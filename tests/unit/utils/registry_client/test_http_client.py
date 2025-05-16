"""Tests for the ailf.registry_client module."""

import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from ailf.registry_client.http_client import HTTPRegistryClient
from ailf.registry_client.base import RegistryError
from ailf.schemas.tooling import ToolDescription
from ailf.schemas.agent import AgentDescription

@pytest.fixture
def sample_tool_descriptions():
    """Create sample tool descriptions for testing."""
    return [
        ToolDescription(
            name="calculator",
            description="Performs mathematical calculations",
            categories=["math", "utility"],
            keywords=["calculate", "math", "compute", "arithmetic"]
        ),
        ToolDescription(
            name="weather_lookup",
            description="Gets current weather information for a location",
            categories=["information", "weather"],
            keywords=["weather", "forecast", "temperature"]
        )
    ]

@pytest.fixture
def sample_agent_descriptions():
    """Create sample agent descriptions for testing."""
    return [
        AgentDescription(
            agent_id="math-agent",
            name="Math Assistant",
            description="An agent that helps with mathematical calculations",
            categories=["math", "education"],
            capabilities=["basic_math", "algebra", "statistics"],
            api_endpoint="http://math-agent.example.com/api"
        ),
        AgentDescription(
            agent_id="weather-agent",
            name="Weather Agent",
            description="An agent that provides weather information",
            categories=["weather", "information"],
            capabilities=["current_weather", "forecast"],
            api_endpoint="http://weather-agent.example.com/api"
        )
    ]

class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, status_code, json_data):
        """Initialize the mock response."""
        self.status_code = status_code
        self._json_data = json_data

    async def json(self):
        """Return the JSON data."""
        return self._json_data
    
    async def __aenter__(self):
        """Context manager enter."""
        return self
    
    async def __aexit__(self, *args):
        """Context manager exit."""
        pass

@pytest.mark.asyncio
async def test_discover_tools_success(sample_tool_descriptions):
    """Test successful tool discovery."""
    # Mock the httpx client response
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MockResponse(
            200, 
            {"tools": [desc.dict() for desc in sample_tool_descriptions]}
        )
        mock_get.return_value = mock_response
        
        # Create the client and call discover_tools
        client = HTTPRegistryClient("http://localhost:8000")
        tools = await client.discover_tools(query="math")
        
        # Verify the request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["url"] == "http://localhost:8000/tools"
        assert "params" in kwargs
        assert kwargs["params"]["query"] == "math"
        
        # Check the results
        assert len(tools) == 2
        assert tools[0].name == "calculator"
        assert tools[1].name == "weather_lookup"

@pytest.mark.asyncio
async def test_discover_tools_with_filters(sample_tool_descriptions):
    """Test tool discovery with category and name filters."""
    # Mock the httpx client response
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MockResponse(
            200, 
            {"tools": [desc.dict() for desc in sample_tool_descriptions]}
        )
        mock_get.return_value = mock_response
        
        # Create the client and call discover_tools with filters
        client = HTTPRegistryClient("http://localhost:8000")
        tools = await client.discover_tools(
            categories=["math"],
            tool_names=["calculator"]
        )
        
        # Verify the request was made with correct parameters
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "params" in kwargs
        assert kwargs["params"]["categories"] == ["math"]
        assert kwargs["params"]["tool_names"] == ["calculator"]

@pytest.mark.asyncio
async def test_discover_tools_error():
    """Test error handling in tool discovery."""
    # Mock the httpx client to raise an exception
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.HTTPError("Connection error")
        
        # Create the client and attempt to call discover_tools
        client = HTTPRegistryClient("http://localhost:8000")
        with pytest.raises(RegistryError) as exc_info:
            await client.discover_tools()
        
        # Check the error message
        assert "Connection error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_discover_agents_success(sample_agent_descriptions):
    """Test successful agent discovery."""
    # Mock the httpx client response
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MockResponse(
            200, 
            {"agents": [desc.dict() for desc in sample_agent_descriptions]}
        )
        mock_get.return_value = mock_response
        
        # Create the client and call discover_agents
        client = HTTPRegistryClient("http://localhost:8000")
        agents = await client.discover_agents(query="weather")
        
        # Verify the request was made correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["url"] == "http://localhost:8000/agents"
        assert "params" in kwargs
        assert kwargs["params"]["query"] == "weather"
        
        # Check the results
        assert len(agents) == 2
        assert agents[0].name == "Math Assistant"
        assert agents[1].name == "Weather Agent"

@pytest.mark.asyncio
async def test_register_tool_success():
    """Test successful tool registration."""
    # Create a tool description
    tool = ToolDescription(
        name="calculator",
        description="Performs mathematical calculations",
        categories=["math", "utility"],
        keywords=["calculate", "math"]
    )
    
    # Mock the httpx client response
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = MockResponse(
            201, 
            {"status": "success", "message": "Tool registered successfully"}
        )
        mock_post.return_value = mock_response
        
        # Create the client and call register_tool
        client = HTTPRegistryClient("http://localhost:8000")
        result = await client.register_tool(tool)
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["url"] == "http://localhost:8000/tools"
        assert "json" in kwargs
        assert kwargs["json"]["name"] == "calculator"
        
        # Check the result
        assert result["status"] == "success"

@pytest.mark.asyncio
async def test_register_agent_success():
    """Test successful agent registration."""
    # Create an agent description
    agent = AgentDescription(
        agent_id="math-agent",
        name="Math Assistant",
        description="An agent that helps with mathematical calculations",
        categories=["math", "education"],
        capabilities=["basic_math", "algebra", "statistics"],
        api_endpoint="http://math-agent.example.com/api"
    )
    
    # Mock the httpx client response
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = MockResponse(
            201, 
            {"status": "success", "message": "Agent registered successfully"}
        )
        mock_post.return_value = mock_response
        
        # Create the client and call register_agent
        client = HTTPRegistryClient("http://localhost:8000")
        result = await client.register_agent(agent)
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["url"] == "http://localhost:8000/agents"
        assert "json" in kwargs
        assert kwargs["json"]["agent_id"] == "math-agent"
        
        # Check the result
        assert result["status"] == "success"

@pytest.mark.asyncio
async def test_authentication():
    """Test that API key is properly included in requests."""
    # Mock the httpx client response
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = MockResponse(
            200, 
            {"tools": []}
        )
        mock_get.return_value = mock_response
        
        # Create the client with API key and make a request
        api_key = "test-api-key-12345"
        client = HTTPRegistryClient("http://localhost:8000", api_key=api_key)
        await client.discover_tools()
        
        # Verify the API key was included in headers
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "headers" in kwargs
        assert "Authorization" in kwargs["headers"]
        assert kwargs["headers"]["Authorization"] == f"Bearer {api_key}"
