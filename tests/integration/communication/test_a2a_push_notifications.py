"""Integration tests for A2A push notifications.

This module contains integration tests for A2A push notification functionality.
"""
import asyncio
import json
import os
import signal
import subprocess
import time
import unittest
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Any, Dict, List, Optional, Union

import pytest
import requests

from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_push import (
    PushNotificationClient,
    PushNotificationConfig,
    PushNotificationEvent,
    PushNotificationManager,
)
from ailf.communication.a2a_server import AILFASA2AServer, A2AAgentExecutor, A2ARequestContext
from ailf.schemas.a2a import (
    Message,
    MessagePart,
    Task,
    TaskDelta,
    TaskState,
)


class NotificationHandler(BaseHTTPRequestHandler):
    """HTTP handler for receiving push notifications."""
    
    notifications = []
    
    def do_POST(self):
        """Handle POST requests with notifications."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        notification = json.loads(post_data.decode('utf-8'))
        
        # Store the notification for inspection
        NotificationHandler.notifications.append(notification)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
    
    @classmethod
    def reset(cls):
        """Reset notifications list."""
        cls.notifications = []


class PushNotificationAgentExecutor(A2AAgentExecutor):
    """Agent executor that uses push notifications."""
    
    def __init__(self, push_manager: PushNotificationManager):
        """Initialize with a push notification manager."""
        super().__init__()
        self.push_manager = push_manager
    
    async def execute(self, context: A2ARequestContext) -> Union[Task, asyncio.Future]:
        """Execute agent logic with push notifications."""
        if not context.message:
            return context.task
        
        content = context.message.parts[0].content if context.message.parts else ""
        
        # First update the task state to running and notify
        context.task.state = TaskState.RUNNING
        await self.push_manager.notify_task_state_change(
            context.task.id, 
            TaskState.RUNNING
        )
        
        # Process the message
        await asyncio.sleep(0.2)  # Simulate processing time
        
        # Create response
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=f"Echo: {content}")]
        )
        context.task.messages.append(response)
        context.task.state = TaskState.COMPLETED
        
        # Send notification of the complete task
        await self.push_manager.notify_task_update(context.task)
        
        return context.task


@pytest.mark.asyncio
class TestA2APushNotifications:
    """Test A2A push notification functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_notification_server(self):
        """Set up a notification server."""
        # Reset notifications
        NotificationHandler.reset()
        
        # Create and start server
        server = HTTPServer(('localhost', 8085), NotificationHandler)
        server_thread = Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        yield
        
        # Shutdown server
        server.shutdown()
        server.server_close()
    
    @pytest.fixture
    def a2a_server(self):
        """Set up an A2A server with push notification support."""
        # Create push notification manager
        push_manager = PushNotificationManager()
        
        # Create agent executor with push manager
        executor = PushNotificationAgentExecutor(push_manager)
        
        # Create the agent description
        from ailf.schemas.agent import AgentDescription
        agent_description = AgentDescription(
            agent_name="Push Notification Test Agent",
            agent_type="test_agent",
            description="A test agent that supports push notifications",
            version="1.0.0",
            supports_a2a=True
        )
        
        # Create and prepare server
        server = AILFASA2AServer(
            agent_description=agent_description,
            executor=executor,
            task_store=None  # Use default
        )
        
        # Store push manager in server state
        server.push_manager = push_manager
        
        # Create FastAPI application
        app = server.create_app()
        
        # Start the server using test client instead of actual server
        from fastapi.testclient import TestClient
        test_client = TestClient(app)
        server.test_client = test_client
        
        return server
    
    @pytest.fixture
    def client(self, a2a_server):
        """Create an A2A client.
        
        Since we're not actually starting a server, we'll create a client
        that works with FastAPI TestClient.
        """
        import json
        from datetime import datetime
        
        # Custom JSON encoder that can handle datetime objects
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
        
        class TestA2AClient(A2AClient):
            """A2A client that works with FastAPI TestClient."""
            
            async def _make_request(self, method, path, json_data=None):
                """Override to use TestClient."""
                url = path
                test_client = a2a_server.test_client
                
                # Convert json_data to JSON-serializable data
                if json_data:
                    json_data = json.loads(json.dumps(json_data, cls=DateTimeEncoder))
                
                if method == "GET":
                    response = test_client.get(url, headers=self.headers)
                elif method == "POST":
                    response = test_client.post(url, headers=self.headers, json=json_data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                response.raise_for_status()
                return response.json()
            
            # Override methods that use deprecated Pydantic methods
            async def create_task(self):
                """Create a new task."""
                response = await self._make_request("POST", "/tasks")
                from ailf.schemas.a2a import Task
                return Task.model_validate(response.get("task"))
                
            async def send_message(self, task_id: str, message):
                """Send a message to a task."""
                from ailf.communication.a2a_client import SendMessageRequest
                request = SendMessageRequest(message=message)
                # Use model_dump instead of dict
                json_data = {"message": message.model_dump(exclude_none=True)}
                response = await self._make_request(
                    "POST", f"/tasks/{task_id}/messages", json_data
                )
                from ailf.schemas.a2a import Task
                return Task.model_validate(response.get("task"))
        
        return TestA2AClient(base_url="http://testserver")
    
    async def test_push_notifications_for_task_updates(self, a2a_server, client):
        """Test receiving push notifications for task updates."""
        # Create notification configuration
        config = PushNotificationConfig(
            url="http://localhost:8085",
            token="test-token",
            headers={"X-Test": "true"}
        )
        
        # Create a task
        task = await client.create_task()
        
        # Register the task for notifications
        a2a_server.push_manager.register_task(task.id, config)
        
        # Send a message to trigger the agent
        message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Hello, agent!")]
        )
        response_task = await client.send_message(task.id, message)
        
        # Give time for notifications to be processed
        await asyncio.sleep(0.5)
        
        # Check notifications
        assert len(NotificationHandler.notifications) >= 2
        
        # First notification should be about state change
        first_notification = NotificationHandler.notifications[0]
        assert first_notification["event_type"] == "task_state_change"
        assert first_notification["task_id"] == task.id
        assert first_notification["data"]["state"] == "running"
        
        # Last notification should be the full task update
        last_notification = NotificationHandler.notifications[-1]
        assert last_notification["event_type"] == "task_update"
        assert last_notification["task_id"] == task.id
        assert "task" in last_notification["data"]
        assert last_notification["data"]["task"]["state"] == "completed"
        
        # The notification should contain the task messages
        assert len(last_notification["data"]["task"]["messages"]) == 2
        assert last_notification["data"]["task"]["messages"][1]["parts"][0]["content"] == "Echo: Hello, agent!"
    
    async def test_push_notification_client(self, a2a_server, client):
        """Test the push notification client for receiving notifications."""
        # Create a push notification client
        push_client = PushNotificationClient(
            callback_url="http://localhost:8085",
            token="test-token"
        )
        
        # Set up a handler to track notifications
        received_notifications = []
        
        async def notification_handler(task_id, data):
            received_notifications.append((task_id, data))
        
        # Register handlers for events
        push_client.register_handler("task_update", notification_handler)
        push_client.register_handler("task_state_change", notification_handler)
        
        # Create a notification processor that will use our handler
        async def process_notification_wrapper(notification):
            await push_client.process_notification(notification)
        
        # Simulate receiving notifications directly to the client
        # Create a task
        task = await client.create_task()
        
        # Register the task for notifications on the server
        a2a_server.push_manager.register_task(
            task.id, 
            push_client.get_notification_config()
        )
        
        # Send a message to trigger the agent
        message = Message(
            role="user",
            parts=[MessagePart(type="text", content="Test notification client")]
        )
        response_task = await client.send_message(task.id, message)
        
        # Give time for notifications to be sent
        await asyncio.sleep(0.5)
        
        # Process the notifications using our client
        for notification in NotificationHandler.notifications:
            await process_notification_wrapper(notification)
        
        # Check that our handler was called
        assert len(received_notifications) >= 2
        
        # Check the task state change notification
        task_id, data = received_notifications[0]
        assert task_id == task.id
        assert data["state"] == "running"
        
        # Check the task update notification
        task_id, data = received_notifications[-1]
        assert task_id == task.id
        assert "task" in data
        assert data["task"]["state"] == "completed"


if __name__ == "__main__":
    unittest.main()
