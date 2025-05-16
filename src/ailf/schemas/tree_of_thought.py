"""Tree of Thought (ToT) schema models.

This module provides Pydantic models for the Tree of Thoughts cognitive pattern,
a structured approach to AI deliberation that enables exploring multiple reasoning
paths through generating, evaluating, and selecting thoughts.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field


class ThoughtState(str, Enum):
    """Possible states of a thought node."""
    
    CREATED = "created"
    EVALUATING = "evaluating"
    PROMISING = "promising"
    REJECTED = "rejected"
    TERMINAL = "terminal"
    

class EvaluationStrategy(str, Enum):
    """Evaluation strategies for thought nodes."""
    
    DFS = "depth_first"
    BFS = "breadth_first"
    BEST_FIRST = "best_first"
    MONTE_CARLO = "monte_carlo"


class ThoughtNode(BaseModel):
    """A node in the tree of thoughts.
    
    Attributes:
        id: Unique identifier for this thought
        content: The actual thought content
        state: Current state of this thought
        parent_id: ID of the parent thought, if any
        depth: Depth in the tree (0 for root)
        score: Evaluation score (higher is better)
        children: IDs of child thoughts
        metadata: Additional data associated with this thought
    """
    
    id: str
    content: str
    state: ThoughtState = ThoughtState.CREATED
    parent_id: Optional[str] = None
    depth: int = 0
    score: Optional[float] = None
    children: List[str] = []
    metadata: Dict[str, Union[str, int, float, bool]] = {}


class ToTConfiguration(BaseModel):
    """Configuration for the Tree of Thoughts processor.
    
    Attributes:
        max_thoughts: Maximum number of thoughts to generate 
        max_depth: Maximum depth of the thought tree
        branching_factor: Maximum number of children per thought
        evaluation_strategy: Method to evaluate and select thoughts
        temperature: Sampling temperature for thought generation
        max_evaluation_samples: Maximum samples for Monte Carlo evaluation
    """
    
    max_thoughts: int = 50
    max_depth: int = 5
    branching_factor: int = 3
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.BEST_FIRST
    temperature: float = 0.7
    max_evaluation_samples: int = 5


class ToTState(BaseModel):
    """Current state of a Tree of Thoughts process.
    
    Attributes:
        thoughts: Map of thought IDs to ThoughtNode objects
        root_id: ID of the root thought
        terminal_thoughts: IDs of thoughts that reached a terminal state
        rejected_thoughts: IDs of thoughts that were rejected
        promising_thoughts: IDs of thoughts that are promising for expansion
        evaluating_thoughts: IDs of thoughts currently being evaluated
    """
    
    thoughts: Dict[str, ThoughtNode] = {}
    root_id: Optional[str] = None
    terminal_thoughts: Set[str] = set()
    rejected_thoughts: Set[str] = set()
    promising_thoughts: Set[str] = set()
    evaluating_thoughts: Set[str] = set()


class ToTResult(BaseModel):
    """Result of a Tree of Thoughts process.
    
    Attributes:
        best_path: Sequence of thoughts forming the best solution path
        state: Final state of the thought tree
        solution: The final solution or conclusion reached
        explanation: Explanation of how the solution was reached
        confidence: Confidence score for the solution (0-1)
    """
    
    best_path: List[ThoughtNode] = []
    state: ToTState
    solution: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = 0.0


__all__ = [
    "ThoughtNode",
    "ThoughtState",
    "ToTConfiguration",
    "ToTState",
    "ToTResult",
    "EvaluationStrategy"
]
