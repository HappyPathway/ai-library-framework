"""Tests for A2A push notification functionality.

This module tests the push notification functionality for A2A protocol.
"""
import asyncio
import datetime
import json
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ailf.communication.a2a_push import (
    PushNotificationClient,
    PushNotificationConfig,
    PushNotificationEvent,
    PushNotificationManager,
)
from ailf.schemas.a2a import Task, TaskDelta, TaskState


class TestPushNotificationManager(unittest.TestCase):
    """Test the push notification manager."""

    def setUp(self):
        """Set up the test case."""
        self.manager = PushNotificationManager()
        self.config = PushNotificationConfig(
            url="https://example.com/webhook",
            token="test-token",
            headers={"X-Test": "true"}
        )
        self.task_id = "test-task-1"
        self.manager.register_task(self.task_id, self.config)

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_push.httpx.AsyncClient")
    async def test_send_notification(self, mock_client):
        """Test sending a notification."""
        # Set up mock
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value.status_code = 200
        mock_client.return_value = mock_client_instance

        # Send notification
        result = await self.manager.send_notification(
            self.task_id,
            "test_event",
            {"key": "value"}
        )

        # Assert
        assert result is True
        mock_client_instance.post.assert_called_once()
        args, kwargs = mock_client_instance.post.call_args
        assert args[0] == "https://example.com/webhook"
        
        # Check headers
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["headers"]["Authorization"] == "Bearer test-token"
        assert kwargs["headers"]["X-Test"] == "true"
        
        # Check payload
        payload = kwargs["json"]
        assert payload["event_type"] == "test_event"
        assert payload["task_id"] == self.task_id
        assert payload["data"] == {"key": "value"}
        assert "timestamp" in payload

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_push.httpx.AsyncClient")
    async def test_notify_task_update(self, mock_client):
        """Test notifying about a task update."""
        # Set up mock
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value.status_code = 200
        mock_client.return_value = mock_client_instance

        # Create a task
        task = Task(
            id=self.task_id,
            state=TaskState.RUNNING,
            messages=[]
        )

        # Send notification
        result = await self.manager.notify_task_update(task)

        # Assert
        assert result is True
        mock_client_instance.post.assert_called_once()
        args, kwargs = mock_client_instance.post.call_args
        payload = kwargs["json"]
        assert payload["event_type"] == "task_update"
        assert payload["task_id"] == self.task_id
        assert "task" in payload["data"]
        assert payload["data"]["task"]["id"] == self.task_id
        assert payload["data"]["task"]["state"] == "running"

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_push.httpx.AsyncClient")
    async def test_notify_task_state_change(self, mock_client):
        """Test notifying about a task state change."""
        # Set up mock
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value.status_code = 200
        mock_client.return_value = mock_client_instance

        # Send notification
        result = await self.manager.notify_task_state_change(
            self.task_id,
            TaskState.COMPLETED
        )

        # Assert
        assert result is True
        mock_client_instance.post.assert_called_once()
        args, kwargs = mock_client_instance.post.call_args
        payload = kwargs["json"]
        assert payload["event_type"] == "task_state_change"
        assert payload["task_id"] == self.task_id
        assert payload["data"]["state"] == "completed"

    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_push.httpx.AsyncClient")
    async def test_notify_task_delta(self, mock_client):
        """Test notifying about a task delta."""
        # Set up mock
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value.status_code = 200
        mock_client.return_value = mock_client_instance

        # Create a delta
        delta = TaskDelta(
            state=TaskState.RUNNING,
            done=False
        )

        # Send notification
        result = await self.manager.notify_task_delta(self.task_id, delta)

        # Assert
        assert result is True
        mock_client_instance.post.assert_called_once()
        args, kwargs = mock_client_instance.post.call_args
        payload = kwargs["json"]
        assert payload["event_type"] == "task_delta"
        assert payload["task_id"] == self.task_id
        assert "delta" in payload["data"]
        assert payload["data"]["delta"]["state"] == "running"
        assert payload["data"]["delta"]["done"] is False

    def test_unregister_task(self):
        """Test unregistering a task."""
        # Register and unregister a task
        task_id = "test-task-2"
        self.manager.register_task(task_id, self.config)
        assert task_id in self.manager.task_configs
        
        self.manager.unregister_task(task_id)
        assert task_id not in self.manager.task_configs


class TestPushNotificationClient(unittest.TestCase):
    """Test the push notification client."""

    def setUp(self):
        """Set up the test case."""
        self.client = PushNotificationClient(
            callback_url="https://example.com/webhook",
            token="test-token"
        )
        self.task_id = "test-task-1"

    def test_get_notification_config(self):
        """Test getting the notification configuration."""
        config = self.client.get_notification_config()
        assert isinstance(config, PushNotificationConfig)
        assert config.url == "https://example.com/webhook"
        assert config.token == "test-token"

    @pytest.mark.asyncio
    async def test_process_notification(self):
        """Test processing a notification."""
        # Set up mock handlers
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        
        # Register handlers
        self.client.register_handler("task_update", handler1)
        self.client.register_handler("task_update", handler2)
        
        # Create notification
        notification = {
            "event_type": "task_update",
            "task_id": self.task_id,
            "data": {"task": {"id": self.task_id, "state": "running"}},
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        # Process notification
        await self.client.process_notification(notification)
        
        # Assert both handlers were called
        handler1.assert_called_once_with(
            self.task_id, 
            {"task": {"id": self.task_id, "state": "running"}}
        )
        handler2.assert_called_once_with(
            self.task_id, 
            {"task": {"id": self.task_id, "state": "running"}}
        )

    @pytest.mark.asyncio
    async def test_unknown_event_type(self):
        """Test processing a notification with an unknown event type."""
        # Set up mock handler
        handler = AsyncMock()
        
        # Register handler for a different event type
        self.client.register_handler("task_update", handler)
        
        # Create notification with unknown event type
        notification = {
            "event_type": "unknown_event",
            "task_id": self.task_id,
            "data": {"key": "value"},
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        # Process notification
        await self.client.process_notification(notification)
        
        # Assert handler was not called
        handler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
