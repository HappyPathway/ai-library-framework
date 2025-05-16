"""
Agent Planning Patterns.

This module provides different planning strategies for agents, including:
- ReactivePlan: Simple stimulus-response planning
- DeliberativePlan: Multi-step planning with reasoning
- TreeOfThoughtsPlan: Branching thought process for complex problem solving

Each planning strategy implements the PlanningStrategy interface and can be
composed with the base Agent class.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from ailf.agent.base import PlanningStrategy, Agent, AgentStep

logger = logging.getLogger(__name__)


class ReactivePlan(PlanningStrategy):
    """Simple reactive planning strategy.
    
    This strategy creates a one-step plan that directly responds to the input,
    suitable for simple query-response interactions.
    """
    
    async def plan(self, agent: Agent, query: str) -> List[AgentStep]:
        """Generate a simple one-step reactive plan.
        
        Args:
            agent: The agent that will execute the plan
            query: The user query to respond to
            
        Returns:
            List[AgentStep]: A single-step plan
        """
        return [AgentStep(
            action=query,
            reasoning="Direct response to query"
        )]


class DeliberativePlan(PlanningStrategy):
    """Deliberative planning strategy with explicit reasoning steps.
    
    This strategy creates a multi-step plan that includes:
    1. Understanding the problem
    2. Determining required information
    3. Planning approach
    4. Executing the plan
    5. Synthesizing results
    """
    
    async def plan(self, agent: Agent, query: str) -> List[AgentStep]:
        """Generate a deliberative multi-step plan.
        
        Args:
            agent: The agent that will execute the plan
            query: The user query/task to plan for
            
        Returns:
            List[AgentStep]: A multi-step deliberative plan
        """
        # Use the AI engine to generate a plan
        system_prompt = f"""You are {agent.name}, a deliberative agent that plans carefully.
        
You are given a task and need to create a step-by-step plan to complete it.
Each step should include:
1. The specific action to take
2. The reasoning behind this action

Create 3-5 logical steps that will solve the problem effectively.
"""
        
        planning_query = f"""
Task: {query}

Generate a step-by-step plan to complete this task. For each step include:
- What action to take
- Why this action is necessary
"""
        
        # Generate plan using the agent's AI engine
        plan_result = await agent.ai_engine.analyze(
            planning_query,
            system=system_prompt,
            temperature=0.2  # Lower temperature for more logical planning
        )
        
        # Handle different return types from various AI engine implementations
        if isinstance(plan_result, dict) and 'content' in plan_result:
            # Handle dictionary response with content field (some AI engines)
            plan_text = plan_result['content']
        elif isinstance(plan_result, str):
            # Handle direct string response
            plan_text = plan_result
        else:
            # Try to convert to string as fallback
            logger.warning(f"Unexpected plan result type: {type(plan_result)}, attempting to convert to string")
            plan_text = str(plan_result)
        
        # Parse the plan into discrete steps
        # This is a simplified parsing that assumes the AI returns steps in a somewhat structured format
        raw_steps = plan_text.split("\n")
        steps = []
        
        current_step = {"action": "", "reasoning": ""}
        for line in raw_steps:
            line = line.strip()
            if not line:
                continue
                
            # Look for step indicators
            if line.startswith("Step") and ":" in line:
                # If we have an existing step, save it
                if current_step["action"]:
                    steps.append(AgentStep(
                        action=current_step["action"],
                        reasoning=current_step["reasoning"]
                    ))
                    current_step = {"action": "", "reasoning": ""}
                
                # Extract the action from the step
                parts = line.split(":", 1)
                if len(parts) > 1:
                    current_step["action"] = parts[1].strip()
            
            # Look for reasoning indicators
            elif line.startswith("Why:") or line.startswith("Reason:") or line.startswith("Reasoning:"):
                parts = line.split(":", 1)
                if len(parts) > 1:
                    current_step["reasoning"] = parts[1].strip()
            
            # Otherwise, append to the current action or reasoning
            elif current_step["action"] and not current_step["reasoning"]:
                current_step["action"] += " " + line
            elif current_step["reasoning"]:
                current_step["reasoning"] += " " + line
        
        # Add the final step if there is one
        if current_step["action"]:
            steps.append(AgentStep(
                action=current_step["action"],
                reasoning=current_step["reasoning"]
            ))
        
        # If parsing failed to produce steps, create a simple fallback plan
        if not steps:
            logger.warning("Failed to parse deliberative plan, using fallback")
            steps = [
                AgentStep(
                    action="Analyze the task requirements",
                    reasoning="Understanding what needs to be done"
                ),
                AgentStep(
                    action=query,
                    reasoning="Direct execution of the task"
                )
            ]
        
        return steps


class TreeOfThoughtsPlan(PlanningStrategy):
    """Tree of Thoughts planning strategy for complex problem solving.
    
    This strategy explores multiple reasoning paths and selects the most promising one,
    suitable for problems that require creative thinking or exploring alternatives.
    """
    
    def __init__(self, num_thoughts: int = 3, max_depth: int = 2):
        """Initialize the Tree of Thoughts planning strategy.
        
        Args:
            num_thoughts: Number of alternative thoughts to generate at each step
            max_depth: Maximum depth of the thought tree
        """
        self.num_thoughts = num_thoughts
        self.max_depth = max_depth
    
    async def plan(self, agent: Agent, query: str) -> List[AgentStep]:
        """Generate a plan using tree of thoughts methodology.
        
        Args:
            agent: The agent that will execute the plan
            query: The user query/task to plan for
            
        Returns:
            List[AgentStep]: A plan representing the best path through the thought tree
        """
        system_prompt = f"""You are {agent.name}, solving a problem using tree of thoughts methodology.
        
You will explore multiple approaches to solving this problem, considering different perspectives
and techniques. For each thought level:
1. Generate {self.num_thoughts} distinct approaches
2. Evaluate each approach
3. Select the most promising approach to expand further

Be creative but logical in your exploration.
"""
        
        tot_query = f"""
Problem: {query}

Think through this step by step using the tree of thoughts method:
1. Generate {self.num_thoughts} different initial approaches
2. Evaluate the pros and cons of each approach
3. Select the most promising approach
4. Break down the selected approach into concrete steps
"""
        
        # Generate tree of thoughts using the agent's AI engine
        tot_result = await agent.ai_engine.analyze(
            tot_query, 
            system=system_prompt,
            temperature=0.7  # Higher temperature to encourage creative thinking
        )
        
        # Handle different return types from various AI engine implementations
        if isinstance(tot_result, dict) and 'content' in tot_result:
            # Handle dictionary response with content field (some AI engines)
            tot_text = tot_result['content']
        elif isinstance(tot_result, str):
            # Handle direct string response
            tot_text = tot_result
        else:
            # Try to convert to string as fallback
            logger.warning(f"Unexpected ToT result type: {type(tot_result)}, attempting to convert to string")
            tot_text = str(tot_result)
        
        # Extract the final plan steps - this is simplified parsing
        # In a real implementation, we would do more sophisticated extraction
        # First, try to find a section labeled "Final Plan:", if not found, use the whole text
        if "Final Plan:" in tot_text:
            final_plan_section = tot_text.split("Final Plan:", 1)[-1]
            # If there's a conclusion section, extract only the plan part
            if "Conclusion:" in final_plan_section:
                final_plan_section = final_plan_section.split("Conclusion:", 1)[0]
        else:
            # Use the whole text if no specific sections found
            final_plan_section = tot_text
        
        # Parse steps from the final plan
        raw_steps = final_plan_section.split("\n")
        steps = []
        
        current_step = {"action": "", "reasoning": ""}
        for line in raw_steps:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("Step") and ":" in line:
                # Save previous step if it exists
                if current_step["action"]:
                    steps.append(AgentStep(
                        action=current_step["action"],
                        reasoning=current_step["reasoning"]
                    ))
                    current_step = {"action": "", "reasoning": ""}
                
                # Extract new step
                parts = line.split(":", 1)
                if len(parts) > 1:
                    current_step["action"] = parts[1].strip()
            elif current_step["action"] and not current_step["reasoning"]:
                current_step["reasoning"] = line
        
        # Add the final step if there is one
        if current_step["action"]:
            steps.append(AgentStep(
                action=current_step["action"],
                reasoning=current_step["reasoning"]
            ))
        
        # If parsing failed, create a simple fallback plan
        if not steps:
            logger.warning("Failed to parse tree of thoughts plan, using fallback")
            steps = [
                AgentStep(
                    action="Analyze multiple approaches to the problem",
                    reasoning="Exploring different solution paths"
                ),
                AgentStep(
                    action="Select and implement the most promising approach",
                    reasoning="Based on evaluation of alternatives"
                ),
                AgentStep(
                    action=query,
                    reasoning="Executing the selected approach"
                )
            ]
        
        return steps
