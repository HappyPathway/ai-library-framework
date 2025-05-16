"""Tests for task planner.

This module contains tests for the TaskPlanner class in ailf.cognition.task_planner.
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from ailf.cognition.task_planner import TaskPlanner
from ailf.schemas.cognition import Plan, PlanStep


class TestTaskPlanner:
    """Tests for TaskPlanner."""

    @pytest.fixture
    def mock_ai_engine(self):
        """Create a mock AI engine."""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def task_planner(self, mock_ai_engine):
        """Create a TaskPlanner instance with a mock AI engine."""
        return TaskPlanner(ai_engine=mock_ai_engine)

    @pytest.fixture
    def sample_plan(self):
        """Create a sample plan for testing."""
        step1 = PlanStep(step_id="step1", description="First step")
        step2 = PlanStep(step_id="step2", description="Second step", dependencies=["step1"])
        step3 = PlanStep(step_id="step3", description="Third step", dependencies=["step2"])
        return Plan(
            plan_id="test_plan",
            goal="Test goal",
            steps=[step1, step2, step3]
        )

    def test_init(self, mock_ai_engine):
        """Test initialization."""
        planner = TaskPlanner(ai_engine=mock_ai_engine)
        assert planner.ai_engine == mock_ai_engine
        assert planner.step_executors == {}

    def test_register_step_executor(self, task_planner):
        """Test registering a step executor."""
        async def test_executor(step, context):
            return "Test result"

        task_planner.register_step_executor("test_tool", test_executor)
        
        assert "test_tool" in task_planner.step_executors
        assert task_planner.step_executors["test_tool"] == test_executor

    @pytest.mark.asyncio
    async def test_generate_plan_success(self, task_planner, mock_ai_engine, sample_plan):
        """Test successful plan generation."""
        mock_ai_engine.analyze.return_value = sample_plan
        
        result = await task_planner.generate_plan("Test goal")
        
        # Verify AI engine was called correctly
        mock_ai_engine.analyze.assert_called_once()
        args, kwargs = mock_ai_engine.analyze.call_args
        assert "Test goal" in kwargs.get('content', '')
        assert kwargs.get('output_schema') == Plan
        assert kwargs.get('system_prompt') is not None
        
        # Verify returned plan properties
        assert result.goal == "Test goal"
        assert len(result.steps) == 3
        assert result.plan_id is not None  # Should be regenerated for uniqueness

    @pytest.mark.asyncio
    async def test_generate_plan_invalid_response(self, task_planner, mock_ai_engine):
        """Test handling invalid AI response."""
        mock_ai_engine.analyze.return_value = "Not a valid Plan"
        
        result = await task_planner.generate_plan("Test goal")
        
        # Should return a fallback plan with failed status
        assert isinstance(result, Plan)
        assert result.goal == "Test goal"
        assert result.steps == []
        assert result.current_status == "failed_generation"

    @pytest.mark.asyncio
    async def test_execute_plan_success(self, task_planner, sample_plan):
        """Test successful plan execution."""
        # Register a mock executor
        mock_executor = AsyncMock(return_value="Step completed")
        task_planner.register_step_executor("default_executor", mock_executor)
        
        # Execute the plan
        result = await task_planner.execute_plan(sample_plan)
        
        # Verify all steps were executed
        assert mock_executor.call_count == 3
        assert result.current_status == "completed"
        for step in result.steps:
            assert step.status == "completed"
            assert step.result == "Step completed"

    @pytest.mark.asyncio
    async def test_execute_plan_tool_specific_executor(self, task_planner, sample_plan):
        """Test executing with tool-specific executors."""
        # Modify a step to use a specific tool
        sample_plan.steps[1].tool_name = "specific_tool"
        
        # Register executors
        default_executor = AsyncMock(return_value="Default result")
        specific_executor = AsyncMock(return_value="Specific result")
        task_planner.register_step_executor("default_executor", default_executor)
        task_planner.register_step_executor("specific_tool", specific_executor)
        
        # Execute the plan
        result = await task_planner.execute_plan(sample_plan)
        
        # Verify the right executors were called
        assert default_executor.call_count == 2  # For steps 1 and 3
        assert specific_executor.call_count == 1  # For step 2
        assert result.steps[0].result == "Default result"
        assert result.steps[1].result == "Specific result"
        assert result.steps[2].result == "Default result"

    @pytest.mark.asyncio
    async def test_execute_plan_missing_executor(self, task_planner, sample_plan):
        """Test handling missing executor."""
        # Set a tool name but don't register the corresponding executor
        sample_plan.steps[1].tool_name = "nonexistent_tool"
        
        # Register default executor for other steps
        default_executor = AsyncMock(return_value="Default result")
        task_planner.register_step_executor("default_executor", default_executor)
        
        # Execute the plan
        result = await task_planner.execute_plan(sample_plan)
        
        # Verify execution stopped when reaching the step with missing executor
        assert default_executor.call_count == 1  # Only the first step should execute
        assert result.current_status == "failed"
        assert result.steps[0].status == "completed"
        assert result.steps[1].status == "failed_no_executor"
        assert "No executor found" in result.steps[1].result
        # Step 3 should not have been attempted
        assert result.steps[2].status == "pending"

    @pytest.mark.asyncio
    async def test_execute_plan_step_failure(self, task_planner, sample_plan):
        """Test handling step execution failure."""
        # First executor succeeds, second fails
        def success(*args, **kwargs):
            return "Success"
            
        def failure(*args, **kwargs):
            raise ValueError("Test error")
            
        task_planner.register_step_executor("default_executor", AsyncMock(side_effect=[
            success(), failure(), success()  # for steps 1, 2, 3
        ]))
        
        # Execute the plan
        result = await task_planner.execute_plan(sample_plan)
        
        # Verify execution stopped after failure
        assert result.current_status == "failed"
        assert result.steps[0].status == "completed"
        assert result.steps[1].status == "failed"
        assert "error" in result.steps[1].result.lower()
        # Step 3 should not have been attempted
        assert result.steps[2].status == "pending"

    @pytest.mark.asyncio
    async def test_execute_plan_dependency_resolution(self, task_planner):
        """Test dependency resolution and execution order."""
        # Create a plan with complex dependencies
        step1 = PlanStep(step_id="step1", description="First step")
        step2 = PlanStep(step_id="step2", description="Second step", dependencies=["step1"])
        step3 = PlanStep(step_id="step3", description="Third step", dependencies=["step1"])
        step4 = PlanStep(step_id="step4", description="Fourth step", dependencies=["step2", "step3"])
        
        complex_plan = Plan(
            plan_id="complex_plan",
            goal="Test complex dependencies",
            steps=[step1, step2, step3, step4]  # Deliberately out of order
        )
        
        # Spy on step execution to track order
        execution_order = []
        
        async def track_execution(step, context):
            execution_order.append(step.step_id)
            return f"Executed {step.step_id}"
            
        task_planner.register_step_executor("default_executor", track_execution)
        
        # Execute the plan
        result = await task_planner.execute_plan(complex_plan)
        
        # Verify correct execution order based on dependencies
        assert execution_order[0] == "step1"  # Must be first
        # step2 and step3 can be in any order since they both depend only on step1
        assert set(execution_order[1:3]) == {"step2", "step3"}
        assert execution_order[3] == "step4"  # Must be last
        
        # Verify all steps completed
        assert result.current_status == "completed"
        for step in result.steps:
            assert step.status == "completed"

    @pytest.mark.asyncio
    async def test_execute_plan_circular_dependencies(self, task_planner):
        """Test handling circular dependencies."""
        # Create a plan with circular dependencies
        step1 = PlanStep(step_id="step1", description="First step", dependencies=["step3"])
        step2 = PlanStep(step_id="step2", description="Second step", dependencies=["step1"])
        step3 = PlanStep(step_id="step3", description="Third step", dependencies=["step2"])
        
        circular_plan = Plan(
            plan_id="circular_plan",
            goal="Test circular dependencies",
            steps=[step1, step2, step3]
        )
        
        mock_executor = AsyncMock(return_value="Step executed")
        task_planner.register_step_executor("default_executor", mock_executor)
        
        # Execute the plan
        result = await task_planner.execute_plan(circular_plan)
        
        # Verify the planner detected the circular dependency issue
        assert result.current_status == "failed_dependency_resolution"
        assert mock_executor.call_count == 0  # No steps should execute
        for step in result.steps:
            assert step.status == "skipped_dependency_issue"

    @pytest.mark.asyncio
    async def test_execute_plan_with_context(self, task_planner, sample_plan):
        """Test executing a plan with initial context."""
        # Create a mock executor that uses context
        async def context_using_executor(step, context):
            # Return a combination of step id and any context values
            context_values = [f"{k}={v}" for k, v in context.items()]
            return f"{step.step_id} with {', '.join(context_values)}"
            
        task_planner.register_step_executor("default_executor", context_using_executor)
        
        # Initial context
        initial_context = {"param1": "value1", "param2": 42}
        
        # Execute the plan with context
        result = await task_planner.execute_plan(sample_plan, initial_context=initial_context)
        
        # Verify context was passed and results were properly accumulated
        assert "param1=value1" in result.steps[0].result
        assert "param2=42" in result.steps[0].result
        # Step 2 should have access to step1's result
        assert "step1=" in result.steps[1].result
        # Step 3 should have access to step2's result
        assert "step2=" in result.steps[2].result
