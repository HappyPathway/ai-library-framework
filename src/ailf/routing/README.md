# Agent Routing and Task Delegation

This module provides components for routing incoming messages to appropriate handlers and delegating tasks to other agents or workers.

## Core Components

### `TaskDelegator`

The `TaskDelegator` manages the delegation of tasks to other agents or worker processes and tracks their results.

Key features:
- Send `DelegatedTaskMessage` to target agents
- Track task status and completion
- Support callbacks for task results
- Provide task status querying

### `AgentRouter`

The `AgentRouter` directs incoming messages to appropriate internal handlers or other agents, using either predefined rules or AI-driven decisions.

Key features:
- Rule-based routing
- LLM-driven routing decisions
- Support for both internal handlers and external delegation
- Customizable matching logic

## Usage Examples

### Using the `TaskDelegator`

```python
from ailf.routing import TaskDelegator
from ailf.messaging import MessageClient  # Your messaging implementation

# Initialize a message client (implementation-specific)
message_client = MessageClient(broker_url="redis://localhost:6379")

# Create a task delegator
delegator = TaskDelegator(
    message_client=message_client,
    source_agent_id="agent-123"
)

# Simple delegation (fire-and-forget)
task_id = await delegator.delegate_task(
    task_name="analyze_text",
    task_input={"text": "Analyze this text"},
    target_agent_id="analysis-agent"
)

# Delegation with waiting for result
result = await delegator.delegate_task(
    task_name="analyze_text",
    task_input={"text": "Analyze this text"},
    target_agent_id="analysis-agent",
    wait_for_result=True,
    timeout=10.0  # Optional timeout
)

# Check status of a task
status = delegator.get_task_status(task_id)

# Handle incoming task results
async def on_message(message):
    # Determine if this is a task result message
    if is_task_result_message(message):
        await delegator.handle_task_result(message)

# Register message handler with your message client
message_client.on_message(on_message)
```

### Using the `AgentRouter`

```python
from ailf.routing import AgentRouter, RouteRule
from ailf.schemas.interaction import AnyInteractionMessage

# Initialize router (optionally with AI engine)
router = AgentRouter(ai_engine=None, debug_mode=True)

# Add internal message handlers
async def handle_query(message: AnyInteractionMessage):
    # Handle query messages
    return {"response": "Query processed"}

async def handle_command(message: AnyInteractionMessage):
    # Handle command messages
    return {"status": "Command executed"}

# Register handlers
router.add_internal_handler("query_handler", handle_query)
router.add_internal_handler("command_handler", handle_command)

# Add routing rules
router.add_routing_rule(
    RouteRule(
        name="query_rule",
        match_keywords=["what", "how", "why", "when"],
        target_handler="query_handler",
        priority=10
    )
)

router.add_routing_rule(
    RouteRule(
        name="command_rule",
        match_keywords=["do", "execute", "run", "perform"],
        target_handler="command_handler",
        priority=10
    )
)

# Use the router to handle a message
async def process_message(message: AnyInteractionMessage):
    result = await router.route_message(message)
    
    # Check if the message should be delegated externally
    if isinstance(result, RouteDecision) and result.target_agent_id:
        # Delegate to another agent
        task_message = DelegatedTaskMessage(
            task_id=f"task-{uuid.uuid4()}",
            target_agent_id=result.target_agent_id,
            task_name="process_message",
            task_input={"message": message.model_dump()}
        )
        await delegator.delegate_task_message(task_message)
    else:
        # Process the result from the internal handler
        return result
```

### Decorator-based Routing

```python
from ailf.routing import AgentRouter

router = AgentRouter()

# Register a handler with routing rule in one step
@router.handler_decorator(match_type="query", match_keywords=["weather"])
async def handle_weather_query(message):
    # Handle weather queries
    return {"weather": "sunny"}

@router.handler_decorator(match_type="command", match_keywords=["reminder", "schedule"])
async def handle_reminder(message):
    # Handle reminder/scheduling commands
    return {"scheduled": True}
```

## Integration with `AIEngine`

For LLM-driven routing, the router expects an AI engine with these capabilities:
- `analyze(context, output_schema)` - Analyze context and return structured output
- Optional `preprocess_tool_input` and `postprocess_tool_output` for tool integration

Example:

```python
from ailf.routing import AgentRouter
from ailf.ai_engine import AIEngine

# Initialize AI engine
ai_engine = AIEngine(model="gpt-4", temperature=0.2)

# Create router with AI engine
router = AgentRouter(ai_engine=ai_engine)

# The router will use the AI engine to make routing decisions
# when rule-based routing doesn't find a match
```
