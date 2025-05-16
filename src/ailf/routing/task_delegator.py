"""Enhanced TaskDelegator implementation for ailf.routing."""
import asyncio
import logging
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from ailf.schemas.routing import DelegatedTaskMessage, TaskResultMessage

# Set up proper logging
logger = logging.getLogger(__name__)

class TaskTrackingStore:
    """
    Handles tracking of delegated tasks and their status.
    
    This can be extended to use an external store like Redis for distributed scenarios.
    """
    
    def __init__(self):
        """Initialize the task tracking store."""
        self.pending_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_callbacks: Dict[str, List[Callable[[TaskResultMessage], Awaitable[None]]]] = {}
        self.max_history_items = 1000  # Limit history to avoid memory issues
    
    def track_task(self, task_message: DelegatedTaskMessage) -> None:
        """
        Start tracking a delegated task.
        
        :param task_message: The task message being delegated
        """
        self.pending_tasks[task_message.task_id] = {
            "task_message": task_message,
            "delegated_at": time.time(),
            "target_agent_id": task_message.target_agent_id,
            "task_name": task_message.task_name
        }
    
    def register_callback(
        self, 
        task_id: str, 
        callback: Callable[[TaskResultMessage], Awaitable[None]]
    ) -> None:
        """
        Register a callback for when a task result is received.
        
        :param task_id: The ID of the task to track
        :param callback: Async function to call when the result is received
        """
        if task_id not in self.task_callbacks:
            self.task_callbacks[task_id] = []
        self.task_callbacks[task_id].append(callback)
    
    def complete_task(self, result_message: TaskResultMessage) -> List[Callable]:
        """
        Mark a task as completed and get registered callbacks.
        
        :param result_message: The result message received
        :return: List of callbacks to invoke
        """
        task_id = result_message.task_id
        
        # Move from pending to completed
        if task_id in self.pending_tasks:
            task_data = self.pending_tasks.pop(task_id)
            task_data["completed_at"] = time.time()
            task_data["status"] = result_message.status
            task_data["result"] = result_message.result
            task_data["error_message"] = result_message.error_message
            
            # Store in completed tasks
            self.completed_tasks[task_id] = task_data
            
            # Prune old completed tasks if needed
            if len(self.completed_tasks) > self.max_history_items:
                oldest_task_id = min(self.completed_tasks.items(), 
                                     key=lambda x: x[1].get("completed_at", 0))[0]
                self.completed_tasks.pop(oldest_task_id, None)
        
        # Get and clear callbacks
        callbacks = self.task_callbacks.pop(task_id, [])
        return callbacks
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific task.
        
        :param task_id: The task ID to check
        :return: Task status information or None if not found
        """
        if task_id in self.pending_tasks:
            status_data = self.pending_tasks[task_id].copy()
            status_data["status"] = "pending"
            return status_data
        
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        
        return None
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all pending tasks.
        
        :return: List of pending tasks with their status information
        """
        return [
            {"task_id": task_id, **task_data} 
            for task_id, task_data in self.pending_tasks.items()
        ]

class TaskDelegator:
    """
    Enhanced TaskDelegator that manages delegation of tasks to other agents and tracks results.
    
    Features:
    - Sends DelegatedTaskMessage to target agents
    - Tracks task status and completion
    - Supports callbacks for task results
    - Provides task status querying
    """
    
    def __init__(
        self, 
        message_client: Any,  # Should ideally implement a messaging interface
        source_agent_id: Optional[str] = None,
        task_store: Optional[TaskTrackingStore] = None
    ):
        """
        Initialize the TaskDelegator.
        
        :param message_client: Client for sending messages between agents
        :param source_agent_id: ID of this agent (source of delegated tasks)
        :param task_store: Optional custom task tracking store
        """
        self.message_client = message_client
        self.source_agent_id = source_agent_id
        self.task_store = task_store or TaskTrackingStore()
    
    async def delegate_task(
        self, 
        task_name: str,
        task_input: Dict[str, Any],
        target_agent_id: str,
        task_id: Optional[str] = None,
        timeout: Optional[float] = None,
        wait_for_result: bool = False
    ) -> Union[str, TaskResultMessage]:
        """
        Delegate a task to another agent.
        
        :param task_name: Name of the task to delegate
        :param task_input: Input data for the task
        :param target_agent_id: ID of the target agent
        :param task_id: Optional custom task ID (generated if not provided)
        :param timeout: Optional timeout for waiting (if wait_for_result=True)
        :param wait_for_result: Whether to wait for the task result
        :return: Task ID if not waiting, or TaskResultMessage if waiting
        """
        # Generate task ID if not provided
        if not task_id:
            task_id = str(uuid.uuid4())
        
        # Create task message
        task_message = DelegatedTaskMessage(
            task_id=task_id,
            target_agent_id=target_agent_id,
            task_name=task_name,
            task_input=task_input,
            source_agent_id=self.source_agent_id
        )
        
        # Track the task
        self.task_store.track_task(task_message)
        
        # Send the task
        await self._send_task_message(task_message)
        
        # If waiting for result, set up a future
        if wait_for_result:
            result = await self._wait_for_result(task_id, timeout)
            return result
        
        # Otherwise just return the task ID
        return task_id
    
    async def delegate_task_message(
        self, 
        task_message: DelegatedTaskMessage,
        wait_for_result: bool = False,
        timeout: Optional[float] = None
    ) -> Union[str, TaskResultMessage]:
        """
        Delegate a task using a pre-constructed DelegatedTaskMessage.
        
        :param task_message: The task message to send
        :param wait_for_result: Whether to wait for the result
        :param timeout: Optional timeout for waiting
        :return: Task ID if not waiting, or TaskResultMessage if waiting
        """
        # Ensure source agent ID is set
        if self.source_agent_id and not task_message.source_agent_id:
            task_message.source_agent_id = self.source_agent_id
        
        # Track the task
        self.task_store.track_task(task_message)
        
        # Send the task
        await self._send_task_message(task_message)
        
        # If waiting for result, set up a future
        if wait_for_result:
            result = await self._wait_for_result(task_message.task_id, timeout)
            return result
        
        return task_message.task_id
    
    async def _send_task_message(self, task_message: DelegatedTaskMessage) -> None:
        """
        Send a task message using the message client.
        
        :param task_message: The task message to send
        """
        if hasattr(self.message_client, 'send_message'):
            try:
                # Assuming message client has a send_message method
                await self.message_client.send_message(
                    target=task_message.target_agent_id,
                    message=task_message
                )
                logger.info(f"Task {task_message.task_id} delegated to {task_message.target_agent_id}")
            except Exception as e:
                logger.error(f"Error sending task message: {e}")
                raise
        else:
            # Fallback for testing or simple cases
            logger.info(f"[TaskDelegator] Would send task {task_message.task_id} "
                       f"to {task_message.target_agent_id}: {task_message.task_name}")
    
    async def _wait_for_result(self, task_id: str, timeout: Optional[float] = None) -> TaskResultMessage:
        """
        Wait for a task result to be received.
        
        :param task_id: The task ID to wait for
        :param timeout: Optional timeout in seconds
        :return: The task result message
        :raises asyncio.TimeoutError: If timeout is reached
        """
        # Create a future to be resolved when the result arrives
        result_future = asyncio.Future()
        
        # Register callback
        async def on_result(result: TaskResultMessage) -> None:
            if not result_future.done():
                result_future.set_result(result)
        
        self.task_store.register_callback(task_id, on_result)
        
        # Wait for the result with optional timeout
        try:
            if timeout:
                return await asyncio.wait_for(result_future, timeout)
            else:
                return await result_future
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for task {task_id}")
            raise
    
    async def handle_task_result(self, result_message: TaskResultMessage) -> None:
        """
        Handle a received task result message.
        
        :param result_message: The task result message
        """
        task_id = result_message.task_id
        logger.info(f"Received result for task {task_id}: {result_message.status}")
        
        # Mark task as completed and get callbacks
        callbacks = self.task_store.complete_task(result_message)
        
        # Execute callbacks
        for callback in callbacks:
            try:
                await callback(result_message)
            except Exception as e:
                logger.error(f"Error in task result callback for {task_id}: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific task.
        
        :param task_id: The task ID to check
        :return: Task status information or None if not found
        """
        return self.task_store.get_task_status(task_id)
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        Get all pending tasks.
        
        :return: List of pending tasks with their status information
        """
        return self.task_store.get_pending_tasks()
