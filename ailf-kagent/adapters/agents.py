"""
Agent adapter for integrating AILF cognitive capabilities with Kagent.

This module provides adapter classes that allow Kagent agents to leverage AILF's
cognitive capabilities, such as ReAct patterns and intent refinement.
"""

from typing import Any, Dict, List, Optional, Union, Type
import inspect
from pydantic import BaseModel

# Import Kagent components
from kagent.agents import Agent as KAgent
from kagent.schema import AgentResponse, AgentMessage

# Import AILF components
# Note: These imports may need to be adjusted based on actual AILF structure
from ailf.cognition import ReActProcessor
from ailf.schemas.cognition import ReActState

# Import the AIEngine adapter
from ailf_kagent.adapters.ai_engine import AIEngineAdapter


class AILFEnabledAgent(KAgent):
    """Kagent agent with AILF cognitive capabilities.
    
    This adapter enhances Kagent agents with AILF's cognitive processing capabilities,
    allowing for more sophisticated reasoning and intent refinement.
    
    Attributes:
        react_processor: The AILF ReAct processor for step-by-step reasoning
        use_react_for_complex: Whether to automatically use ReAct for complex queries
        reasoning_threshold: Complexity threshold for triggering ReAct reasoning
    """
    
    def __init__(
        self, 
        *args, 
        use_react_for_complex: bool = True,
        reasoning_threshold: float = 0.7,
        model_name: str = "gpt-4-turbo",  # Default model for AIEngine
        **kwargs
    ):
        """Initialize the AILF-enabled agent.
        
        Args:
            *args: Arguments to pass to the parent Kagent Agent
            use_react_for_complex: Whether to automatically use ReAct for complex queries
            reasoning_threshold: Complexity threshold for triggering ReAct (0-1)
            model_name: Model name to use for the AIEngine
            **kwargs: Keyword arguments to pass to the parent Kagent Agent
        """
        super().__init__(*args, **kwargs)
        
        # Initialize AIEngine with Kagent model access
        ai_engine = AIEngineAdapter(
            model_name=model_name, 
            feature_name="ailf_kagent"
        )
        
        # Initialize the ReAct processor with our AIEngine adapter
        self.react_processor = ReActProcessor(ai_engine=ai_engine)
        self.use_react_for_complex = use_react_for_complex
        self.reasoning_threshold = reasoning_threshold
    
    def _requires_reasoning(self, query: str) -> bool:
        """Determine if a query requires advanced reasoning.
        
        This method analyzes the input query to determine if it would benefit
        from step-by-step reasoning through the ReAct pattern.
        
        Args:
            query: The user query to analyze
            
        Returns:
            True if the query should use ReAct reasoning, False otherwise
        """
        if not self.use_react_for_complex:
            return False
            
        # Simple heuristic based on query length and complexity indicators
        # In a real implementation, this could use more sophisticated detection
        complexity_indicators = [
            "step by step", "explain", "analyze", "compare", "why", "how would",
            "solve", "determine", "think through"
        ]
        
        # Check for explicit reasoning requests
        for indicator in complexity_indicators:
            if indicator in query.lower():
                return True
                
        # Consider length as a complexity factor
        if len(query.split()) > 50:
            return True
            
        return False
    
    def _format_result(self, react_result: ReActState) -> AgentResponse:
        """Format a ReAct result as a Kagent agent response.
        
        Args:
            react_result: The result from the ReAct processor
            
        Returns:
            Formatted AgentResponse for Kagent compatibility
        """
        # Extract the final answer from the ReAct state
        final_answer = react_result.final_answer or "No definitive answer found."
        
        # Create a standard agent message
        message = AgentMessage(
            content=final_answer,
            role="assistant"
        )
        
        # Include reasoning trace in metadata if available
        metadata = {}
        if react_result.reasoning_steps:
            metadata["reasoning_trace"] = [
                step.dict() for step in react_result.reasoning_steps
            ]
        
        return AgentResponse(
            messages=[message],
            metadata=metadata
        )
    
    async def run(self, query: str, *args, **kwargs) -> AgentResponse:
        """Run the agent on a query, using AILF's reasoning when appropriate.
        
        Args:
            query: The user query to process
            *args: Additional arguments to pass to the parent run method
            **kwargs: Additional keyword arguments to pass to the parent run method
            
        Returns:
            The agent's response
        """
        # Check if we should use ReAct reasoning
        if self._requires_reasoning(query):
            # Use AILF's ReAct processor for step-by-step reasoning
            result = await self.react_processor.process(query)
            return self._format_result(result)
        
        # Fall back to standard Kagent processing for simpler queries
        return await super().run(query, *args, **kwargs)


class ReActAgent(AILFEnabledAgent):
    """Specialized agent that always uses ReAct reasoning.
    
    This is a convenience class for cases where all queries should use
    the ReAct reasoning pattern from AILF.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize a ReAct-focused agent.
        
        Args:
            *args: Arguments to pass to AILFEnabledAgent
            **kwargs: Keyword arguments to pass to AILFEnabledAgent
        """
        # Override the use_react_for_complex setting
        super().__init__(*args, use_react_for_complex=True, **kwargs)
    
    def _requires_reasoning(self, query: str) -> bool:
        """Always use reasoning for this specialized agent.
        
        Args:
            query: The user query (ignored for this agent type)
            
        Returns:
            Always returns True
        """
        return True
