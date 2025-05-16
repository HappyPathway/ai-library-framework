"""Advanced example of Tree of Thoughts for complex problem-solving."""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional

try:
    from ailf.cognition.tree_of_thoughts import TreeOfThoughtsProcessor
    from ailf.schemas.tree_of_thought import ToTConfiguration, EvaluationStrategy
    from ailf.schemas.cognition import TaskContext, ProcessingResult
    from ailf.memory.in_memory import InMemoryShortTermMemory
    from ailf.cognition.prompt_library import PromptLibrary
except ImportError:
    print("AILF package not found. This example requires the AILF framework.")
    exit(1)

# For demo purposes, create a mock AIEngine if real one isn't available
try:
    from utils.ai.engine import AIEngine
except ImportError:
    class AIEngine:
        """Mock AIEngine for demonstration purposes."""
        
        def __init__(self, model_name="mock-model"):
            self.model_name = model_name
            
        async def analyze(self, content: str, system_prompt: Optional[str] = None, **kwargs):
            """Mock analyze method with simulated responses for the example."""
            print(f"\nAI Engine Call ({self.model_name}):")
            print(f"System: {system_prompt[:50]}..." if system_prompt else "No system prompt")
            print(f"Content: {content[:100]}...\n")
            
            # Simulate different responses based on content
            if "generate" in content.lower() and "thought" in content.lower():
                return {
                    "content": """
                    1. We could approach this by defining a set of orthogonal basis vectors in the new coordinate system.
                    2. Another approach is to use a transformation matrix that relates the original coordinates to the new system.
                    3. We could use quaternions to represent the rotation needed for the coordinate transformation.
                    """
                }
            elif "evaluate" in content.lower():
                if "quaternion" in content.lower():
                    return {
                        "content": "Quaternions provide a compact and numerically stable way to represent rotations. They avoid gimbal lock issues encountered with Euler angles. Score: 0.95"
                    }
                elif "transformation matrix" in content.lower():
                    return {
                        "content": "Transformation matrices are straightforward to understand and implement, but may have numerical precision issues. Score: 0.75"
                    }
                else:
                    return {
                        "content": "This is a valid approach but may be less efficient than alternatives. Score: 0.60"
                    }
            elif "summarize" in content.lower() or "solution" in system_prompt.lower():
                return {
                    "content": """
                    To convert coordinates between Cartesian and cylindrical systems:
                    
                    1. For Cartesian to cylindrical conversion:
                       - r = √(x² + y²)
                       - θ = atan2(y, x)
                       - z remains the same
                    
                    2. For cylindrical to Cartesian conversion:
                       - x = r*cos(θ)
                       - y = r*sin(θ)
                       - z remains the same
                    
                    This approach uses quaternions to handle the rotational component efficiently,
                    avoiding gimbal lock and maintaining numerical stability.
                    """
                }
            else:  # Initial thought
                return {
                    "content": "To derive the coordinate transformation between Cartesian and cylindrical coordinates, I need to understand the mathematical relationships between these two systems."
                }

class CoordinateSystemProblem:
    """Example class demonstrating a complex problem solved with Tree of Thoughts."""
    
    def __init__(self):
        self.ai_engine = AIEngine(model_name="gpt-4-mock")
        self.memory = InMemoryShortTermMemory()
        self.prompt_library = self._setup_custom_prompts()
        
    def _setup_custom_prompts(self) -> PromptLibrary:
        """Set up custom prompts for this specific problem domain."""
        library = PromptLibrary()
        
        # Custom thought generation prompt
        library.add_prompt("generate_thoughts", """
        Given the following mathematical problem about coordinate transformations and previous thought,
        generate {branching_factor} different possible approaches or reasoning steps.
        
        Problem: {problem}
        
        Previous thought: {previous_thought}
        
        Generate {branching_factor} distinct next steps in the reasoning process:
        1.
        """)
        
        # Custom thought evaluation prompt
        library.add_prompt("evaluate_thought", """
        Evaluate the quality and mathematical correctness of the following approach to the coordinate transformation problem.
        Rate from 0.0 (incorrect or unhelpful) to 1.0 (mathematically elegant and correct).
        
        Problem: {problem}
        
        Approach to evaluate: {thought}
        
        Consider:
        1. Mathematical correctness
        2. Elegance and simplicity
        3. Computational efficiency
        4. Edge case handling
        
        Provide your reasoning and then a score from 0.0 to 1.0.
        """)
        
        return library
    
    async def solve_coordinate_transformation(self):
        """Solve a coordinate transformation problem using Tree of Thoughts."""
        problem = """
        Derive the coordinate transformation equations between the Cartesian coordinate system (x, y, z) 
        and the cylindrical coordinate system (r, θ, z). Then implement a Python function to convert 
        coordinates from one system to the other. Analyze the edge cases and potential numerical issues 
        that might arise in the implementation.
        """
        
        # Store problem in memory
        await self.memory.add("coordinate_problem", problem)
        
        # Configure Tree of Thoughts
        config = ToTConfiguration(
            max_depth=4,            # Maximum depth of the thought tree
            branching_factor=3,     # Generate 3 thoughts per node
            beam_width=2,           # Explore the 2 most promising paths
            temperature=0.3,        # Lower temperature for a more deterministic approach
            evaluation_strategy=EvaluationStrategy.OBJECTIVE_BASED
        )
        
        # Create ToT processor with custom prompts
        tot_processor = TreeOfThoughtsProcessor(
            ai_engine=self.ai_engine,
            prompt_library=self.prompt_library,
            config=config
        )
        
        # Create task context
        context = TaskContext(
            user_input=problem,
            conversation_history=[],
            task_type="mathematical_derivation",
            metadata={"memory": self.memory}
        )
        
        # Process with ToT
        print(f"🌳 Solving coordinate transformation problem with Tree of Thoughts...\n")
        print(f"Problem: {problem}\n")
        
        result = await tot_processor.process(context)
        
        # Store result in memory
        await self.memory.add("coordinate_solution", result.output)
        await self.memory.add("solution_confidence", result.confidence)
        
        # Display results
        print("\n" + "="*80)
        print(f"🌟 Solution (confidence: {result.confidence:.2f}):\n")
        print(result.output)
        print("\n📝 Reasoning path:")
        print(result.reasoning)
        print("\n📊 Stats:")
        print(f"- Explored nodes: {result.metadata.get('explored_nodes', 0)}")
        print(f"- Max depth reached: {result.metadata.get('max_depth_reached', 0)}")
        print("="*80)
        
        # Optional: Save the reasoning tree visualization
        if result.metadata.get("reasoning_tree"):
            # In a real implementation, this could generate a visual tree diagram
            print("\nReasoning tree structure (sample):")
            tree_sample = {k: tree_node for k, tree_node in list(result.metadata["reasoning_tree"].items())[:3]}
            print(json.dumps(tree_sample, indent=2)[:500] + "...\n")
        
        return result

async def main():
    """Run the coordinate transformation example."""
    problem_solver = CoordinateSystemProblem()
    await problem_solver.solve_coordinate_transformation()

if __name__ == "__main__":
    asyncio.run(main())
