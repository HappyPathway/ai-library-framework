"""Integration tests for Tree of Thoughts processor."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

from ailf.cognition.tree_of_thoughts import TreeOfThoughtsProcessor
from ailf.schemas.tree_of_thought import ToTConfiguration
from ailf.schemas.cognition import TaskContext
from ailf.memory.in_memory import InMemoryShortTermMemory

class MockAIEngine:
    """Mock AIEngine for testing."""
    
    async def analyze(self, content=None, system_prompt=None, **kwargs):
        """Mock analyze method."""
        if "generate" in content.lower():
            return {
                "content": "1. First thought\n2. Second thought\n3. Third thought"
            }
        elif "evaluate" in content.lower():
            return {
                "content": "This thought is promising. Score: 0.75"
            }
        elif "summarize" in content.lower() or "synthesize" in system_prompt.lower():
            return {
                "content": "The solution is to implement X using approach Y."
            }
        else:
            return {
                "content": "Initial approach to the problem"
            }

@pytest.fixture
def mock_ai_engine():
    """Fixture for mock AI engine."""
    return MockAIEngine()

@pytest.fixture
def memory():
    """Fixture for memory system."""
    return InMemoryShortTermMemory()

@pytest.fixture
def tot_processor(mock_ai_engine):
    """Fixture for ToT processor."""
    config = ToTConfiguration(
        max_depth=2,
        branching_factor=2,
        beam_width=2
    )
    return TreeOfThoughtsProcessor(mock_ai_engine, config=config)

@pytest.mark.asyncio
async def test_tot_with_memory_integration(tot_processor, memory):
    """Test ToT processor integration with memory system."""
    # Store problem in memory
    problem = "Design an algorithm to efficiently sort a large distributed dataset."
    await memory.add("current_problem", problem)
    
    # Create task context with memory reference
    context = TaskContext(
        user_input=problem,
        conversation_history=[],
        task_type="problem_solving",
        metadata={"memory": memory}
    )
    
    # Process with ToT
    result = await tot_processor.process(context)
    
    # Verify result
    assert result is not None
    assert result.output is not None
    assert result.confidence > 0
    
    # Store result in memory
    await memory.add("tot_result", result.output)
    await memory.add("tot_confidence", result.confidence)
    await memory.add("tot_reasoning", result.reasoning)
    
    # Verify memory contains result
    stored_result = await memory.get("tot_result")
    stored_confidence = await memory.get("tot_confidence")
    stored_reasoning = await memory.get("tot_reasoning")
    
    assert stored_result == result.output
    assert stored_confidence == result.confidence
    assert stored_reasoning == result.reasoning

@pytest.mark.asyncio
async def test_tot_with_context_history(tot_processor):
    """Test ToT processor with conversation history in context."""
    # Create conversation history
    conversation_history = [
        {"role": "user", "content": "I need to solve a complex optimization problem."},
        {"role": "assistant", "content": "I'd be happy to help with that. What's the specific problem?"},
        {"role": "user", "content": "How do I optimize resource allocation across multiple data centers?"}
    ]
    
    # Create task context with conversation history
    context = TaskContext(
        user_input="Design an algorithm for efficient resource allocation across global data centers",
        conversation_history=conversation_history,
        task_type="problem_solving"
    )
    
    # Process with ToT
    result = await tot_processor.process(context)
    
    # Verify result
    assert result is not None
    assert result.output is not None
    assert result.confidence > 0
    assert "reasoning_tree" in result.metadata

@pytest.mark.asyncio
async def test_multi_round_tot_processing(tot_processor):
    """Test multiple rounds of ToT processing for iterative problem solving."""
    # Initial round
    context1 = TaskContext(
        user_input="Design a high-level architecture for a distributed database",
        conversation_history=[],
        task_type="design"
    )
    
    result1 = await tot_processor.process(context1)
    
    # Second round - refine based on first result
    context2 = TaskContext(
        user_input="Refine the storage layer of the database design",
        conversation_history=[
            {"role": "user", "content": "Design a high-level architecture for a distributed database"},
            {"role": "assistant", "content": result1.output}
        ],
        task_type="design",
        metadata={"previous_result": result1.metadata}
    )
    
    result2 = await tot_processor.process(context2)
    
    # Verify results
    assert result1 is not None
    assert result2 is not None
    assert result1.confidence > 0
    assert result2.confidence > 0
    # Second result should reference the first result's concepts
    assert result2.reasoning is not None
