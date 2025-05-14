"""
Tests for the agent framework.

This module contains unit tests for the unified agent framework.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import from our local test module instead of the installed package
from tests.unit.agent import Agent, ReactivePlan, DeliberativePlan, TreeOfThoughtsPlan
from tests.unit.agent import AgentStatus, AgentStep
from tests.unit.agent import tool, ToolRegistry, execute_tool


class TestAgent(unittest.TestCase):
    """Tests for the base Agent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock AIEngine
        self.mock_engine_patcher = patch('ailf.agent.base.AIEngine')
        self.mock_engine_cls = self.mock_engine_patcher.start()
        self.mock_engine = self.mock_engine_cls.return_value
        self.mock_engine.analyze = AsyncMock(return_value="Test response")
        
        # Create test agent
        self.agent = Agent(
            name="TestAgent",
            model_name="test-model"
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.mock_engine_patcher.stop()
    
    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.name, "TestAgent")
        self.assertEqual(self.agent.config.model_name, "test-model")
        self.assertEqual(self.agent.status, AgentStatus.IDLE)
    
    def test_add_tool(self):
        """Test adding a tool to the agent."""
        def test_tool(): 
            """Test tool docstring."""
            pass
        
        self.agent.add_tool(test_tool)
        self.assertIn("test_tool", self.agent.tools)
    
    @pytest.mark.asyncio
    async def test_run_simple(self):
        """Test running an agent with no planning strategy."""
        result = await self.agent.run("Test query")
        
        # Verify agent called AI engine
        self.mock_engine.analyze.assert_called_once()
        
        # Check result
        self.assertEqual(result, "Test response")
    
    @pytest.mark.asyncio
    async def test_run_with_planning(self):
        """Test running an agent with a planning strategy."""
        # Create a mock planning strategy
        mock_plan = MagicMock(spec=ReactivePlan)
        mock_plan.plan = AsyncMock(return_value=[
            AgentStep(action="Step 1", reasoning="Reasoning 1"),
            AgentStep(action="Step 2", reasoning="Reasoning 2")
        ])
        
        # Set planning strategy
        self.agent.planning_strategy = mock_plan
        
        # Run agent
        await self.agent.run("Test query")
        
        # Verify planning was called
        mock_plan.plan.assert_called_once_with(self.agent, "Test query")
        
        # Verify AI engine was called twice (once per step)
        self.assertEqual(self.mock_engine.analyze.call_count, 2)


class TestPlanningStrategies(unittest.TestCase):
    """Tests for agent planning strategies."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock AIEngine
        self.mock_engine_patcher = patch('ailf.agent.base.AIEngine')
        self.mock_engine_cls = self.mock_engine_patcher.start()
        self.mock_engine = self.mock_engine_cls.return_value
        self.mock_engine.analyze = AsyncMock(return_value="""
Step 1: Understand the problem
Reason: Need to clarify what we're solving

Step 2: Research the topic
Reason: Gather necessary information

Step 3: Synthesize a solution
Reason: Combine information into answer
""")
        
        # Create test agent
        self.agent = Agent(
            name="TestAgent",
            model_name="test-model"
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.mock_engine_patcher.stop()
    
    @pytest.mark.asyncio
    async def test_reactive_plan(self):
        """Test reactive planning strategy."""
        strategy = ReactivePlan()
        steps = await strategy.plan(self.agent, "Test query")
        
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].action, "Test query")
    
    @pytest.mark.asyncio
    async def test_deliberative_plan(self):
        """Test deliberative planning strategy."""
        strategy = DeliberativePlan()
        steps = await strategy.plan(self.agent, "Test query")
        
        # Should parse the mock response into 3 steps
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0].action, "Understand the problem")
        self.assertEqual(steps[1].action, "Research the topic")
        self.assertEqual(steps[2].action, "Synthesize a solution")


class TestTools(unittest.TestCase):
    """Tests for agent tools functionality."""
    
    def test_tool_decorator(self):
        """Test the tool decorator."""
        @tool(name="custom_name", description="Custom description")
        def test_tool(param1: str, param2: int = 0) -> str:
            """Test tool docstring.
            
            :param param1: First parameter
            :param param2: Second parameter
            :return: A test result
            """
            return f"{param1} {param2}"
        
        # Check tool metadata
        tool_meta = getattr(test_tool, "_tool_meta", None)
        self.assertIsNotNone(tool_meta)
        self.assertEqual(tool_meta.name, "custom_name")
        self.assertEqual(tool_meta.description, "Custom description")
        
        # Check parameters
        self.assertIn("param1", tool_meta.parameters)
        self.assertIn("param2", tool_meta.parameters)
        self.assertTrue(tool_meta.parameters["param1"]["required"])
        self.assertFalse(tool_meta.parameters["param2"]["required"])
    
    def test_tool_registry(self):
        """Test the tool registry."""
        registry = ToolRegistry()
        
        # Register a tool
        @registry.register(category="test")
        def test_tool():
            """Test tool."""
            return "test"
        
        # Check registration
        self.assertIn("test_tool", registry.tools)
        self.assertEqual(registry.descriptions["test_tool"].category, "test")
        
        # Get tool by name
        tool_func = registry.get("test_tool")
        self.assertIsNotNone(tool_func)
        self.assertEqual(tool_func(), "test")
        
        # Get tools by category
        category_tools = registry.get_by_category("test")
        self.assertEqual(len(category_tools), 1)
        self.assertEqual(category_tools[0].name, "test_tool")
    
    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test tool execution."""
        # Test successful execution
        def success_tool(x: int, y: int) -> int:
            return x + y
        
        result = await execute_tool(success_tool, x=1, y=2)
        self.assertTrue(result.success)
        self.assertEqual(result.result, 3)
        
        # Test failed execution
        def failing_tool():
            raise ValueError("Test error")
        
        result = await execute_tool(failing_tool)
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Test error")
        
        # Test async tool
        async def async_tool(x: int) -> int:
            await asyncio.sleep(0.1)
            return x * 2
        
        result = await execute_tool(async_tool, x=3)
        self.assertTrue(result.success)
        self.assertEqual(result.result, 6)
