"""Tests for the enhanced ailf.routing components."""
import pytest
import asyncio
from typing import Dict, Any, List, Optional

import uuid
from ailf.routing import TaskDelegator, AgentRouter, RouteRule
from ailf.schemas.routing import DelegatedTaskMessage, TaskResultMessage, TaskStatus
from ailf.schemas.interaction import AnyInteractionMessage

class MockInteractionMessage(AnyInteractionMessage):
    """Mock implementation of AnyInteractionMessage for testing."""
    
    class Header:
        """Mock header class."""
        def __init__(self, message_id: str = None, target_system: Optional[str] = None):
            self.message_id = message_id or str(uuid.uuid4())
            self.target_system = target_system
    
    def __init__(
        self, 
        content: str = "", 
        message_type: str = "text",
        target_system: Optional[str] = None
    ):
        self.content = content
        self.type = message_type
        self.header = self.Header(target_system=target_system)

class MockMessageClient:
    """Mock message client for testing."""
    
    def __init__(self):
        """Initialize mock client."""
        self.sent_messages = []
        self.message_handlers = []
    
    async def send_message(self, target: str, message: Any):
        """Mock sending a message."""
        self.sent_messages.append((target, message))
    
    def register_handler(self, handler):
        """Register a message handler."""
        self.message_handlers.append(handler)
    
    async def deliver_message(self, message):
        """Simulate delivering a message to handlers."""
        for handler in self.message_handlers:
            await handler(message)

@pytest.fixture
def message_client():
    """Create a mock message client."""
    return MockMessageClient()

@pytest.fixture
def task_delegator(message_client):
    """Create a TaskDelegator with mock client."""
    return TaskDelegator(
        message_client=message_client,
        source_agent_id="test-agent"
    )

@pytest.fixture
def agent_router():
    """Create an AgentRouter for testing."""
    router = AgentRouter(debug_mode=True)
    
    # Add some test handlers
    async def handle_query(message):
        return {"response": "Query processed", "content": message.content}
    
    async def handle_command(message):
        return {"status": "Command executed", "content": message.content}
    
    async def fallback_handler(message):
        return {"status": "Fallback used", "content": message.content}
    
    router.add_internal_handler("query_handler", handle_query)
    router.add_internal_handler("command_handler", handle_command)
    router.add_internal_handler("fallback_handler", fallback_handler)
    
    # Add routing rules
    router.add_routing_rule(
        RouteRule(
            name="query_rule",
            match_keywords=["question", "what", "how", "why"],
            target_handler="query_handler",
            priority=10
        )
    )
    
    router.add_routing_rule(
        RouteRule(
            name="command_rule",
            match_keywords=["do", "execute", "run"],
            target_handler="command_handler",
            priority=10
        )
    )
    
    return router

@pytest.mark.asyncio
async def test_task_delegator_send(task_delegator, message_client):
    """Test delegating a task."""
    task_id = await task_delegator.delegate_task(
        task_name="test_task",
        task_input={"param": "value"},
        target_agent_id="target-agent"
    )
    
    # Check that message was sent
    assert len(message_client.sent_messages) == 1
    target, message = message_client.sent_messages[0]
    
    assert target == "target-agent"
    assert isinstance(message, DelegatedTaskMessage)
    assert message.task_name == "test_task"
    assert message.task_input == {"param": "value"}
    assert message.source_agent_id == "test-agent"
    assert message.task_id == task_id

@pytest.mark.asyncio
async def test_task_delegator_wait_for_result(task_delegator, message_client):
    """Test delegating a task and waiting for result."""
    # Start task delegation with wait_for_result
    task_future = asyncio.create_task(
        task_delegator.delegate_task(
            task_name="async_task",
            task_input={"param": "value"},
            target_agent_id="target-agent",
            wait_for_result=True,
            timeout=1.0  # Short timeout for test
        )
    )
    
    # Wait a bit to ensure delegation happened
    await asyncio.sleep(0.1)
    
    # Check that task was sent
    assert len(message_client.sent_messages) == 1
    target, message = message_client.sent_messages[0]
    task_id = message.task_id
    
    # Create and deliver a task result
    result = TaskResultMessage(
        task_id=task_id,
        status=TaskStatus.COMPLETED,
        result={"output": "task result"},
        source_agent_id="target-agent"
    )
    
    await task_delegator.handle_task_result(result)
    
    # Verify the task future resolved with our result
    task_result = await task_future
    assert task_result.status == TaskStatus.COMPLETED
    assert task_result.result == {"output": "task result"}

@pytest.mark.asyncio
async def test_agent_router_rule_based(agent_router):
    """Test agent router with rule-based routing."""
    # Create a query message
    query_message = MockInteractionMessage(
        content="I have a question about something",
        message_type="text"
    )
    
    # Route the message
    result = await agent_router.route_message(query_message)
    
    # Check the result
    assert result["response"] == "Query processed"
    assert result["content"] == query_message.content
    
    # Create a command message
    command_message = MockInteractionMessage(
        content="Please execute this command",
        message_type="text"
    )
    
    # Route the command message
    result = await agent_router.route_message(command_message)
    
    # Check the result
    assert result["status"] == "Command executed"
    assert result["content"] == command_message.content

@pytest.mark.asyncio
async def test_agent_router_direct_targeting(agent_router):
    """Test agent router with direct targeting via message header."""
    # Create a message with explicit target
    direct_message = MockInteractionMessage(
        content="Direct message",
        message_type="text",
        target_system="fallback_handler"
    )
    
    # Route the message
    result = await agent_router.route_message(direct_message)
    
    # Check the result
    assert result["status"] == "Fallback used"
    assert result["content"] == direct_message.content

@pytest.mark.asyncio
async def test_integration_router_and_delegator(agent_router, task_delegator, message_client):
    """Test integration between router and delegator."""
    # Create a decorator function for routing external messages
    async def route_and_delegate(message, router, delegator):
        """Route a message and delegate if needed."""
        result = await router.route_message(message)
        
        # If result is a route decision for external agent
        if hasattr(result, "target_agent_id") and result.target_agent_id:
            # Delegate task
            task_message = DelegatedTaskMessage(
                task_id=str(uuid.uuid4()),
                target_agent_id=result.target_agent_id,
                task_name="process_message",
                task_input={"message_content": message.content},
                source_agent_id="test-agent"
            )
            return await delegator.delegate_task_message(task_message)
        
        return result
    
    # Add a rule for external delegation
    agent_router.add_routing_rule(
        RouteRule(
            name="external_rule",
            match_keywords=["external", "delegate"],
            target_agent_id="external-agent",
            priority=20
        )
    )
    
    # Test with message that should be handled externally
    external_message = MockInteractionMessage(
        content="Please delegate this task to an external agent",
        message_type="text"
    )
    
    # Route and delegate
    result = await route_and_delegate(external_message, agent_router, task_delegator)
    
    # Verify a message was sent to the external agent
    assert len(message_client.sent_messages) == 1
    target, sent_message = message_client.sent_messages[0]
    
    assert target == "external-agent"
    assert isinstance(sent_message, DelegatedTaskMessage)
    assert sent_message.task_name == "process_message"
    assert "delegate this task" in sent_message.task_input["message_content"]
