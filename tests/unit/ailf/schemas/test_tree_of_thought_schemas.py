"""Tests for the Tree of Thoughts schemas."""
import pytest
from pydantic import ValidationError

from ailf.schemas.tree_of_thought import (
    ThoughtNode, 
    ToTConfiguration, 
    ToTState, 
    ToTResult, 
    ThoughtState,
    EvaluationStrategy
)

def test_thought_node_creation():
    """Test the creation of a ThoughtNode."""
    node = ThoughtNode(
        id="test-id",
        content="This is a test thought"
    )
    
    assert node.id == "test-id"
    assert node.content == "This is a test thought"
    assert node.depth == 0
    assert node.state == ThoughtState.PENDING
    assert node.parent_id is None
    assert node.evaluation_score is None
    assert node.metadata == {}

def test_thought_node_validation():
    """Test validation of ThoughtNode fields."""
    # Missing required fields
    with pytest.raises(ValidationError):
        ThoughtNode()
    
    with pytest.raises(ValidationError):
        ThoughtNode(id="test-id")
    
    with pytest.raises(ValidationError):
        ThoughtNode(content="This is a test thought")
    
    # Valid node with all required fields
    node = ThoughtNode(id="test-id", content="This is a test thought")
    assert node.id == "test-id"
    assert node.content == "This is a test thought"

def test_thought_node_with_all_fields():
    """Test ThoughtNode with all fields specified."""
    node = ThoughtNode(
        id="test-id",
        parent_id="parent-id",
        content="This is a test thought",
        depth=2,
        state=ThoughtState.ACTIVE,
        evaluation_score=0.75,
        metadata={"source": "user", "timestamp": 1234567890}
    )
    
    assert node.id == "test-id"
    assert node.parent_id == "parent-id"
    assert node.content == "This is a test thought"
    assert node.depth == 2
    assert node.state == ThoughtState.ACTIVE
    assert node.evaluation_score == 0.75
    assert node.metadata == {"source": "user", "timestamp": 1234567890}

def test_tot_configuration_defaults():
    """Test the default values for ToTConfiguration."""
    config = ToTConfiguration()
    
    assert config.max_depth == 3
    assert config.branching_factor == 3
    assert config.beam_width == 5
    assert config.temperature == 0.7
    assert config.evaluation_strategy == EvaluationStrategy.VALUE_BASED
    assert config.custom_evaluation_prompt is None

def test_tot_configuration_custom():
    """Test ToTConfiguration with custom values."""
    config = ToTConfiguration(
        max_depth=5,
        branching_factor=2,
        beam_width=3,
        temperature=0.5,
        evaluation_strategy=EvaluationStrategy.OBJECTIVE_BASED,
        custom_evaluation_prompt="Custom evaluation prompt"
    )
    
    assert config.max_depth == 5
    assert config.branching_factor == 2
    assert config.beam_width == 3
    assert config.temperature == 0.5
    assert config.evaluation_strategy == EvaluationStrategy.OBJECTIVE_BASED
    assert config.custom_evaluation_prompt == "Custom evaluation prompt"

def test_tot_state():
    """Test ToTState creation and validation."""
    # Create a node
    node = ThoughtNode(id="node1", content="Initial thought")
    
    # Create state
    state = ToTState(
        problem="Solve this problem",
        thought_nodes={"node1": node},
        active_node_ids=["node1"],
        root_node_id="node1"
    )
    
    assert state.problem == "Solve this problem"
    assert "node1" in state.thought_nodes
    assert state.thought_nodes["node1"].id == "node1"
    assert state.active_node_ids == ["node1"]
    assert state.root_node_id == "node1"
    assert state.max_depth_reached == 0

def test_tot_result():
    """Test ToTResult creation and validation."""
    # Create sample nodes for a reasoning path
    node1 = ThoughtNode(id="node1", content="Initial thought")
    node2 = ThoughtNode(id="node2", parent_id="node1", content="Follow-up thought", depth=1)
    node3 = ThoughtNode(id="node3", parent_id="node2", content="Conclusion", depth=2)
    
    # Create result
    result = ToTResult(
        solution="The solution is X",
        reasoning_path=[node1, node2, node3],
        confidence=0.85,
        explored_nodes=10
    )
    
    assert result.solution == "The solution is X"
    assert len(result.reasoning_path) == 3
    assert result.reasoning_path[0].id == "node1"
    assert result.reasoning_path[2].content == "Conclusion"
    assert result.confidence == 0.85
    assert result.explored_nodes == 10
    assert result.metadata == {}
