"""Integration tests for A2A orchestration.

This module contains integration tests that verify the A2A orchestration components
work together correctly for multi-agent workflows.
"""
import asyncio
import json
import os
import signal
import subprocess
import time
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Union, AsyncIterator

import pytest
import httpx
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.testclient import TestClient
import uvicorn
from threading import Thread
from contextlib import asynccontextmanager

from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_orchestration import (
    A2AOrchestrator,
    AgentRoute,
    OrchestrationConfig,
    OrchestratorError,
    ParallelTaskGroup,
    RouteCondition,
    RouteType,
    SequentialTaskChain,
)
from ailf.communication.a2a_registry import A2ARegistryManager, RegistryEntry
from ailf.communication.a2a_server import AILFASA2AServer, A2AAgentExecutor, A2ARequestContext, A2ATaskManager
from ailf.schemas.a2a import (
    AgentCard,
    AgentCapabilities,
    AgentType,
    Message,
    MessagePart,
    Task,
    TaskDelta,
    TaskState,
)
from ailf.schemas.agent import AgentDescription, CommunicationEndpoint


# Test agent executors for each role in the orchestration
class CalculatorAgentExecutor(A2AAgentExecutor):
    """Calculator agent that can perform basic math operations."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute the agent logic."""
        # Get the latest message
        message = context.messages[-1]
        if message.role != "user":
            # We only process user messages
            return context.task
        
        # Process the message
        content = message.parts[0].content.lower() if message.parts else ""
        
        # Calculate response
        response_content = "I couldn't understand your calculation request."
        if "calculate" in content:
            try:
                # Extract the expression - assuming simple format like "calculate 2 + 3"
                expression = content.replace("calculate", "").strip()
                result = eval(expression)  # Note: eval is used only for testing
                response_content = f"The result of {expression} is {result}"
            except Exception as e:
                response_content = f"Error calculating: {str(e)}"
        
        # Create response message
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=response_content)]
        )
        
        # Update task
        context.task.messages.append(response)
        return context.task


class ResearchAgentExecutor(A2AAgentExecutor):
    """Research agent that can simulate finding information."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute the agent logic."""
        # Get the latest message
        message = context.messages[-1]
        if message.role != "user":
            # We only process user messages
            return context.task
        
        # Process the message
        content = message.parts[0].content.lower() if message.parts else ""
        
        # Simulate research
        response_content = "I couldn't understand your research request."
        if "research" in content:
            # Extract the topic - assuming format like "research quantum computing"
            topic = content.replace("research", "").strip()
            response_content = f"Here's what I found about {topic}: [Simulated research results]"
        
        # Create response message
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=response_content)]
        )
        
        # Update task
        context.task.messages.append(response)
        return context.task


class SummarizationAgentExecutor(A2AAgentExecutor):
    """Summarization agent that summarizes text."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute the agent logic."""
        # Get the latest message
        message = context.messages[-1]
        if message.role != "user":
            # We only process user messages
            return context.task
        
        # Process the message
        content = message.parts[0].content if message.parts else ""
        
        # Summarize
        summary = f"SUMMARY: {content[:50]}..." if len(content) > 50 else content
        
        # Create response message
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=summary)]
        )
        
        # Update task
        context.task.messages.append(response)
        return context.task


class GeneralAgentExecutor(A2AAgentExecutor):
    """General agent that can route requests to specialized agents."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute the agent logic."""
        # Get the latest message
        message = context.messages[-1]
        if message.role != "user":
            # We only process user messages
            return context.task
        
        # Process the message
        content = message.parts[0].content.lower() if message.parts else ""
        
        # Generate response
        if "calculate" in content:
            response_content = "I'll help you calculate that. Let me route this to our calculator agent."
        elif "research" in content:
            response_content = "I'll research that for you. Let me route this to our research agent."
        elif "summarize" in content:
            response_content = "I'll summarize that for you. Let me route this to our summarization agent."
        else:
            response_content = "I'm a general agent. I can help route your request to specialized agents. Try asking me to calculate something, research a topic, or summarize some text."
        
        # Create response message
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=response_content)]
        )
        
        # Update task
        context.task.messages.append(response)
        return context.task


# Test agent server classes
class TestAgentServer:
    """Base class for test agent servers."""
    
    def __init__(self, name: str, description: str, executor_class, port: int):
        """Initialize test agent server."""
        self.name = name
        self.description = description
        self.executor_class = executor_class
        self.port = port
        self.app = FastAPI()
        self.client = TestClient(self.app)
        
        # Create agent description
        self.agent_description = AgentDescription(
            name=name,
            description=description,
            agent_type=AgentType.ASSISTANT,  # Add this required field
            capabilities={
                "streaming": False,
                "file_upload": False,
                "file_download": False,
            },
            communication_endpoints=[
                CommunicationEndpoint(
                    protocol="a2a",
                    url=f"http://localhost:{port}",
                )
            ],
        )
        
        # Create A2A server
        self.server = AILFASA2AServer(
            agent_description=self.agent_description,
            agent_executor=self.executor_class(),
        )
        
        # Add routes to app
        self.app.include_router(self.server.router)


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that can handle datetime objects."""
    
    def default(self, obj):
        """Convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class TestA2AClient(A2AClient):
    """Test A2A client using TestClient instead of real HTTP."""
    
    def __init__(self, test_client: TestClient, base_url: str):
        """Initialize with a test client."""
        super().__init__(base_url=base_url)
        self.test_client = test_client
        
    async def _make_request(self, method, path, json_data=None):
        """Make a request using the test client."""
        url = f"{self.base_url}{path}"
        
        # Convert json_data to JSON-serializable data
        if json_data:
            json_data = json.loads(json.dumps(json_data, cls=DateTimeEncoder))
        
        if method == "GET":
            response = self.test_client.get(url)
        elif method == "POST":
            response = self.test_client.post(url, json=json_data)
        elif method == "PUT":
            response = self.test_client.put(url, json=json_data)
        elif method == "DELETE":
            response = self.test_client.delete(url)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        if response.content:
            return response.json()
        return None


@pytest.fixture
def calculator_server():
    """Create a calculator agent server."""
    server = TestAgentServer(
        name="Calculator Agent",
        description="An agent that can perform basic math calculations",
        executor_class=CalculatorAgentExecutor,
        port=8001,
    )
    return server


@pytest.fixture
def research_server():
    """Create a research agent server."""
    server = TestAgentServer(
        name="Research Agent",
        description="An agent that can find information on topics",
        executor_class=ResearchAgentExecutor,
        port=8002,
    )
    return server


@pytest.fixture
def summarization_server():
    """Create a summarization agent server."""
    server = TestAgentServer(
        name="Summarization Agent",
        description="An agent that can summarize text",
        executor_class=SummarizationAgentExecutor,
        port=8003,
    )
    return server


@pytest.fixture
def general_server():
    """Create a general agent server."""
    server = TestAgentServer(
        name="General Agent",
        description="A general agent that routes requests to specialized agents",
        executor_class=GeneralAgentExecutor,
        port=8000,
    )
    return server


@pytest.fixture
def test_orchestrator(general_server, calculator_server, research_server):
    """Create a test orchestrator with routing configuration."""
    # Set up registry manager
    registry = A2ARegistryManager()
    
    # Define agent URLs
    agent_urls = {
        "general-agent": "http://localhost:8000",
        "calculator-agent": "http://localhost:8001",
        "research-agent": "http://localhost:8002",
    }
    
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
    
    # Initialize clients for test servers
    clients = {
        "general-agent": TestA2AClient(general_server.client, "http://localhost:8000"),
        "calculator-agent": TestA2AClient(calculator_server.client, "http://localhost:8001"),
        "research-agent": TestA2AClient(research_server.client, "http://localhost:8002"),
    }
    
    # Create orchestrator with test clients
    orchestrator = A2AOrchestrator(
        config=config,
        registry_manager=registry,
        agent_url_map=agent_urls,
    )
    
    # Replace orchestrator's client creation with our test clients
    async def get_client_for_agent(agent_id: str) -> A2AClient:
        return clients.get(agent_id)
    
    orchestrator._get_client_for_agent = get_client_for_agent
    
    return orchestrator


@pytest.mark.integration
class TestA2AOrchestrationIntegration:
    """Integration tests for A2A orchestration."""

    @pytest.mark.asyncio
    async def test_conditional_routing_calculator(self, test_orchestrator):
        """Test conditional routing to calculator agent."""
        # Create a task at the entry point
        task = await test_orchestrator.create_task("general-agent")
        assert task is not None
        assert task.id is not None
        
        # Send a message that should route to the calculator agent
        calc_message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Can you calculate 123 * 456?")]
        )
        response = await test_orchestrator.send_message(task.id, calc_message)
        
        # Verify response comes from calculator agent (contains calculation result)
        assert response is not None
        assert response.messages[-1].parts[0].content is not None
        assert "56088" in response.messages[-1].parts[0].content

    @pytest.mark.asyncio
    async def test_conditional_routing_research(self, test_orchestrator):
        """Test conditional routing to research agent."""
        # Create a task at the entry point
        task = await test_orchestrator.create_task("general-agent")
        assert task is not None
        assert task.id is not None
        
        # Send a message that should route to the research agent
        research_message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Can you research quantum computing?")]
        )
        response = await test_orchestrator.send_message(task.id, research_message)
        
        # Verify response comes from research agent
        assert response is not None
        assert response.messages[-1].parts[0].content is not None
        assert "quantum computing" in response.messages[-1].parts[0].content.lower()
        assert "found" in response.messages[-1].parts[0].content.lower()

    @pytest.mark.asyncio
    async def test_sequential_chain(self, test_orchestrator, research_server, summarization_server):
        """Test a sequential chain of agents."""
        # Set up registry manager
        registry = A2ARegistryManager()
        
        # Define agent URLs
        agent_urls = {
            "research-agent": "http://localhost:8002",
            "summarization-agent": "http://localhost:8003",
        }
        
        # Initialize clients for test servers
        clients = {
            "research-agent": TestA2AClient(research_server.client, "http://localhost:8002"),
            "summarization-agent": TestA2AClient(summarization_server.client, "http://localhost:8003"),
        }
        
        # Define the sequence of agents
        agent_sequence = ["research-agent", "summarization-agent"]
        
        # Create an orchestrator for the sequential chain
        orchestrator = A2AOrchestrator(
            config=OrchestrationConfig(entry_points=["research-agent"]),
            registry_manager=registry,
            agent_url_map=agent_urls,
        )
        
        # Replace orchestrator's client creation with our test clients
        async def get_client_for_agent(agent_id: str) -> A2AClient:
            return clients.get(agent_id)
        
        orchestrator._get_client_for_agent = get_client_for_agent
        
        # Create a sequential chain
        chain = SequentialTaskChain(orchestrator, agent_sequence)
        
        # Start the chain
        task = await chain.start_chain()
        assert task is not None
        
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
        
        # Verify the response from summarization agent (contains "SUMMARY")
        assert response is not None
        assert response.messages[-1].parts[0].content is not None
        assert "SUMMARY" in response.messages[-1].parts[0].content
        assert "renewable energy" in response.messages[-1].parts[0].content.lower()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
