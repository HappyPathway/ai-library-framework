"""Unit tests for A2A push notification serialization.

This module tests the serialization of push notifications, particularly
focusing on proper handling of datetime objects.
"""
import json
import unittest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ailf.communication.a2a_push import (
    DateTimeEncoder,
    PushNotificationClient,
    PushNotificationConfig,
    PushNotificationEvent,
    PushNotificationManager,
)
from ailf.schemas.a2a import TaskState


class TestDateTimeEncoder(unittest.TestCase):
    """Test the DateTimeEncoder class for JSON serialization."""
    
    def test_datetime_serialization(self):
        """Test that datetime objects are properly serialized."""
        test_time = datetime(2025, 1, 15, 12, 30, 45, tzinfo=UTC)
        test_data = {"timestamp": test_time, "value": "test"}
        
        # Encode to JSON using the DateTimeEncoder
        json_str = json.dumps(test_data, cls=DateTimeEncoder)
        
        # Verify the result is valid JSON and the datetime was converted to string
        decoded = json.loads(json_str)
        self.assertEqual(decoded["value"], "test")
        self.assertIsInstance(decoded["timestamp"], str)
        
        # Verify the format is ISO format
        expected_iso = test_time.isoformat()
        self.assertEqual(decoded["timestamp"], expected_iso)
    
    def test_mixed_data_serialization(self):
        """Test that mixed data types are properly serialized."""
        test_time = datetime(2025, 1, 15, 12, 30, 45, tzinfo=UTC)
        test_data = {
            "timestamp": test_time,
            "values": [1, 2, 3],
            "nested": {
                "created_at": test_time,
                "name": "test"
            }
        }
        
        # Encode to JSON using the DateTimeEncoder
        json_str = json.dumps(test_data, cls=DateTimeEncoder)
        
        # Verify the result is valid JSON and all datetimes were converted
        decoded = json.loads(json_str)
        self.assertEqual(decoded["values"], [1, 2, 3])
        self.assertIsInstance(decoded["timestamp"], str)
        self.assertIsInstance(decoded["nested"]["created_at"], str)
        self.assertEqual(decoded["nested"]["name"], "test")
    
    def test_non_datetime_values(self):
        """Test that non-datetime values are handled correctly."""
        test_data = {
            "string": "test",
            "number": 123,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "object": {"key": "value"}
        }
        
        # Encode to JSON using the DateTimeEncoder
        json_str = json.dumps(test_data, cls=DateTimeEncoder)
        
        # Verify all values are preserved correctly
        decoded = json.loads(json_str)
        self.assertEqual(decoded["string"], "test")
        self.assertEqual(decoded["number"], 123)
        self.assertEqual(decoded["boolean"], True)
        self.assertIsNone(decoded["null"])
        self.assertEqual(decoded["list"], [1, 2, 3])
        self.assertEqual(decoded["object"], {"key": "value"})


class TestPushNotificationSerialization(unittest.TestCase):
    """Test the serialization of push notifications."""
    
    @pytest.mark.asyncio
    @patch("ailf.communication.a2a_push.httpx.AsyncClient")
    async def test_notification_serialization(self, mock_client):
        """Test that notifications are properly serialized when sent."""
        # Set up test objects
        manager = PushNotificationManager()
        config = PushNotificationConfig(
            url="https://example.com/webhook",
            token="test-token"
        )
        task_id = "test-task-1"
        manager.register_task(task_id, config)
        
        # Create a notification with a datetime object
        test_time = datetime.now(UTC)
        event_data = {
            "timestamp": test_time,
            "state": TaskState.COMPLETED,
            "messages_count": 3
        }
        
        # Set up the mock client
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value.status_code = 200
        mock_client.return_value = mock_client_instance
        
        # Send the notification
        await manager.send_notification(
            task_id,
            "task_state_change",
            event_data
        )
        
        # Verify the request was made with proper data
        mock_client_instance.post.assert_called_once()
        
        # Extract and validate the request data
        call_args = mock_client_instance.post.call_args
        url_arg, kwargs = call_args[0][0], call_args[1]
        
        self.assertEqual(url_arg, "https://example.com/webhook")
        self.assertIn("json", kwargs)
        
        # The JSON data should have been serialized correctly
        json_data = kwargs["json"]
        self.assertIsInstance(json_data, dict)
        self.assertIn("data", json_data)
        
        # The timestamp should be a string in the serialized JSON
        self.assertIsInstance(json_data["data"].get("timestamp"), str)
        self.assertEqual(json_data["data"]["state"], TaskState.COMPLETED)
    
    def test_notification_event_serialization(self):
        """Test that PushNotificationEvent can be properly serialized."""
        test_time = datetime.now(UTC)
        
        # Create a notification event with a datetime
        event = PushNotificationEvent(
            event_type="task_update",
            task_id="test-task-1",
            data={
                "timestamp": test_time,
                "state": TaskState.COMPLETED,
                "updated_at": test_time
            },
            timestamp=test_time.isoformat()  # Already a string
        )
        
        # Convert to dict and then to JSON
        event_dict = event.model_dump()
        json_str = json.dumps(event_dict, cls=DateTimeEncoder)
        
        # Verify the result is valid JSON
        decoded = json.loads(json_str)
        self.assertEqual(decoded["event_type"], "task_update")
        self.assertEqual(decoded["task_id"], "test-task-1")
        
        # Check that both datetime fields were properly serialized
        self.assertIsInstance(decoded["data"]["timestamp"], str)
        self.assertIsInstance(decoded["data"]["updated_at"], str)


if __name__ == "__main__":
    unittest.main()
