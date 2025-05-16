"""Example of using A2A push notifications with the AILF framework.

This example demonstrates how to:
1. Set up push notifications for A2A tasks on the server side
2. Create a webhook handler to receive push notifications on the client side
3. Process and respond to push notifications
"""
import asyncio
import json
import logging
from datetime import datetime, UTC
from typing import Dict, Any, List

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_push import (
    PushNotificationClient, 
    PushNotificationManager,
    PushNotificationConfig
)
from ailf.schemas.a2a import (
    Task,
    TaskState,
    Message,
    MessagePart,
)

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs for our example
A2A_SERVER_URL = "http://localhost:8000"
WEBHOOK_URL = "http://localhost:8001/webhook"

# Store received notifications for demonstration
received_notifications = []

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

async def setup_notification_client():
    """Set up a notification client to receive push notifications."""
    # Create a push notification client
    push_client = PushNotificationClient(
        callback_url=WEBHOOK_URL,
        token="example-token"
    )
    
    # Define handlers for different notification types
    async def handle_task_update(task_id: str, data: Dict[str, Any]):
        logger.info(f"Received task update for task {task_id}")
        received_notifications.append({
            "type": "task_update",
            "task_id": task_id,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat()
        })
    
    async def handle_task_state_change(task_id: str, data: Dict[str, Any]):
        logger.info(f"Task {task_id} state changed to: {data.get('state')}")
        received_notifications.append({
            "type": "task_state_change",
            "task_id": task_id,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat()
        })
    
    async def handle_custom_notification(task_id: str, data: Dict[str, Any]):
        logger.info(f"Custom notification for task {task_id}: {data}")
        received_notifications.append({
            "type": "custom",
            "task_id": task_id,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat()
        })
    
    # Register handlers for different event types
    push_client.register_handler("task_update", handle_task_update)
    push_client.register_handler("task_state_change", handle_task_state_change)
    push_client.register_handler("progress_update", handle_custom_notification)
    
    return push_client

def create_webhook_app(push_client: PushNotificationClient):
    """Create a FastAPI app with a webhook endpoint for push notifications."""
    app = FastAPI(title="A2A Push Notification Webhook")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.post("/webhook")
    async def webhook(request: Request):
        """Webhook endpoint that receives push notifications."""
        try:
            # Get the notification data
            notification = await request.json()
            logger.info(f"Received notification: {json.dumps(notification, cls=DateTimeEncoder)[:200]}...")
            
            # Process the notification
            await push_client.process_notification(notification)
            
            # Return a success response
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error processing notification: {e}")
            return {"status": "error", "message": str(e)}
    
    @app.get("/notifications")
    async def get_notifications():
        """Get all received notifications."""
        return {"notifications": received_notifications}
    
    return app

async def demonstrate_push_notifications():
    """Demonstrate A2A push notifications."""
    logger.info("Starting push notification example...")
    
    try:
        # In a real scenario, you would have an actual A2A server running
        # For demonstration, we'll just show the code pattern
        
        # 1. Create an A2A client
        client = A2AClient(base_url=A2A_SERVER_URL)
        
        # 2. Create a push notification client
        push_client = await setup_notification_client()
        
        # 3. Get the notification config
        config = push_client.get_notification_config()
        logger.info(f"Push notification config: {json.dumps(config.model_dump(), cls=DateTimeEncoder)}")
        
        # 4. In a real scenario, you would:
        # - Create a task with the A2A client
        # - Register the task for push notifications
        # - Send messages to the task
        # - Receive notifications via the webhook
        
        logger.info("""
        Push notification flow:
        
        1. Client creates a task on A2A server
        2. Client registers task for push notifications with webhook URL
        3. Client sends message to task
        4. Server processes task and sends push notifications to webhook
        5. Webhook receives notifications and processes them
        
        This example sets up the webhook and notification handlers.
        To run it with a real A2A server, start the server and run:
            
            uvicorn push_notification_example:webhook_app --port 8001
            
        Then create tasks and register them for push notifications.
        """)
        
        return push_client
        
    except Exception as e:
        logger.error(f"Error in push notification example: {e}")
        raise

# Create FastAPI app for the webhook
push_client_instance = asyncio.run(setup_notification_client())
webhook_app = create_webhook_app(push_client_instance)

if __name__ == "__main__":
    logger.info("Starting webhook server...")
    uvicorn.run(webhook_app, host="0.0.0.0", port=8001)
