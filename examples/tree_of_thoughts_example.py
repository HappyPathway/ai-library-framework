"""Example usage of the Tree of Thoughts processor."""

import asyncio
from typing import Optional, Dict, Any

# Placeholder for AIEngine
try:
    from utils.ai.engine import AIEngine
except ImportError:
    class AIEngine: # type: ignore
        async def analyze(self, content: str, system_prompt: Optional[str] = None, **kwargs):
            print(f"Analyzing with prompt: {system_prompt}\nContent: {content[:50]}...")
            # For demo purposes
            if "initial" in (system_prompt or "").lower():
                return {"content": "I should break this down into smaller problems"}
            elif "generate" in content.lower():
                return {"content": "1. Consider material constraints\n2. Calculate energy requirements\n3. Evaluate orbital stability"}
            elif "evaluate" in content.lower():
                return {"content": "This is a promising direction. Score: 0.82"}
            else:
                return {"content": "The solution involves using carbon nanotubes for the tether, stationed at geosynchronous orbit, with counterweight beyond GEO."}

from ailf.cognition.tree_of_thoughts import TreeOfThoughtsProcessor
from ailf.schemas.tree_of_thought import ToTConfiguration, EvaluationStrategy
from ailf.schemas.cognition import TaskContext

async def main():
    """Run a demonstration of the Tree of Thoughts processor."""
    print("Tree of Thoughts Example\n")
    
    # Create AI engine
    print("Initializing AI Engine...")
    ai_engine = AIEngine()
    
    # Configure Tree of Thoughts
    print("Setting up Tree of Thoughts processor...")
    config = ToTConfiguration(
        max_depth=3,
        branching_factor=3,
        beam_width=2,
        temperature=0.7,
        evaluation_strategy=EvaluationStrategy.OBJECTIVE_BASED
    )
    
    # Create processor
    tot_processor = TreeOfThoughtsProcessor(ai_engine, config=config)
    
    # Create task context
    problem = "Design a space elevator that can transport 10 tons of cargo to geosynchronous orbit."
    context = TaskContext(
        user_input=problem,
        conversation_history=[],
        task_type="problem_solving"
    )
    
    # Process the problem
    print(f"\nProcessing problem: {problem}\n")
    result = await tot_processor.process(context)
    
    # Display results
    print("\n" + "="*80)
    print(f"Solution (confidence: {result.confidence:.2f}):\n")
    print(result.output)
    print("\nReasoning path:")
    print(result.reasoning)
    print("\nMetadata:")
    print(f"- Explored nodes: {result.metadata.get('explored_nodes', 0)}")
    print(f"- Max depth: {result.metadata.get('max_depth_reached', 0)}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
