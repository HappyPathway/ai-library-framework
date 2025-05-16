"""Push notification support for the A2A protocol.

This module provides support for A2A push notifications, allowing servers to notify clients
about task state changes and other events.
"""
import asyncio
import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that can handle datetime objects."""
    
    def default(self, obj):
        """Convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

import httpx
from pydantic import BaseModel, Field

from ailf.schemas.a2a import Task, TaskDelta, TaskState

logger = logging.getLogger(__name__)


class PushNotificationConfig(BaseModel):
    """Configuration for push notifications."""
    url: str = Field(..., description="The URL to send notifications to")
    token: str = Field(..., description="Authentication token for the notification endpoint")
    headers: Optional[Dict[str, str]] = Field(
        default=None, 
        description="Additional headers to include with notifications"
    )


class PushNotificationEvent(BaseModel):
    """Event for push notifications."""
    event_type: str = Field(..., description="Type of notification event")
    task_id: str = Field(..., description="ID of the task that generated the event")
    data: Dict[str, Any] = Field(..., description="Event-specific data")
    timestamp: str = Field(..., description="ISO 8601 timestamp of when the event occurred")


class PushNotificationManager:
    """Manager for sending push notifications to clients."""
    
    def __init__(self):
        """Initialize a new push notification manager."""
        self.task_configs: Dict[str, PushNotificationConfig] = {}
        
    def register_task(self, task_id: str, config: PushNotificationConfig) -> None:
        """Register a task for push notifications.
        
        Args:
            task_id: The ID of the task.
            config: The notification configuration.
        """
        self.task_configs[task_id] = config
        
    def unregister_task(self, task_id: str) -> None:
        """Unregister a task from push notifications.
        
        Args:
            task_id: The ID of the task.
        """
        if task_id in self.task_configs:
            del self.task_configs[task_id]
        
    async def send_notification(
        self, 
        task_id: str, 
        event_type: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Send a notification for a task.
        
        Args:
            task_id: The ID of the task.
            event_type: The type of notification event.
            data: The event data.
            
        Returns:
            True if the notification was sent, False otherwise.
        """
        if task_id not in self.task_configs:
            logger.warning(f"No push notification config for task {task_id}")
            return False
            
        config = self.task_configs[task_id]
        
        # Create notification payload
        notification = PushNotificationEvent(
            event_type=event_type,
            task_id=task_id,
            data=data,
            timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
        )
        
        # Send the notification
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Content-Type": "application/json", 
                    "Authorization": f"Bearer {config.token}"
                }
                
                if config.headers:
                    headers.update(config.headers)
                    
                # Convert to JSON-safe dictionary first with custom encoder
                notification_dict = json.loads(
                    json.dumps(notification.model_dump(), cls=DateTimeEncoder)
                )
                
                response = await client.post(
                    config.url, 
                    json=notification_dict,
                    headers=headers
                )
                
                response.raise_for_status()
                logger.info(f"Push notification sent for task {task_id}: {event_type}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send push notification for task {task_id}: {str(e)}")
            return False
            
    async def notify_task_update(self, task: Task) -> bool:
        """Send a task update notification.
        
        Args:
            task: The updated task.
            
        Returns:
            True if the notification was sent, False otherwise.
        """
        return await self.send_notification(
            task.id,
            "task_update",
            {"task": task.model_dump(exclude_none=True)}
        )
        
    async def notify_task_delta(self, task_id: str, delta: TaskDelta) -> bool:
        """Send a task delta notification.
        
        Args:
            task_id: The ID of the task.
            delta: The task delta.
            
        Returns:
            True if the notification was sent, False otherwise.
        """
        return await self.send_notification(
            task_id,
            "task_delta",
            {"delta": delta.model_dump(exclude_none=True)}
        )
            
    async def notify_task_state_change(self, task_id: str, new_state: TaskState) -> bool:
        """Send a notification about a task state change.
        
        Args:
            task_id: The ID of the task.
            new_state: The new state of the task.
            
        Returns:
            True if the notification was sent, False otherwise.
        """
        return await self.send_notification(
            task_id,
            "task_state_change",
            {"state": new_state}
        )


class PushNotificationClient:
    """Client for handling push notifications from A2A servers."""
    
    def __init__(self, callback_url: str, token: str):
        """Initialize a new push notification client.
        
        Args:
            callback_url: The URL where notifications will be received.
            token: The authentication token for the callback URL.
        """
        self.callback_url = callback_url
        self.token = token
        self.handlers = {
            "task_update": [],
            "task_delta": [],
            "task_state_change": [],
        }
        
    def get_notification_config(self) -> PushNotificationConfig:
        """Get the notification configuration for this client.
        
        Returns:
            A PushNotificationConfig object.
        """
        return PushNotificationConfig(url=self.callback_url, token=self.token)
        
    def register_handler(self, event_type: str, handler_func: callable) -> None:
        """Register a handler for notification events.
        
        Args:
            event_type: The type of event to handle.
            handler_func: The function to call when the event occurs.
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
            
        self.handlers[event_type].append(handler_func)
        
    async def process_notification(self, notification: Dict[str, Any]) -> None:
        """Process an incoming notification.
        
        This method should be called by your webhook handler when a notification
        is received at the callback URL.
        
        Args:
            notification: The notification data.
        """
        try:
            event = PushNotificationEvent(**notification)
            
            if event.event_type in self.handlers:
                for handler in self.handlers[event.event_type]:
                    try:
                        await handler(event.task_id, event.data)
                    except Exception as e:
                        logger.error(f"Error in notification handler: {str(e)}")
            else:
                logger.warning(f"No handlers for event type: {event.event_type}")
                
        except Exception as e:
            logger.error(f"Failed to process notification: {str(e)}")


# Import missing datetime module
import datetime
