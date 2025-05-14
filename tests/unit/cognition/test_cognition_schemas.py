"""Tests for cognition schemas.

This module contains tests for the Pydantic models in ailf.schemas.cognition.
"""
import time
import pytest
from pydantic import ValidationError

from ailf.schemas.cognition import (
    ReActStepType,
    ReActStep,
    ReActState,
    PlanStep,
    Plan,
    IntentRefinementRequest,
    IntentRefinementResponse,
    PromptTemplateV1
)


class TestReActStepType:
    """Tests for ReActStepType enum."""

    def test_values(self):
        """Test enum values."""
        assert ReActStepType.THOUGHT == "thought"
        assert ReActStepType.ACTION == "action"
        assert ReActStepType.OBSERVATION == "observation"


class TestReActStep:
    """Tests for ReActStep model."""

    def test_create_thought_step(self):
        """Test creating a thought step."""
        step = ReActStep(
            step_type=ReActStepType.THOUGHT,
            content="I should check the weather."
        )
        
        assert step.step_type == ReActStepType.THOUGHT
        assert step.content == "I should check the weather."
        assert step.tool_name is None
        assert step.tool_input is None
        assert isinstance(step.timestamp, float)
        # Timestamp should be recent (within last few seconds)
        assert abs(time.time() - step.timestamp) < 5
    
    def test_create_action_step(self):
        """Test creating an action step."""
        tool_input = {"location": "New York"}
        step = ReActStep(
            step_type=ReActStepType.ACTION,
            content="Check weather for New York",
            tool_name="get_weather",
            tool_input=tool_input
        )
        
        assert step.step_type == ReActStepType.ACTION
        assert step.content == "Check weather for New York"
        assert step.tool_name == "get_weather"
        assert step.tool_input == tool_input
    
    def test_create_observation_step(self):
        """Test creating an observation step."""
        step = ReActStep(
            step_type=ReActStepType.OBSERVATION,
            content="It is sunny and 72°F in New York."
        )
        
        assert step.step_type == ReActStepType.OBSERVATION
        assert step.content == "It is sunny and 72°F in New York."
    
    def test_required_fields(self):
        """Test validation of required fields."""
        # Missing step_type
        with pytest.raises(ValidationError):
            ReActStep(content="Test content")
        
        # Missing content
        with pytest.raises(ValidationError):
            ReActStep(step_type=ReActStepType.THOUGHT)


class TestReActState:
    """Tests for ReActState model."""

    def test_create_with_defaults(self):
        """Test creating state with default values."""
        state = ReActState(initial_prompt="What's the weather?")
        
        assert state.initial_prompt == "What's the weather?"
        assert state.max_steps == 10
        assert state.current_step_number == 0
        assert state.history == []
        assert state.final_answer is None
        assert state.is_halted is False
    
    def test_create_with_custom_values(self):
        """Test creating state with custom values."""
        history = [
            ReActStep(step_type=ReActStepType.THOUGHT, content="I need to check the weather."),
            ReActStep(step_type=ReActStepType.ACTION, content="Get weather", tool_name="weather_api", tool_input={"location": "Seattle"})
        ]
        
        state = ReActState(
            initial_prompt="What's the weather in Seattle?",
            max_steps=5,
            current_step_number=2,
            history=history,
            final_answer="It is raining in Seattle.",
            is_halted=True
        )
        
        assert state.initial_prompt == "What's the weather in Seattle?"
        assert state.max_steps == 5
        assert state.current_step_number == 2
        assert len(state.history) == 2
        assert state.history[0].content == "I need to check the weather."
        assert state.history[1].tool_name == "weather_api"
        assert state.final_answer == "It is raining in Seattle."
        assert state.is_halted is True
    
    def test_required_fields(self):
        """Test validation of required fields."""
        # Missing initial_prompt
        with pytest.raises(ValidationError):
            ReActState()


class TestPlanStep:
    """Tests for PlanStep model."""

    def test_create_with_defaults(self):
        """Test creating plan step with default values."""
        step = PlanStep(
            step_id="step1",
            description="Search for weather information."
        )
        
        assert step.step_id == "step1"
        assert step.description == "Search for weather information."
        assert step.tool_name is None
        assert step.tool_inputs is None
        assert step.dependencies == []
        assert step.status == "pending"
        assert step.result is None
    
    def test_create_with_custom_values(self):
        """Test creating plan step with custom values."""
        tool_inputs = {"query": "weather in Paris"}
        dependencies = ["step0"]
        
        step = PlanStep(
            step_id="step1",
            description="Search for weather information.",
            tool_name="search",
            tool_inputs=tool_inputs,
            dependencies=dependencies,
            status="completed",
            result={"temperature": 22, "conditions": "sunny"}
        )
        
        assert step.step_id == "step1"
        assert step.description == "Search for weather information."
        assert step.tool_name == "search"
        assert step.tool_inputs == tool_inputs
        assert step.dependencies == dependencies
        assert step.status == "completed"
        assert step.result == {"temperature": 22, "conditions": "sunny"}


class TestPlan:
    """Tests for Plan model."""

    def test_create_with_defaults(self):
        """Test creating plan with default values."""
        plan = Plan(
            plan_id="plan1",
            goal="Find the weather forecast for Paris."
        )
        
        assert plan.plan_id == "plan1"
        assert plan.goal == "Find the weather forecast for Paris."
        assert plan.steps == []
        assert plan.current_status == "pending"
        assert isinstance(plan.created_at, float)
        assert plan.updated_at is None
    
    def test_create_with_custom_values(self):
        """Test creating plan with custom values."""
        steps = [
            PlanStep(step_id="step1", description="Search for weather in Paris."),
            PlanStep(step_id="step2", description="Extract forecast information.", dependencies=["step1"])
        ]
        created_at = time.time() - 3600  # 1 hour ago
        updated_at = time.time() - 1800  # 30 minutes ago
        
        plan = Plan(
            plan_id="plan1",
            goal="Find the weather forecast for Paris.",
            steps=steps,
            current_status="in_progress",
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert plan.plan_id == "plan1"
        assert plan.goal == "Find the weather forecast for Paris."
        assert len(plan.steps) == 2
        assert plan.steps[0].step_id == "step1"
        assert plan.steps[1].step_id == "step2"
        assert plan.current_status == "in_progress"
        assert plan.created_at == created_at
        assert plan.updated_at == updated_at


class TestIntentRefinementModels:
    """Tests for intent refinement models."""

    def test_intent_refinement_request(self):
        """Test IntentRefinementRequest model."""
        # With minimum fields
        request1 = IntentRefinementRequest(original_query="What's the weather?")
        assert request1.original_query == "What's the weather?"
        assert request1.conversation_history is None
        assert request1.context_data is None
        
        # With all fields
        conversation_history = [
            {"role": "user", "content": "Hi there"},
            {"role": "assistant", "content": "How can I help?"}
        ]
        context_data = {"location": "New York"}
        
        request2 = IntentRefinementRequest(
            original_query="What's the weather like?",
            conversation_history=conversation_history,
            context_data=context_data
        )
        
        assert request2.original_query == "What's the weather like?"
        assert request2.conversation_history == conversation_history
        assert request2.context_data == context_data

    def test_intent_refinement_response(self):
        """Test IntentRefinementResponse model."""
        # With default values
        response1 = IntentRefinementResponse()
        assert response1.refined_query is None
        assert response1.clarifying_questions is None
        assert response1.is_clear is False
        assert response1.extracted_parameters is None
        
        # With custom values
        clarifying_questions = ["Did you mean the current weather?", "Which location?"]
        extracted_parameters = {"intent": "weather", "location": "New York"}
        
        response2 = IntentRefinementResponse(
            refined_query="What is the weather forecast for New York?",
            clarifying_questions=clarifying_questions,
            is_clear=True,
            extracted_parameters=extracted_parameters
        )
        
        assert response2.refined_query == "What is the weather forecast for New York?"
        assert response2.clarifying_questions == clarifying_questions
        assert response2.is_clear is True
        assert response2.extracted_parameters == extracted_parameters


class TestPromptTemplateV1:
    """Tests for PromptTemplateV1 model."""

    def test_create_with_defaults(self):
        """Test creating template with default values."""
        template = PromptTemplateV1(
            template_id="weather_prompt",
            template_string="What is the weather in {{location}}?"
        )
        
        assert template.template_id == "weather_prompt"
        assert template.version == "1.0"
        assert template.description is None
        assert template.template_string == "What is the weather in {{location}}?"
        assert template.input_variables == []
        assert template.metadata == {}
    
    def test_create_with_custom_values(self):
        """Test creating template with custom values."""
        input_variables = ["location", "date"]
        metadata = {"category": "weather", "usage_count": 42}
        
        template = PromptTemplateV1(
            template_id="weather_prompt",
            version="1.1",
            description="Template for weather inquiries",
            template_string="What will the weather be in {{location}} on {{date}}?",
            input_variables=input_variables,
            metadata=metadata
        )
        
        assert template.template_id == "weather_prompt"
        assert template.version == "1.1"
        assert template.description == "Template for weather inquiries"
        assert template.template_string == "What will the weather be in {{location}} on {{date}}?"
        assert template.input_variables == input_variables
        assert template.metadata == metadata
