"""Pydantic schemas for Tree of Thoughts reasoning pattern."""

from typing import List, Optional, Dict, Any, TypeVar
from enum import Enum
from pydantic import BaseModel, Field

class ThoughtState(str, Enum):
    """Possible states of a thought node in the reasoning tree."""
    ACTIVE = "active"           # Currently being explored
    COMPLETED = "completed"     # Exploration completed
    ABANDONED = "abandoned"     # Abandoned due to low evaluation
    PENDING = "pending"         # Queued for exploration

class EvaluationStrategy(str, Enum):
    """Possible evaluation strategies for thought nodes."""
    VALUE_BASED = "value_based"         # Evaluate based on expected value/utility
    OBJECTIVE_BASED = "objective_based"  # Evaluate against objective criteria
    SIMULATION_BASED = "simulation_based"  # Evaluate by simulating outcomes

class ThoughtNode(BaseModel):
    """Represents a single thought in the reasoning tree."""
    id: str = Field(..., description="Unique identifier for the thought")
    parent_id: Optional[str] = Field(None, description="Parent thought ID (None for root)")
    content: str = Field(..., description="The actual thought content")
    depth: int = Field(0, description="Depth level in the tree")
    state: ThoughtState = Field(ThoughtState.PENDING, description="Current state of the thought")
    evaluation_score: Optional[float] = Field(None, description="Quality score (0.0-1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ToTConfiguration(BaseModel):
    """Configuration for Tree of Thoughts processing."""
    max_depth: int = Field(3, description="Maximum depth of the thought tree")
    branching_factor: int = Field(3, description="Number of branches to explore per node")
    beam_width: int = Field(5, description="Number of active paths to maintain")
    temperature: float = Field(0.7, description="Temperature for thought generation")
    evaluation_strategy: EvaluationStrategy = Field(
        EvaluationStrategy.VALUE_BASED,
        description="Strategy for evaluating thoughts"
    )
    custom_evaluation_prompt: Optional[str] = Field(
        None, 
        description="Custom prompt template for evaluation"
    )

class ToTState(BaseModel):
    """Represents the current state of a Tree of Thoughts reasoning process."""
    problem: str = Field(..., description="The problem being solved")
    thought_nodes: Dict[str, ThoughtNode] = Field(default_factory=dict, description="All nodes in the thought tree")
    active_node_ids: List[str] = Field(default_factory=list, description="Currently active nodes")
    completed_node_ids: List[str] = Field(default_factory=list, description="Completed exploration paths")
    root_node_id: Optional[str] = Field(None, description="Root node of the thought tree")
    max_depth_reached: int = Field(0, description="Maximum depth reached so far")
    
class ToTResult(BaseModel):
    """Result of a Tree of Thoughts reasoning process."""
    solution: str = Field(..., description="The final solution derived from the thought process")
    reasoning_path: List[ThoughtNode] = Field(..., description="Path of thoughts leading to the solution")
    confidence: float = Field(..., description="Confidence in the solution (0.0-1.0)")
    explored_nodes: int = Field(..., description="Total number of thought nodes explored")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional result metadata")
