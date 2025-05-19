"""Tests for ReAct processor.

This module contains tests for the ReActProcessor class in ailf.cognition.react_processor.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from ailf.cognition.react_processor import ReActProcessor, ReActStep, ReActStepType, ReActState


class TestReActProcessor:
    """Tests for ReActProcessor."""

    @pytest.fixture
    def mock_ai_engine(self):
        """Create a mock AI engine."""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def react_processor(self, mock_ai_engine):
        """Create a ReActProcessor instance with a mock AI engine."""
        return ReActProcessor(ai_engine=mock_ai_engine)

    def test_init(self, mock_ai_engine):
        """Test initialization."""
        processor = ReActProcessor(ai_engine=mock_ai_engine, max_steps=5)
        assert processor.ai_engine == mock_ai_engine
        assert processor.default_max_steps == 5
        assert processor.tools == {}

    def test_register_tool(self, react_processor):
        """Test tool registration."""
        async def test_tool(param1: str, param2: int = 0) -> str:
            """Test tool documentation."""
            return f"Result: {param1}, {param2}"

        react_processor.register_tool("test_tool", test_tool, "A test tool.")
        
        assert "test_tool" in react_processor.tools
        assert react_processor.tools["test_tool"] == test_tool

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, react_processor):
        """Test successful tool execution."""
        async def add(a: int, b: int) -> int:
            return a + b

        react_processor.register_tool("add", add)
        
        result = await react_processor._execute_tool("add", {"a": 2, "b": 3})
        assert result == "5"

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, react_processor):
        """Test executing a non-existent tool."""
        result = await react_processor._execute_tool("nonexistent_tool", {})
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_error(self, react_processor):
        """Test error handling during tool execution."""
        async def failing_tool(**kwargs) -> str:
            raise ValueError("Test error")

        react_processor.register_tool("failing_tool", failing_tool)
        
        result = await react_processor._execute_tool("failing_tool", {})
        assert "error" in result.lower()
        assert "test error" in result.lower()

    def test_format_history_for_prompt(self, react_processor):
        """Test formatting history for prompt."""
        history = [
            ReActStep(step_type=ReActStepType.THOUGHT, content="I need to add two numbers."),
            ReActStep(step_type=ReActStepType.ACTION, content="Add numbers", tool_name="add", tool_input={"a": 2, "b": 3}),
            ReActStep(step_type=ReActStepType.OBSERVATION, content="5")
        ]
        
        formatted_history = react_processor._format_history_for_prompt(history)
        
        assert "Thought: I need to add two numbers." in formatted_history
        assert 'Action: Tool: add, Input: {"a": 2, "b": 3}' in formatted_history
        assert "Observation: 5" in formatted_history

    @pytest.mark.asyncio
    async def test_process_thought_only(self, react_processor, mock_ai_engine):
        """Test process with only thought steps."""
        # Setup AI engine to generate a thought and then a final answer
        mock_ai_engine.analyze.side_effect = [
            ReActStep(step_type=ReActStepType.THOUGHT, content="I'm thinking about this question."),
            ReActStep(step_type=ReActStepType.THOUGHT, content="The final answer is 42.")
        ]
        
        state = await react_processor.process("What is the meaning of life?")
        
        assert len(state.history) == 2
        assert state.history[0].step_type == ReActStepType.THOUGHT
        assert state.history[1].step_type == ReActStepType.THOUGHT
        assert "final answer" in state.history[1].content.lower()
        assert state.is_halted is True
        assert state.final_answer == "The final answer is 42."

    @pytest.mark.asyncio
    async def test_process_with_action(self, react_processor, mock_ai_engine):
        """Test process with action steps."""
        # Register a test tool
        async def get_weather(location: str) -> str:
            return f"Weather in {location}: Sunny, 72°F"

        react_processor.register_tool("get_weather", get_weather)
        
        # Setup AI engine to generate a thought, action, and final answer
        mock_ai_engine.analyze.side_effect = [
            ReActStep(step_type=ReActStepType.THOUGHT, content="I should check the weather."),
            ReActStep(step_type=ReActStepType.ACTION, content="Check weather", tool_name="get_weather", tool_input={"location": "New York"}),
            ReActStep(step_type=ReActStepType.THOUGHT, content="The final answer is that it's sunny in New York.")
        ]
        
        state = await react_processor.process("What's the weather in New York?")
        
        assert len(state.history) == 4  # Thought, Action, Observation, Thought
        assert state.history[0].step_type == ReActStepType.THOUGHT
        assert state.history[1].step_type == ReActStepType.ACTION
        assert state.history[2].step_type == ReActStepType.OBSERVATION
        assert "sunny" in state.history[2].content.lower()
        assert state.history[3].step_type == ReActStepType.THOUGHT
        assert state.is_halted is True
        assert "sunny" in state.final_answer.lower()

    @pytest.mark.asyncio
    async def test_process_max_steps(self, react_processor, mock_ai_engine):
        """Test process halts after max steps."""
        # Setup AI engine to always generate thoughts that don't conclude
        mock_ai_engine.analyze.return_value = ReActStep(step_type=ReActStepType.THOUGHT, content="Still thinking...")
        
        state = await react_processor.process("Complex question", max_steps=3)
        
        assert len(state.history) == 3
        assert state.current_step_number == 3
        assert state.is_halted is True
        assert state.final_answer is not None
        assert "max steps" in state.final_answer.lower()

    @pytest.mark.asyncio
    async def test_process_invalid_response(self, react_processor, mock_ai_engine):
        """Test process handles invalid AI response."""
        # Setup AI engine to return something that's not a ReActStep
        mock_ai_engine.analyze.return_value = "Not a valid ReActStep"
        
        state = await react_processor.process("Test question")
        
        assert len(state.history) == 1
        assert state.history[0].step_type == ReActStepType.OBSERVATION
        assert "error" in state.history[0].content.lower()
        assert state.is_halted is True

    @pytest.mark.asyncio
    async def test_process_action_without_tool_name(self, react_processor, mock_ai_engine):
        """Test process handles action without tool name."""
        # Setup AI engine to generate an action without a tool name
        mock_ai_engine.analyze.return_value = ReActStep(step_type=ReActStepType.ACTION, content="Do something", tool_name=None)
        
        state = await react_processor.process("Test question")
        
        assert len(state.history) == 2  # Action, Observation (error)
        assert state.history[0].step_type == ReActStepType.ACTION
        assert state.history[1].step_type == ReActStepType.OBSERVATION
        assert "error" in state.history[1].content.lower()
        assert state.is_halted is True

    @pytest.mark.asyncio
    async def test_process_with_nonexistent_tool(self, react_processor, mock_ai_engine):
        """Test process handles actions with non-existent tools."""
        # Setup AI engine to request a non-existent tool
        mock_ai_engine.analyze.return_value = ReActStep(step_type=ReActStepType.ACTION, content="Use non-existent tool", tool_name="nonexistent_tool")
        
        state = await react_processor.process("Test question")
        
        assert len(state.history) == 2  # Action, Observation (error)
        assert state.history[0].step_type == ReActStepType.ACTION
        assert state.history[1].step_type == ReActStepType.OBSERVATION
        assert "tool 'nonexistent_tool' not found" in state.history[1].content.lower()
        assert state.is_halted is True
