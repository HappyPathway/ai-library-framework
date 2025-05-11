"""
Unit tests for AILF-Kagent agent adapters.

These tests verify that Kagent agents can be enhanced with AILF's cognitive capabilities.
"""

import pytest
import asyncio
import sys
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, patch, MagicMock

# Mock dependency imports to allow testing without actual dependencies
try:
    # Try to import actual dependencies
    from ailf.cognition import ReActProcessor
    from ailf.schemas.reasoning import ReActState
    from kagent.agents import Agent as KAgent
    from kagent.schema import AgentResponse, AgentMessage
except ImportError:
    # Create mock classes if dependencies aren't available
    class ReActProcessor:
        async def process(self, *args, **kwargs):
            pass
    
    class ReActState:
        final_answer = ""
        reasoning_steps = []
        def dict(self):
            return {}
    
    class KAgent:
        async def run(self, *args, **kwargs):
            pass
    
    class AgentResponse:
        def __init__(self, messages=None, metadata=None):
            self.messages = messages or []
            self.metadata = metadata or {}
    
    class AgentMessage:
        def __init__(self, content="", role=""):
            self.content = content
            self.role = role

# Import adapter components
from ailf_kagent.adapters.agents import AILFEnabledAgent, ReActAgent


class TestAILFEnabledAgent:
    """Test suite for AILFEnabledAgent"""

    @pytest.fixture
    def react_processor_mock(self):
        """Create a mock ReActProcessor for testing"""
        mock = AsyncMock(spec=ReActProcessor)
        mock.process = AsyncMock()
        return mock

    @pytest.fixture
    def agent(self, react_processor_mock):
        """Create an AILFEnabledAgent for testing"""
        with patch('ailf_kagent.adapters.agents.ReActProcessor', return_value=react_processor_mock):
            agent = AILFEnabledAgent()
            # Directly assign the mock to ensure it's used
            agent.react_processor = react_processor_mock
            return agent

    def test_agent_initialization(self):
        """Test that the agent initializes correctly"""
        agent = AILFEnabledAgent(
            use_react_for_complex=True,
            reasoning_threshold=0.5
        )
        
        assert isinstance(agent.react_processor, ReActProcessor)
        assert agent.use_react_for_complex is True
        assert agent.reasoning_threshold == 0.5

    def test_requires_reasoning_with_indicators(self, agent):
        """Test that the agent detects reasoning need based on indicators"""
        # Queries containing reasoning indicators
        assert agent._requires_reasoning("Can you explain step by step how to solve this problem?")
        assert agent._requires_reasoning("Why does this happen in this situation?")
        assert agent._requires_reasoning("Compare these two approaches and analyze their strengths.")
        
        # Simple queries without reasoning indicators
        assert not agent._requires_reasoning("Hello")
        assert not agent._requires_reasoning("What time is it?")
    
    def test_requires_reasoning_with_length(self, agent):
        """Test that the agent detects reasoning need based on query length"""
        # Long query without explicit indicators should trigger reasoning
        long_query = "This is a very long question that contains many words but doesn't actually " + \
                    "have any specific reasoning indicators. However, due to its length alone, " + \
                    "the agent should recognize that it might require complex thought to address " + \
                    "all the aspects mentioned in this verbose and extensive query that continues " + \
                    "for multiple sentences without using keywords like 'explain' or 'analyze'."
        
        assert agent._requires_reasoning(long_query)

    def test_requires_reasoning_disabled(self):
        """Test that reasoning detection can be disabled"""
        agent = AILFEnabledAgent(use_react_for_complex=False)
        
        # Even with reasoning indicators, it should return False when disabled
        assert not agent._requires_reasoning("Please explain step by step")

    def test_format_result(self, agent):
        """Test formatting of ReAct results into AgentResponse"""
        # Create a mock ReActState
        react_state = MagicMock(spec=ReActState)
        react_state.final_answer = "This is the final answer"
        react_state.reasoning_steps = [
            MagicMock(dict=lambda: {"thought": "First thought"}),
            MagicMock(dict=lambda: {"thought": "Second thought"})
        ]
        
        # Format the result
        response = agent._format_result(react_state)
        
        # Check the response structure
        assert isinstance(response, AgentResponse)
        assert len(response.messages) == 1
        assert response.messages[0].content == "This is the final answer"
        assert response.messages[0].role == "assistant"
        
        # Check that reasoning steps are included in metadata
        assert "reasoning_trace" in response.metadata
        assert len(response.metadata["reasoning_trace"]) == 2

    @pytest.mark.asyncio
    async def test_run_without_reasoning(self, agent):
        """Test running a simple query that doesn't need reasoning"""
        # Mock the parent run method
        parent_run_mock = AsyncMock(return_value=AgentResponse(messages=[AgentMessage(content="Simple response", role="assistant")]))
        with patch.object(KAgent, 'run', parent_run_mock):
            response = await agent.run("What's your name?")
        
        # Verify parent run was called and react processor was not used
        parent_run_mock.assert_called_once()
        agent.react_processor.process.assert_not_called()
        
        # Check the response
        assert response.messages[0].content == "Simple response"

    @pytest.mark.asyncio
    async def test_run_with_reasoning(self, agent, react_processor_mock):
        """Test running a complex query that needs reasoning"""
        # Mock the ReAct process method to return a state
        react_state = MagicMock(spec=ReActState)
        react_state.final_answer = "Complex reasoning result"
        react_state.reasoning_steps = [MagicMock(dict=lambda: {"thought": "Complex analysis"})]
        react_processor_mock.process.return_value = react_state
        
        # Run a complex query
        response = await agent.run("Can you explain step by step why this happens?")
        
        # Verify react processor was used
        react_processor_mock.process.assert_called_once_with("Can you explain step by step why this happens?")
        
        # Check the response
        assert response.messages[0].content == "Complex reasoning result"
        assert "reasoning_trace" in response.metadata


class TestReActAgent:
    """Test suite for ReActAgent"""

    @pytest.fixture
    def react_agent(self):
        """Create a ReActAgent for testing"""
        with patch('ailf_kagent.adapters.agents.ReActProcessor'):
            return ReActAgent()

    def test_agent_initialization(self, react_agent):
        """Test that the specialized ReAct agent initializes correctly"""
        # Should always have use_react_for_complex=True
        assert react_agent.use_react_for_complex is True
    
    def test_always_requires_reasoning(self, react_agent):
        """Test that ReActAgent always uses reasoning regardless of query"""
        # Should return True for any query
        assert react_agent._requires_reasoning("Hello")
        assert react_agent._requires_reasoning("What time is it?")
        assert react_agent._requires_reasoning("Just a simple question")
