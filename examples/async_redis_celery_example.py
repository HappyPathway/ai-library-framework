"""Example of combining AsyncIO tasks with Redis messaging and Celery.

This example demonstrates how to build an agent that:
1. Uses AsyncIO for concurrent operations
2. Uses Redis PubSub for real-time messaging
3. Offloads heavy work to Celery tasks
4. Coordinates results between components

To run this example:
1. Make sure Redis is running (`redis-server`)
2. Start a Celery worker in a separate terminal:
   `celery -A utils.workers.celery_app worker --loglevel=INFO`
3. Run this script: `python examples/async_redis_celery_example.py`
"""

import asyncio
import json
import time
import uuid
from typing import Any, Dict, List

from celery.result import AsyncResult

# Import AsyncIO task management
from utils.async_tasks import TaskManager, TaskStatus
# Configure logging
from utils.logging import setup_logging
# Import Redis components
from utils.messaging.redis import AsyncRedisClient, RedisPubSub
# Import Celery tasks
from utils.workers.tasks import analyze_content, process_document

logger = setup_logging("async_redis_celery_example")


class CoordinatorAgent:
    """Agent that coordinates AsyncIO, Redis and Celery.

    This agent demonstrates an architecture pattern where:
    - AsyncIO handles concurrent operations and coordination
    - Redis provides real-time messaging between components
    - Celery handles CPU/memory-intensive background tasks
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize the agent.

        Args:
            redis_url: Redis connection URL
        """
        # Create Redis clients
        self.redis = AsyncRedisClient(url=redis_url)
        self.pubsub = RedisPubSub(client=self.redis)

        # Create task manager
        self.task_manager = TaskManager()

        # State tracking
        self.running = False
        self.pending_tasks: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, Any] = {}

    async def start(self):
        """Start the agent."""
        if self.running:
            return

        self.running = True
        logger.info("Starting coordinator agent")

        # Start task manager
        await self.task_manager.start()

        # Initialize Redis connection
        await self.redis.connect()

        # Subscribe to Redis channels
        await self.pubsub.subscribe("agent:requests", self._handle_request)
        await self.pubsub.subscribe("agent:results", self._handle_result)

        logger.info("Coordinator agent started")

    async def stop(self):
        """Stop the agent."""
        if not self.running:
            return

        self.running = False
        logger.info("Stopping coordinator agent")

        # Unsubscribe from Redis channels
        await self.pubsub.unsubscribe_all()

        # Stop task manager
        await self.task_manager.stop()

        # Close Redis connection
        await self.redis.disconnect()

        logger.info("Coordinator agent stopped")

    async def process_request(self, request_data: Dict[str, Any]) -> str:
        """Process an incoming request.

        This showcases coordinating between AsyncIO tasks and Celery tasks.

        Args:
            request_data: Request data dictionary

        Returns:
            Request ID for tracking
        """
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())

        # Store request info
        self.pending_tasks[request_id] = {
            "status": "pending",
            "request": request_data,
            "celery_tasks": [],
            "started_at": time.time()
        }

        # Submit the processing task
        await self.task_manager.submit(
            self._process_request_workflow(request_id, request_data),
            task_id=f"workflow:{request_id}",
            metadata={"request_id": request_id}
        )

        return request_id

    async def _process_request_workflow(self, request_id: str, request_data: Dict[str, Any]):
        """Main processing workflow combining AsyncIO and Celery.

        Args:
            request_id: Request ID
            request_data: Request data

        Returns:
            Processing results
        """
        try:
            logger.info(f"Starting workflow for request {request_id}")

            # Update status
            self.pending_tasks[request_id]["status"] = "processing"

            # Extract request parameters
            document_ids = request_data.get("document_ids", [])
            perform_analysis = request_data.get("analyze", False)

            # Step 1: Process documents in parallel using Celery
            celery_tasks = []
            for doc_id in document_ids:
                # Delegate document processing to Celery
                logger.info(f"Submitting document {doc_id} to Celery")
                task = process_document.delay(
                    doc_id, {"request_id": request_id})
                celery_tasks.append(task)
                self.pending_tasks[request_id]["celery_tasks"].append(task.id)

            # Step 2: Wait for all document processing to complete
            # This demonstrates waiting for Celery tasks from AsyncIO
            document_results = []
            for task in celery_tasks:
                # Check task status with timeout
                timeout = 60  # Maximum wait time for each task
                start_time = time.time()
                while not task.ready() and time.time() - start_time < timeout:
                    # Use asyncio.sleep to allow other tasks to run
                    await asyncio.sleep(0.5)

                if task.ready():
                    result = task.get()  # Get the result
                    document_results.append(result)
                    logger.info(f"Task {task.id} completed")
                else:
                    logger.warning(f"Task {task.id} timed out")

            # Step 3: Optional analysis step
            analysis_result = None
            if perform_analysis and document_results:
                # Combine document texts (simplified example)
                combined_text = f"Analysis of {len(document_results)} documents"

                # Submit to analysis task
                analysis_task = analyze_content.delay(combined_text)

                # Wait for analysis to complete
                timeout = 30
                start_time = time.time()
                while not analysis_task.ready() and time.time() - start_time < timeout:
                    await asyncio.sleep(0.5)

                if analysis_task.ready():
                    analysis_result = analysis_task.get()

            # Step 4: Publish results to Redis
            final_result = {
                "request_id": request_id,
                "documents": document_results,
                "analysis": analysis_result,
                "completed_at": time.time()
            }

            # Store result
            self.results[request_id] = final_result

            # Publish to results channel
            await self.pubsub.publish("agent:results", json.dumps({
                "request_id": request_id,
                "status": "completed"
            }))

            # Update status
            self.pending_tasks[request_id]["status"] = "completed"

            logger.info(f"Workflow completed for request {request_id}")
            return final_result

        except Exception as e:
            logger.error(
                f"Error in workflow for request {request_id}: {str(e)}")

            # Update status
            self.pending_tasks[request_id]["status"] = "failed"
            self.pending_tasks[request_id]["error"] = str(e)

            # Publish error to results channel
            await self.pubsub.publish("agent:results", json.dumps({
                "request_id": request_id,
                "status": "error",
                "error": str(e)
            }))

            raise

    async def get_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of a request.

        Args:
            request_id: Request ID

        Returns:
            Status information
        """
        # Check if we have a result
        if request_id in self.results:
            return {
                "request_id": request_id,
                "status": "completed",
                "result": self.results[request_id]
            }

        # Check if request is pending
        if request_id in self.pending_tasks:
            task_info = self.pending_tasks[request_id]

            # Check Celery task status
            celery_statuses = []
            for task_id in task_info.get("celery_tasks", []):
                result = AsyncResult(task_id)
                celery_statuses.append({
                    "task_id": task_id,
                    "status": result.status
                })

            return {
                "request_id": request_id,
                "status": task_info["status"],
                "celery_tasks": celery_statuses,
                "started_at": task_info["started_at"]
            }

        # Request not found
        return {
            "request_id": request_id,
            "status": "not_found"
        }

    async def _handle_request(self, channel: str, message: str):
        """Handle incoming requests from Redis PubSub.

        Args:
            channel: Redis channel
            message: Message payload
        """
        try:
            data = json.loads(message)
            logger.info(f"Received request on {channel}: {data}")

            # Process the request
            request_id = await self.process_request(data)

            # Acknowledge receipt
            await self.pubsub.publish("agent:ack", json.dumps({
                "request_id": request_id,
                "status": "processing"
            }))

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")

    async def _handle_result(self, channel: str, message: str):
        """Handle incoming results from Redis PubSub.

        Args:
            channel: Redis channel
            message: Message payload
        """
        try:
            data = json.loads(message)
            logger.info(f"Received result on {channel}: {data}")

            # Here you could trigger further actions based on results
            # This is just a placeholder in this example

        except Exception as e:
            logger.error(f"Error handling result: {str(e)}")


async def run_example():
    """Run the complete example."""
    # Create agent
    agent = CoordinatorAgent()

    try:
        # Start the agent
        await agent.start()

        # Submit a test request directly
        request_data = {
            "document_ids": ["doc-1", "doc-2", "doc-3"],
            "analyze": True
        }

        logger.info(f"Submitting test request: {request_data}")
        request_id = await agent.process_request(request_data)

        # Poll for status a few times
        for _ in range(5):
            await asyncio.sleep(2)
            status = await agent.get_status(request_id)
            logger.info(f"Request status: {status}")

        # Also demonstrate pubsub by publishing a request
        logger.info("Publishing test request via Redis PubSub")
        pubsub = RedisPubSub(client=AsyncRedisClient())
        await pubsub.connect()

        await pubsub.publish("agent:requests", json.dumps({
            "document_ids": ["doc-pubsub-1"],
            "analyze": False
        }))

        # Keep running to process PubSub messages
        logger.info("Waiting for all tasks to complete...")
        await asyncio.sleep(10)

    finally:
        # Clean up
        await agent.stop()


if __name__ == "__main__":
    # Run the example
    asyncio.run(run_example())
