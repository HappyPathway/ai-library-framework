"""End-to-end tests for A2A protocol in real-world scenarios.

This module tests complete A2A workflows that simulate real-world applications,
including multi-agent orchestration, push notifications, and error handling.
"""
import asyncio
import json
import os
import signal
import subprocess
import time
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional, Union, AsyncIterator
from uuid import uuid4

import pytest
import httpx
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager

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
from ailf.communication.a2a_push import (
    PushNotificationClient,
    PushNotificationConfig,
    PushNotificationEvent,
    PushNotificationManager,
)
from ailf.communication.a2a_registry import A2ARegistryManager
from ailf.communication.a2a_server import AILFASA2AServer, A2AAgentExecutor, A2ARequestContext
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


# Test setup helpers
def start_test_server(port: int, agent_name: str, executor_class):
    """Start a test A2A server in a subprocess."""
    # This creates a server that runs in a separate process
    server_script = f"""
import asyncio
import sys
import uvicorn
from fastapi import FastAPI
from ailf.communication.a2a_server import AILFASA2AServer
from ailf.schemas.agent import AgentDescription, CommunicationEndpoint
from ailf.schemas.a2a import AgentType

# Import the executor class
sys.path.append("/workspaces/template-python-dev/tests/e2e")
from test_a2a_e2e import {executor_class.__name__}

# Create FastAPI app
app = FastAPI()

# Create agent description
agent_description = AgentDescription(
    name="{agent_name}",
    description="Test agent for E2E tests",
    agent_type=AgentType.ASSISTANT,
    capabilities={{
        "streaming": False,
        "file_upload": False,
        "file_download": False,
    }},
    communication_endpoints=[
        CommunicationEndpoint(
            protocol="a2a",
            url="http://localhost:{port}",
        )
    ],
)

# Create A2A server
server = AILFASA2AServer(
    agent_description=agent_description,
    agent_executor={executor_class.__name__}(),
)

# Add routes to app
app.include_router(server.router)

# Run the server
uvicorn.run(app, host="0.0.0.0", port={port})
"""
    
    # Write server script to a temporary file
    script_path = f"/tmp/test_server_{port}.py"
    with open(script_path, "w") as f:
        f.write(server_script)
    
    # Start the server in a subprocess
    process = subprocess.Popen(
        ["python", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for the server to start
    time.sleep(3)
    
    # Check if the server is running
    try:
        response = requests.get(f"http://localhost:{port}/")
        if response.status_code != 404:  # FastAPI returns 404 for root path
            raise RuntimeError(f"Server on port {port} is not running properly")
    except Exception as e:
        # Kill the process if the server didn't start
        process.terminate()
        raise RuntimeError(f"Failed to start server on port {port}: {str(e)}")
    
    return process


def stop_test_server(process):
    """Stop a test A2A server subprocess."""
    # Send SIGTERM to gracefully stop the process
    process.terminate()
    try:
        # Wait for process to terminate with timeout
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        # If process doesn't terminate in time, force kill
        process.kill()


# Test agent executors for E2E testing
class SearchAgentExecutor(A2AAgentExecutor):
    """Agent executor that simulates a search service."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute search queries."""
        # Get the latest message
        message = context.messages[-1]
        if message.role != "user":
            # Only process user messages
            return context.task
            
        # Process the message
        content = message.parts[0].content.lower() if message.parts else ""
        
        # Simulate search latency
        await asyncio.sleep(0.5)
        
        # Create a response based on the query
        search_results = []
        if "weather" in content:
            search_results = [
                {"title": "Today's Weather Forecast", "url": "https://example.com/weather"},
                {"title": "5-Day Weather Outlook", "url": "https://example.com/weather/forecast"},
            ]
        elif "news" in content:
            search_results = [
                {"title": "Latest Headlines", "url": "https://example.com/news"},
                {"title": "Breaking News", "url": "https://example.com/news/breaking"},
            ]
        else:
            # Generic search results
            query_terms = content.replace("search", "").strip()
            search_results = [
                {"title": f"Result 1 for {query_terms}", "url": f"https://example.com/search?q={query_terms}"},
                {"title": f"Result 2 for {query_terms}", "url": f"https://example.com/search?q={query_terms}&page=2"},
            ]
            
        # Format the results
        results_text = "\n".join([f"- {item['title']}: {item['url']}" for item in search_results])
        response_content = f"Here are the search results:\n\n{results_text}"
        
        # Create response message
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=response_content)]
        )
        
        # Update task
        context.task.messages.append(response)
        return context.task


class DataAnalysisAgentExecutor(A2AAgentExecutor):
    """Agent executor that simulates data analysis capabilities."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute data analysis requests."""
        # Get the latest message
        message = context.messages[-1]
        if message.role != "user":
            # Only process user messages
            return context.task
            
        # Process the message
        content = message.parts[0].content.lower() if message.parts else ""
        
        # Simulate analysis latency
        await asyncio.sleep(1.0)
        
        # Create a response based on the analysis request
        analysis_result = "No analysis was performed."
        
        if "analyze" in content and "data" in content:
            # Generate fake analysis results
            if "sales" in content:
                analysis_result = """
## Sales Data Analysis

- Total Sales: $1,245,678
- YoY Growth: +12.3%
- Top Product: Widget X
- Weakest Region: Northwest

### Recommendations
1. Increase marketing in Northwest region
2. Focus on Widget X accessories
3. Review pricing strategy for Widget Y
"""
            elif "user" in content or "customer" in content:
                analysis_result = """
## Customer Data Analysis

- Active Users: 45,678
- Average Session: 8.5 minutes
- Conversion Rate: 3.2%
- Churn Rate: 5.1%

### Recommendations
1. Improve onboarding flow
2. Add more engagement features
3. Create loyalty program
"""
            else:
                analysis_result = """
## Generic Data Analysis

- Sample Size: 10,000
- Mean: 45.7
- Median: 42.0
- Standard Deviation: 12.3

### Insights
1. Data shows normal distribution
2. Outliers detected in upper quartile
3. Correlation with time-based factors
"""
                
        # Create response message
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=analysis_result)]
        )
        
        # Update task
        context.task.messages.append(response)
        return context.task


class SummarizerAgentExecutor(A2AAgentExecutor):
    """Agent executor that summarizes content."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute summarization requests."""
        # Get the latest message
        message = context.messages[-1]
        if message.role != "user":
            # Only process user messages
            return context.task
            
        # Process the message
        content = message.parts[0].content if message.parts else ""
        
        # Simulate summarization latency
        await asyncio.sleep(0.7)
        
        # Create a summary (very simplified)
        if len(content) < 100:
            summary = f"Original text: {content}"
        else:
            # Take first and last sentence, add length info
            sentences = content.split(". ")
            if len(sentences) >= 2:
                summary = f"{sentences[0]}... {sentences[-1]}.\n\nSummary of {len(sentences)} sentences and {len(content)} characters."
            else:
                summary = f"Summary: {content[:100]}..."
                
        # Create response message
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=summary)]
        )
        
        # Update task
        context.task.messages.append(response)
        return context.task


class AssistantAgentExecutor(A2AAgentExecutor):
    """Main assistant agent that orchestrates tasks to specialized agents."""
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, AsyncIterator[TaskDelta]]:
        """Execute the main assistant logic."""
        # Get the latest message
        message = context.messages[-1]
        if message.role != "user":
            # Only process user messages
            return context.task
            
        # Process the message
        content = message.parts[0].content.lower() if message.parts else ""
        
        # Determine the appropriate response based on the message
        response_content = "I'm an AI assistant. How can I help you?"
        
        if "search" in content:
            response_content = "I'll help you search for that information."
        elif "analyze" in content and "data" in content:
            response_content = "I'll analyze that data for you."
        elif "summarize" in content:
            response_content = "I'll create a summary of that content for you."
        else:
            # General response with capabilities
            response_content = """
I'm an AI assistant with multiple capabilities. I can help you with:
- Searching for information
- Analyzing data
- Summarizing content

Let me know what you'd like assistance with.
"""
                
        # Create response message
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=response_content)]
        )
        
        # Update task
        context.task.messages.append(response)
        return context.task


# Test webhook server for push notifications
class TestWebhook:
    """Simple webhook server for testing push notifications."""
    
    def __init__(self):
        """Initialize the webhook server."""
        self.app = FastAPI()
        self.client = TestClient(self.app)
        self.received_events = []
        
        # Add routes
        @self.app.post("/webhook")
        async def receive_webhook(request: Request):
            """Receive webhook events."""
            event_data = await request.json()
            self.received_events.append(event_data)
            return {"status": "success"}
            
    def get_events(self):
        """Get received events."""
        return self.received_events
        
    def clear_events(self):
        """Clear received events."""
        self.received_events = []


@pytest.mark.e2e
class TestA2AE2E:
    """End-to-end tests for A2A protocol in real-world scenarios."""
    
    # Skip flag for slow tests
    slow_tests = pytest.mark.skipif(
        os.environ.get("RUN_SLOW_TESTS", "0") != "1",
        reason="Slow tests are disabled by default. Set RUN_SLOW_TESTS=1 to enable."
    )
    
    @pytest.fixture
    def webhook_server(self):
        """Create a test webhook server."""
        return TestWebhook()
    
    @slow_tests
    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self):
        """Test a complete multi-agent workflow."""
        # Start test servers - this would ideally be in a fixture
        # but we're using a simplified approach for demonstration
        try:
            print("Starting test servers...")
            assistant_process = start_test_server(8000, "Assistant", AssistantAgentExecutor)
            search_process = start_test_server(8001, "Search", SearchAgentExecutor)
            analysis_process = start_test_server(8002, "Analysis", DataAnalysisAgentExecutor)
            summarizer_process = start_test_server(8003, "Summarizer", SummarizerAgentExecutor)
            
            # Allow servers to start
            time.sleep(5)
            
            # Create A2A clients
            assistant_client = A2AClient("http://localhost:8000")
            search_client = A2AClient("http://localhost:8001")
            analysis_client = A2AClient("http://localhost:8002")
            summarizer_client = A2AClient("http://localhost:8003")
            
            # Set up orchestration
            registry = A2ARegistryManager()
            config = OrchestrationConfig(
                routes=[
                    # Route from assistant to specialized agents
                    AgentRoute(
                        source_agent="assistant",
                        type=RouteType.CONDITIONAL,
                        conditions=[
                            RouteCondition(
                                field="messages[-1].parts[0].content",
                                operator="contains",
                                value="search",
                                route_to="search"
                            ),
                            RouteCondition(
                                field="messages[-1].parts[0].content",
                                operator="contains",
                                value="analyze",
                                route_to="analysis"
                            ),
                            RouteCondition(
                                field="messages[-1].parts[0].content",
                                operator="contains",
                                value="summarize",
                                route_to="summarizer"
                            ),
                        ]
                    ),
                    # Return to assistant after specialized processing
                    AgentRoute(
                        source_agent="search",
                        type=RouteType.SEQUENTIAL,
                        destination_agents=["assistant"]
                    ),
                    AgentRoute(
                        source_agent="analysis",
                        type=RouteType.SEQUENTIAL,
                        destination_agents=["assistant"]
                    ),
                    AgentRoute(
                        source_agent="summarizer",
                        type=RouteType.SEQUENTIAL,
                        destination_agents=["assistant"]
                    )
                ],
                entry_points=["assistant"]
            )
            
            orchestrator = A2AOrchestrator(
                config=config,
                registry_manager=registry,
                agent_url_map={
                    "assistant": "http://localhost:8000",
                    "search": "http://localhost:8001",
                    "analysis": "http://localhost:8002",
                    "summarizer": "http://localhost:8003"
                }
            )
            
            # Test the workflow
            print("Creating task...")
            task = await orchestrator.create_task("assistant")
            assert task is not None
            assert task.id is not None
            
            # First request - search query
            print("Sending search request...")
            search_message = Message(
                role="user",
                parts=[MessagePart(type="text", content="search for the latest weather forecast")]
            )
            
            search_response = await orchestrator.send_message(task.id, search_message)
            assert "weather" in search_response.messages[-1].parts[0].content.lower()
            
            # Second request - data analysis
            print("Sending analysis request...")
            analysis_message = Message(
                role="user",
                parts=[MessagePart(type="text", content="analyze my sales data please")]
            )
            
            analysis_response = await orchestrator.send_message(task.id, analysis_message)
            assert "sales" in analysis_response.messages[-1].parts[0].content.lower()
            
            # Third request - summarization
            print("Sending summarization request...")
            summarize_message = Message(
                role="user", 
                parts=[MessagePart(
                    type="text",
                    content="summarize this paragraph: The A2A protocol defines standardized communication interfaces between AI agents. It enables seamless collaboration between different types of agents regardless of their implementation details. By using A2A, developers can create interoperable agent ecosystems."
                )]
            )
            
            summarize_response = await orchestrator.send_message(task.id, summarize_message)
            assert "summary" in summarize_response.messages[-1].parts[0].content.lower()
            
            # Check if task history contains all the exchanges
            task_info = await orchestrator.get_task(task.id)
            assert len(task_info.messages) >= 6  # 3 requests + 3 responses
            
        finally:
            # Cleanup: stop all test servers
            print("Stopping test servers...")
            stop_test_server(assistant_process)
            stop_test_server(search_process)
            stop_test_server(analysis_process)
            stop_test_server(summarizer_process)
    
    @pytest.mark.asyncio
    async def test_push_notifications(self, webhook_server):
        """Test push notifications for A2A events."""
        # Create push notification manager
        push_manager = PushNotificationManager()
        
        # Generate a unique task ID
        task_id = f"test-task-{uuid4()}"
        
        # Configure push notifications for the task
        config = PushNotificationConfig(
            url="http://localhost/webhook",  # This will be mocked
            token="test-token"
        )
        push_manager.register_task(task_id, config)
        
        # Create notification event
        event_data = {
            "timestamp": datetime.now(UTC),
            "state": TaskState.COMPLETED,
            "messages_count": 3
        }
        
        # Mock the HTTP client to use the test webhook
        async def mock_send_notification(url, headers, json_data):
            # Use the test client to send the notification
            webhook_server.client.post("/webhook", json=json_data)
            return {"success": True}
            
        # Replace the send method
        original_send = push_manager._send
        push_manager._send = mock_send_notification
        
        try:
            # Send notification
            await push_manager.send_notification(
                task_id,
                "task_state_change",
                event_data
            )
            
            # Check if webhook received the event
            events = webhook_server.get_events()
            assert len(events) == 1
            
            # Verify event data
            event = events[0]
            assert event["event_type"] == "task_state_change"
            assert event["task_id"] == task_id
            assert "data" in event
            assert event["data"]["state"] == TaskState.COMPLETED
            
        finally:
            # Restore original method
            push_manager._send = original_send
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test A2A error handling."""
        # Create a client with an invalid URL
        client = A2AClient("http://non-existent-url")
        
        # Test error handling for various operations
        with pytest.raises(Exception):  # Should raise an exception for connection error
            await client.get_agent_card()
            
        with pytest.raises(Exception):  # Should raise an exception for connection error
            await client.create_task()
            
        # Test with a task ID that doesn't exist
        task_id = "non-existent-task"
        
        with pytest.raises(Exception):  # Should raise an exception
            await client.get_task(task_id)
            
        # Test sending a message to a non-existent task
        message = Message(
            role="user",
            parts=[MessagePart(type="text", content="test")]
        )
        
        with pytest.raises(Exception):  # Should raise an exception
            await client.send_message(task_id, message)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
