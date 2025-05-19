"""Tests for the Tree of Thoughts processor."""
import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid

from ailf.cognition.tree_of_thoughts import TreeOfThoughtsProcessor
from ailf.schemas.tree_of_thought import (
    ThoughtNode, 
    ToTConfiguration, 
    ThoughtState,
    EvaluationStrategy
)
from ailf.schemas.cognition import TaskContext, ProcessingResult
from ailf.cognition.prompt_library import PromptLibrary

class MockAIEngine:
    """Mock AIEngine for testing."""
    
    async def analyze(self, content=None, system_prompt=None, **kwargs):
        """Mock analyze method."""
        if "generate" in content.lower():
            # For thought generation
            return {
                "content": "1. First thought\n2. Second thought\n3. Third thought"
            }
        elif "evaluate" in content.lower():
            # For thought evaluation
            return {
                "content": "This thought is promising. Score: 0.75"
            }
        elif "initial" in system_prompt.lower():
            # For initial thought
            return {
                "content": "Initial approach to the problem"
            }
        elif "summarize" in content.lower() or "synthesize" in system_prompt.lower():
            # For solution summary
            return {
                "content": "The solution is to do X, then Y, and finally Z."
            }
        else:
            # Default response
            return {
                "content": "Generic response"
            }

@pytest.fixture
def mock_ai_engine():
    """Fixture for mock AI engine."""
    return MockAIEngine()

@pytest.fixture
def tot_processor(mock_ai_engine):
    """Fixture for ToT processor."""
    config = ToTConfiguration(
        max_depth=2,
        branching_factor=2,
        beam_width=2
    )
    return TreeOfThoughtsProcessor(mock_ai_engine, config=config)

@pytest.fixture
def task_context():
    """Fixture for task context."""
    return TaskContext(
        user_input="Solve this complex problem: design a space elevator",
        conversation_history=[],
        task_type="problem_solving"
    )

@pytest.mark.asyncio
async def test_initialize_tree(tot_processor):
    """Test initializing the thought tree."""
    root_id = await tot_processor.initialize_tree("Test problem")
    
    assert root_id is not None
    assert tot_processor.state is not None
    assert tot_processor.state.problem == "Test problem"
    assert root_id in tot_processor.state.thought_nodes
    assert tot_processor.state.thought_nodes[root_id].content == "Initial approach to the problem"
    assert tot_processor.state.root_node_id == root_id
    assert tot_processor.state.active_node_ids == [root_id]

@pytest.mark.asyncio
async def test_expand_node(tot_processor):
    """Test expanding a node in the tree."""
    # Initialize tree first
    root_id = await tot_processor.initialize_tree("Test problem")
    
    # Expand the root node
    child_ids = await tot_processor.expand_node(root_id)
    
    # Check results
    assert len(child_ids) == 3  # Should have 3 child thoughts
    
    # Check that children were added to state
    for child_id in child_ids:
        assert child_id in tot_processor.state.thought_nodes
        assert tot_processor.state.thought_nodes[child_id].parent_id == root_id
        assert tot_processor.state.thought_nodes[child_id].depth == 1
    
    # Check that parent node was updated
    assert tot_processor.state.thought_nodes[root_id].state == ThoughtState.COMPLETED
    assert root_id not in tot_processor.state.active_node_ids
    assert root_id in tot_processor.state.completed_node_ids

@pytest.mark.asyncio
async def test_evaluate_node(tot_processor):
    """Test evaluating a thought node."""
    # Initialize tree and create a node
    await tot_processor.initialize_tree("Test problem")
    
    # Create a test node
    node_id = str(uuid.uuid4())
    test_node = ThoughtNode(
        id=node_id,
        content="Test thought to evaluate"
    )
    tot_processor.state.thought_nodes[node_id] = test_node
    
    # Evaluate the node
    score = await tot_processor.evaluate_node(node_id)
    
    # Check results
    assert score == 0.75
    assert tot_processor.state.thought_nodes[node_id].evaluation_score == 0.75

@pytest.mark.asyncio
async def test_select_best_nodes(tot_processor):
    """Test selecting the best nodes to expand."""
    # Initialize tree
    await tot_processor.initialize_tree("Test problem")
    
    # Create several nodes with different scores
    nodes = [
        (str(uuid.uuid4()), 0.9),
        (str(uuid.uuid4()), 0.7),
        (str(uuid.uuid4()), 0.5),
        (str(uuid.uuid4()), 0.3)
    ]
    
    for node_id, score in nodes:
        tot_processor.state.thought_nodes[node_id] = ThoughtNode(
            id=node_id,
            content=f"Test thought with score {score}",
            state=ThoughtState.PENDING,
            evaluation_score=score
        )
    
    # Select best nodes (should select top 2 due to beam_width=2)
    best_nodes = await tot_processor.select_best_nodes()
    
    # Check results
    assert len(best_nodes) == 2
    assert nodes[0][0] in best_nodes  # Best node with score 0.9
    assert nodes[1][0] in best_nodes  # Second best node with score 0.7
    
    # Check that selected nodes were updated to ACTIVE
    for node_id in best_nodes:
        assert tot_processor.state.thought_nodes[node_id].state == ThoughtState.ACTIVE
        assert node_id in tot_processor.state.active_node_ids

@pytest.mark.asyncio
async def test_extract_path(tot_processor):
    """Test extracting a path from root to leaf."""
    # Create a simple tree:
    # root -> mid -> leaf
    root_id = str(uuid.uuid4())
    mid_id = str(uuid.uuid4())
    leaf_id = str(uuid.uuid4())
    
    # Initialize state with test nodes
    tot_processor.state = ToTState(
        problem="Test problem",
        thought_nodes={
            root_id: ThoughtNode(id=root_id, content="Root thought"),
            mid_id: ThoughtNode(id=mid_id, parent_id=root_id, content="Mid thought", depth=1),
            leaf_id: ThoughtNode(id=leaf_id, parent_id=mid_id, content="Leaf thought", depth=2)
        },
        root_node_id=root_id,
        active_node_ids=[]
    )
    
    # Extract path from leaf to root
    path = tot_processor._extract_path(leaf_id)
    
    # Check results
    assert len(path) == 3
    assert path[0].id == root_id
    assert path[1].id == mid_id
    assert path[2].id == leaf_id

@pytest.mark.asyncio
async def test_process_full_flow(tot_processor, task_context):
    """Test the full processing flow."""
    result = await tot_processor.process(task_context)
    
    # Check result structure
    assert isinstance(result, ProcessingResult)
    assert result.output == "The solution is to do X, then Y, and finally Z."
    assert result.confidence > 0
    assert "explored_nodes" in result.metadata
    assert "max_depth_reached" in result.metadata
    assert "reasoning_tree" in result.metadata

@pytest.mark.asyncio
async def test_extract_thoughts_from_response():
    """Test extracting thoughts from an AI response."""
    processor = TreeOfThoughtsProcessor(MockAIEngine())
    
    # Test with numbered list
    response1 = {"content": "1. First thought\n2. Second thought\n3. Third thought"}
    thoughts1 = processor._extract_thoughts_from_response(response1)
    assert len(thoughts1) == 3
    assert thoughts1[0] == "First thought"
    assert thoughts1[1] == "Second thought"
    assert thoughts1[2] == "Third thought"
    
    # Test with multi-line thoughts
    response2 = {"content": "1. First thought\n   with additional detail\n2. Second thought\n   spanning lines"}
    thoughts2 = processor._extract_thoughts_from_response(response2)
    assert len(thoughts2) == 2
    assert "with additional detail" in thoughts2[0]
    assert "spanning lines" in thoughts2[1]
    
    # Test with empty response
    response3 = {"content": ""}
    thoughts3 = processor._extract_thoughts_from_response(response3)
    assert len(thoughts3) == 1
    assert thoughts3[0] == "I need to explore this direction further."

@pytest.mark.asyncio
async def test_extract_score_from_response():
    """Test extracting scores from evaluation responses."""
    processor = TreeOfThoughtsProcessor(MockAIEngine())
    
    # Test various score formats
    responses = [
        {"content": "This is a good thought. Score: 0.75"},
        {"content": "Rating: 0.8"},
        {"content": "Evaluation result: 0.9/1"},
        {"content": "After careful consideration, I give this a 0.65"},
        {"content": "This thought scores 7/10"}, # Should be normalized to 0.7
        {"content": "No clear score"}  # Should default to 0.5
    ]
    
    expected_scores = [0.75, 0.8, 0.9, 0.65, 0.7, 0.5]
    
    for response, expected in zip(responses, expected_scores):
        score = processor._extract_score_from_response(response)
        assert score == expected
