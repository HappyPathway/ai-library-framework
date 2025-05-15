"""Tree of Thoughts (ToT) cognitive processing for AILF agents."""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Tuple, Union, cast

# Placeholder for AIEngine
try:
    from ailf.ai.engine import AIEngine
except ImportError:
    class AIEngine: # type: ignore
        async def analyze(self, content: str, system_prompt: Optional[str] = None):
            print(f"Warning: Using placeholder AIEngine. Analyze called with prompt: {content}")
            return {"content": "This is a placeholder thought"}
        
# Placeholder for BaseProcessor
class BaseProcessor:  # type: ignore
    """Placeholder for BaseProcessor until properly defined."""
    pass

from ailf.schemas.tree_of_thought import (
    ThoughtNode, 
    ToTConfiguration, 
    ToTState, 
    ToTResult, 
    ThoughtState,
    EvaluationStrategy
)
from ailf.schemas.cognition import TaskContext, ProcessingResult
from ailf.cognition.prompt_library import PromptLibrary

class TreeOfThoughtsProcessor(BaseProcessor):
    """Implements the Tree of Thoughts reasoning pattern."""
    
    def __init__(
        self,
        ai_engine: AIEngine,
        prompt_library: Optional[PromptLibrary] = None,
        config: Optional[ToTConfiguration] = None
    ):
        """Initialize the Tree of Thoughts processor.
        
        Args:
            ai_engine: The AI engine for generating and evaluating thoughts
            prompt_library: Optional custom prompt library
            config: Configuration parameters for the ToT process
        """
        self.ai_engine = ai_engine
        self.config = config or ToTConfiguration()
        self.state = None
        self.prompt_library = prompt_library or self._initialize_prompt_library()
    
    def _initialize_prompt_library(self) -> PromptLibrary:
        """Initialize the default prompt templates for ToT operations."""
        library = PromptLibrary()
        
        # Generate thoughts prompt
        library.add_prompt("generate_thoughts", """
        Given the following context and previous thought, generate {branching_factor} different possible next thoughts or reasoning steps.
        
        Problem: {problem}
        
        Previous thought: {previous_thought}
        
        Generate {branching_factor} distinct next thoughts that explore different possible directions:
        1.
        """)
        
        # Evaluate thought prompt
        library.add_prompt("evaluate_thought", """
        Evaluate the quality and potential of the following thought for solving the given problem.
        Rate from 0.0 (not helpful) to 1.0 (extremely promising).
        
        Problem: {problem}
        
        Current thought: {thought}
        
        Evaluation criteria:
        1. Relevance to the problem
        2. Potential to lead to a solution
        3. Logical coherence
        4. Originality/Creativity
        5. Feasibility
        
        First provide your reasoning, then conclude with a numeric score between 0.0 and 1.0.
        """)
        
        # Summarize solution prompt
        library.add_prompt("summarize_solution", """
        Given the following reasoning path that was explored, provide a concise summary
        of the key insights and conclusion.
        
        Problem: {problem}
        
        Reasoning path:
        {reasoning_path}
        
        Summary of key insights and conclusion:
        """)
        
        return library
    
    async def initialize_tree(self, problem: str) -> str:
        """Initialize the thought tree with a root node.
        
        Args:
            problem: The problem statement
            
        Returns:
            Root node ID
        """
        # Generate initial thought
        initial_thought_prompt = f"Given this problem: {problem}\n\nWhat's an initial thought or approach to solve it?"
        
        response = await self.ai_engine.analyze(
            content=initial_thought_prompt,
            system_prompt="You are helping solve a complex problem. Provide a thoughtful starting point."
        )
        
        initial_thought = response.get("content", "Let me think about how to approach this problem.")
        
        # Create root node
        root_id = str(uuid.uuid4())
        root_node = ThoughtNode(
            id=root_id,
            parent_id=None,
            content=initial_thought,
            depth=0,
            state=ThoughtState.ACTIVE
        )
        
        # Initialize state
        self.state = ToTState(
            problem=problem,
            thought_nodes={root_id: root_node},
            active_node_ids=[root_id],
            root_node_id=root_id
        )
        
        return root_id
    
    async def expand_node(self, node_id: str) -> List[str]:
        """Expand a node by generating child thoughts.
        
        Args:
            node_id: ID of the node to expand
            
        Returns:
            List of new child node IDs
        """
        if not self.state:
            raise ValueError("Tree not initialized. Call initialize_tree first.")
            
        parent_node = self.state.thought_nodes.get(node_id)
        if not parent_node:
            raise ValueError(f"Node {node_id} not found in the thought tree.")
        
        # Get generation prompt
        prompt = self.prompt_library.format_prompt(
            "generate_thoughts", 
            {
                "problem": self.state.problem,
                "previous_thought": parent_node.content,
                "branching_factor": self.config.branching_factor
            }
        )
        
        # Generate child thoughts
        response = await self.ai_engine.analyze(
            content=prompt,
            system_prompt="Generate diverse and creative next steps in the reasoning process."
        )
        
        # Process and extract thoughts from the response
        thoughts = self._extract_thoughts_from_response(response)
        
        # Create child nodes
        child_ids = []
        for thought in thoughts:
            child_id = str(uuid.uuid4())
            child_node = ThoughtNode(
                id=child_id,
                parent_id=node_id,
                content=thought,
                depth=parent_node.depth + 1,
                state=ThoughtState.PENDING
            )
            
            # Update state
            self.state.thought_nodes[child_id] = child_node
            child_ids.append(child_id)
            
            # Update max depth if needed
            if child_node.depth > self.state.max_depth_reached:
                self.state.max_depth_reached = child_node.depth
        
        # Mark parent as complete
        parent_node.state = ThoughtState.COMPLETED
        if node_id in self.state.active_node_ids:
            self.state.active_node_ids.remove(node_id)
        self.state.completed_node_ids.append(node_id)
        
        return child_ids
    
    def _extract_thoughts_from_response(self, response: Dict[str, Any]) -> List[str]:
        """Extract individual thoughts from an AI response.
        
        Args:
            response: AI response containing generated thoughts
            
        Returns:
            List of extracted thoughts
        """
        content = response.get("content", "")
        
        # Simple extraction by number prefixes like "1." or "1)"
        thoughts = []
        current_thought = ""
        
        lines = content.split("\n")
        for line in lines:
            # Try to detect numbered items
            stripped = line.strip()
            if (stripped and 
                (stripped[0].isdigit() and len(stripped) > 1 and 
                 (stripped[1] == '.' or stripped[1] == ')'))):
                if current_thought:
                    thoughts.append(current_thought.strip())
                current_thought = stripped[2:].strip()
            else:
                if current_thought:
                    current_thought += " " + stripped
        
        # Add the last thought
        if current_thought:
            thoughts.append(current_thought.strip())
        
        # If we couldn't extract numbered thoughts, try another approach
        if not thoughts:
            # Just split by double newlines as a fallback
            thoughts = [t.strip() for t in content.split("\n\n") if t.strip()]
        
        # Ensure we have the right number of thoughts or at least one
        while len(thoughts) > self.config.branching_factor:
            thoughts.pop()
            
        if not thoughts:
            thoughts = ["I need to explore this direction further."]
            
        return thoughts
    
    async def evaluate_node(self, node_id: str) -> float:
        """Evaluate a thought node.
        
        Args:
            node_id: The ID of the node to evaluate
            
        Returns:
            Evaluation score between 0.0 and 1.0
        """
        if not self.state:
            raise ValueError("Tree not initialized. Call initialize_tree first.")
            
        node = self.state.thought_nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found in the thought tree.")
        
        # Get evaluation prompt
        prompt = self.prompt_library.format_prompt(
            "evaluate_thought", 
            {
                "problem": self.state.problem,
                "thought": node.content
            }
        )
        
        # Evaluate thought
        response = await self.ai_engine.analyze(
            content=prompt,
            system_prompt="You are evaluating the quality of a reasoning step. Be objective and analytical."
        )
        
        # Extract score from response
        score = self._extract_score_from_response(response)
        
        # Update node with score
        node.evaluation_score = score
        
        return score
    
    def _extract_score_from_response(self, response: Dict[str, Any]) -> float:
        """Extract a numerical score from an evaluation response.
        
        Args:
            response: AI response containing evaluation
            
        Returns:
            Extracted score between 0.0 and 1.0
        """
        content = response.get("content", "")
        
        # Look for patterns like "Score: 0.8" or "Rating: 0.8" or just a number
        import re
        
        # Try to find score patterns
        score_patterns = [
            r"(?:score|rating|evaluation):\s*(\d+(?:\.\d+)?)",  # Score: 0.8
            r"(\d+(?:\.\d+)?)\s*\/\s*1\.?0?",  # 0.8/1 or 0.8/1.0
            r"(\d+(?:\.\d+)?)\s*$"  # Just a number at the end
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                try:
                    score = float(matches[-1])  # Take the last match
                    # Normalize to 0.0-1.0 range
                    return min(max(score, 0.0), 1.0)
                except ValueError:
                    continue
        
        # Default score if no pattern matches
        return 0.5
    
    async def select_best_nodes(self, num_nodes: Optional[int] = None) -> List[str]:
        """Select the best nodes to explore based on beam search.
        
        Args:
            num_nodes: Number of nodes to select (defaults to beam_width)
            
        Returns:
            List of node IDs to explore next
        """
        if not self.state:
            raise ValueError("Tree not initialized. Call initialize_tree first.")
            
        if not num_nodes:
            num_nodes = self.config.beam_width
            
        # Get all pending nodes
        pending_nodes = [
            node for node_id, node in self.state.thought_nodes.items()
            if node.state == ThoughtState.PENDING
        ]
        
        # If no pending nodes, return empty list
        if not pending_nodes:
            return []
            
        # For nodes without scores, evaluate them
        nodes_to_evaluate = [node for node in pending_nodes if node.evaluation_score is None]
        
        # Evaluate nodes in parallel
        if nodes_to_evaluate:
            evaluation_tasks = [
                self.evaluate_node(node.id) for node in nodes_to_evaluate
            ]
            await asyncio.gather(*evaluation_tasks)
        
        # Re-get all pending nodes with scores
        pending_nodes = [
            node for node_id, node in self.state.thought_nodes.items()
            if node.state == ThoughtState.PENDING
        ]
        
        # Sort by score and select best ones
        pending_nodes.sort(key=lambda n: n.evaluation_score or 0.0, reverse=True)
        selected_nodes = pending_nodes[:num_nodes]
        
        # Update states
        for node in selected_nodes:
            node.state = ThoughtState.ACTIVE
            self.state.active_node_ids.append(node.id)
            
        return [node.id for node in selected_nodes]
    
    def _extract_path(self, leaf_node_id: str) -> List[ThoughtNode]:
        """Extract the full path from root to a given leaf node.
        
        Args:
            leaf_node_id: ID of the leaf node
            
        Returns:
            List of nodes from root to leaf
        """
        if not self.state:
            raise ValueError("Tree not initialized. Call initialize_tree first.")
            
        path = []
        current_id = leaf_node_id
        
        while current_id:
            node = self.state.thought_nodes.get(current_id)
            if not node:
                break
                
            path.append(node)
            current_id = node.parent_id
            
        # Reverse to get root-to-leaf order
        path.reverse()
        return path
    
    async def _generate_solution_summary(self, best_path: List[ThoughtNode]) -> str:
        """Generate a summary solution based on the best path.
        
        Args:
            best_path: List of nodes in the best path
            
        Returns:
            Summary solution
        """
        if not self.state:
            raise ValueError("Tree not initialized. Call initialize_tree first.")
            
        # Format the reasoning path
        reasoning_path_text = "\n".join(
            [f"{i+1}. {node.content}" for i, node in enumerate(best_path)]
        )
        
        # Generate summary
        prompt = self.prompt_library.format_prompt(
            "summarize_solution", 
            {
                "problem": self.state.problem,
                "reasoning_path": reasoning_path_text
            }
        )
        
        response = await self.ai_engine.analyze(
            content=prompt,
            system_prompt="Synthesize the reasoning path into a concise and clear solution."
        )
        
        return response.get("content", "No solution found.")
    
    def _find_best_leaf_node(self) -> Optional[str]:
        """Find the best leaf node based on evaluation scores.
        
        Returns:
            ID of the best leaf node or None if no leaves
        """
        if not self.state:
            return None
            
        # Find all leaf nodes (nodes that are in completed_node_ids but have no children)
        leaf_nodes = []
        
        for node_id in self.state.completed_node_ids:
            # Check if this node has any children
            has_children = False
            for potential_child in self.state.thought_nodes.values():
                if potential_child.parent_id == node_id:
                    has_children = True
                    break
                    
            if not has_children:
                leaf_nodes.append(self.state.thought_nodes[node_id])
        
        # If no leaf nodes, use the root
        if not leaf_nodes and self.state.root_node_id:
            return self.state.root_node_id
            
        # Find the leaf with the highest score
        if leaf_nodes:
            best_leaf = max(leaf_nodes, key=lambda n: n.evaluation_score or 0.0)
            return best_leaf.id
            
        return None
    
    async def process(self, context: TaskContext) -> ProcessingResult:
        """Process a task using Tree of Thoughts reasoning.
        
        Args:
            context: Task context containing user input and other information
            
        Returns:
            Processing result with solution and confidence
        """
        problem = context.user_input
        
        # Initialize tree
        await self.initialize_tree(problem)
        
        # Iterative deepening
        for depth in range(self.config.max_depth):
            # Select nodes to expand at current depth
            nodes_to_expand = await self.select_best_nodes()
            
            # If no nodes to expand, we're done
            if not nodes_to_expand:
                break
                
            # Expand selected nodes in parallel
            expand_tasks = [self.expand_node(node_id) for node_id in nodes_to_expand]
            await asyncio.gather(*expand_tasks)
        
        # Find the best leaf node
        best_leaf_id = self._find_best_leaf_node()
        if not best_leaf_id:
            return ProcessingResult(
                output="Could not find a solution path.",
                reasoning="No valid reasoning paths were found.",
                confidence=0.0
            )
            
        # Extract the best path
        best_path = self._extract_path(best_leaf_id)
        
        # Generate solution summary
        solution = await self._generate_solution_summary(best_path)
        
        # Calculate confidence
        confidence = self._calculate_confidence(best_path)
        
        # Create result
        result = ProcessingResult(
            output=solution,
            reasoning="\n".join([f"{i+1}. {node.content}" for i, node in enumerate(best_path)]),
            confidence=confidence,
            metadata={
                "explored_nodes": len(self.state.thought_nodes) if self.state else 0,
                "max_depth_reached": self.state.max_depth_reached if self.state else 0,
                "reasoning_tree": {node_id: node.dict() for node_id, node in self.state.thought_nodes.items()} if self.state else {}
            }
        )
        
        return result
    
    def _calculate_confidence(self, path: List[ThoughtNode]) -> float:
        """Calculate overall confidence based on the reasoning path.
        
        Args:
            path: List of nodes in the reasoning path
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not path:
            return 0.0
            
        # Average evaluation scores along the path
        scores = [node.evaluation_score or 0.0 for node in path]
        return sum(scores) / len(scores)
