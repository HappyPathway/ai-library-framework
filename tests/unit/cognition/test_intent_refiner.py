"""Tests for intent refiner.

This module contains tests for the IntentRefiner class in ailf.cognition.intent_refiner.
"""
import pytest
from unittest.mock import AsyncMock

from ailf.cognition.intent_refiner import IntentRefiner
from ailf.schemas.cognition import IntentRefinementRequest, IntentRefinementResponse


class TestIntentRefiner:
    """Tests for IntentRefiner."""

    @pytest.fixture
    def mock_ai_engine(self):
        """Create a mock AI engine."""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def intent_refiner(self, mock_ai_engine):
        """Create an IntentRefiner instance with a mock AI engine."""
        return IntentRefiner(ai_engine=mock_ai_engine)

    @pytest.mark.asyncio
    async def test_refine_intent_basic_query(self, intent_refiner, mock_ai_engine):
        """Test refining a basic query."""
        # Configure mock response
        mock_response = IntentRefinementResponse(
            is_clear=True,
            refined_query="User wants to check the weather in New York.",
            extracted_parameters={"intent": "check_weather", "location": "New York"}
        )
        mock_ai_engine.analyze.return_value = mock_response
        
        # Call the method under test
        request = IntentRefinementRequest(original_query="What's the weather in New York?")
        result = await intent_refiner.refine_intent(request)
        
        # Verify the AI engine was called correctly
        mock_ai_engine.analyze.assert_called_once()
        args, kwargs = mock_ai_engine.analyze.call_args
        assert request.original_query in kwargs.get('content', '')
        assert kwargs.get('output_schema') == IntentRefinementResponse
        assert kwargs.get('system_prompt') is not None
        
        # Verify the response was passed through correctly
        assert result is mock_response
        assert result.is_clear is True
        assert result.refined_query == "User wants to check the weather in New York."
        assert result.extracted_parameters == {"intent": "check_weather", "location": "New York"}

    @pytest.mark.asyncio
    async def test_refine_intent_with_conversation_history(self, intent_refiner, mock_ai_engine):
        """Test refining a query with conversation history."""
        # Configure mock response
        mock_response = IntentRefinementResponse(
            is_clear=True,
            refined_query="User wants to book a flight to Paris on Monday.",
            extracted_parameters={"intent": "book_flight", "destination": "Paris", "day": "Monday"}
        )
        mock_ai_engine.analyze.return_value = mock_response
        
        # Call the method under test with conversation history
        conversation_history = [
            {"role": "assistant", "content": "Do you have a specific day in mind for your trip to Paris?"},
            {"role": "user", "content": "I'd prefer Monday."}
        ]
        request = IntentRefinementRequest(
            original_query="Monday works for me.",
            conversation_history=conversation_history
        )
        result = await intent_refiner.refine_intent(request)
        
        # Verify conversation history was included in the prompt
        args, kwargs = mock_ai_engine.analyze.call_args
        content = kwargs.get('content', '')
        assert "Monday works for me." in content
        assert "assistant: Do you have a specific day in mind" in content
        assert "user: I'd prefer Monday" in content
        
        # Verify the response
        assert result.is_clear is True
        assert "Paris" in result.refined_query
        assert "Monday" in result.refined_query

    @pytest.mark.asyncio
    async def test_refine_intent_with_context_data(self, intent_refiner, mock_ai_engine):
        """Test refining a query with additional context data."""
        # Configure mock response
        mock_response = IntentRefinementResponse(
            is_clear=True,
            refined_query="User wants to get recommended restaurants in Seattle.",
            extracted_parameters={"intent": "get_recommendations", "category": "restaurants", "location": "Seattle"}
        )
        mock_ai_engine.analyze.return_value = mock_response
        
        # Call the method under test with context data
        context_data = {"user_location": "Seattle", "time": "evening", "preferences": ["Italian", "Thai"]}
        request = IntentRefinementRequest(
            original_query="What are some good restaurants around here?",
            context_data=context_data
        )
        result = await intent_refiner.refine_intent(request)
        
        # Verify context data was included in the prompt
        args, kwargs = mock_ai_engine.analyze.call_args
        content = kwargs.get('content', '')
        assert "user_location: Seattle" in content
        assert "time: evening" in content
        assert "preferences:" in content and "Italian" in content and "Thai" in content
        
        # Verify the response
        assert "Seattle" in result.refined_query
        assert "restaurants" in result.refined_query

    @pytest.mark.asyncio
    async def test_refine_ambiguous_query(self, intent_refiner, mock_ai_engine):
        """Test refining an ambiguous query that needs clarification."""
        # Configure mock response with clarifying questions
        mock_response = IntentRefinementResponse(
            is_clear=False,
            clarifying_questions=[
                "What type of weather information are you looking for (forecast, current conditions, etc.)?",
                "For which location do you need the weather information?"
            ]
        )
        mock_ai_engine.analyze.return_value = mock_response
        
        # Call the method under test with an ambiguous query
        request = IntentRefinementRequest(original_query="Tell me about the weather.")
        result = await intent_refiner.refine_intent(request)
        
        # Verify the response
        assert result.is_clear is False
        assert len(result.clarifying_questions) == 2
        assert "which location" in result.clarifying_questions[1].lower()
        assert result.refined_query is None

    @pytest.mark.asyncio
    async def test_handle_invalid_ai_response(self, intent_refiner, mock_ai_engine):
        """Test handling an invalid response from the AI engine."""
        # Configure mock to return an invalid response type
        mock_ai_engine.analyze.return_value = "This is not an IntentRefinementResponse"
        
        # Call the method under test
        request = IntentRefinementRequest(original_query="Hello there")
        result = await intent_refiner.refine_intent(request)
        
        # Verify fallback behavior
        assert isinstance(result, IntentRefinementResponse)
        assert result.is_clear is False
        assert len(result.clarifying_questions) == 1
        assert "rephrase" in result.clarifying_questions[0].lower()

    @pytest.mark.asyncio
    async def test_extracted_parameters(self, intent_refiner, mock_ai_engine):
        """Test handling complex extracted parameters."""
        # Configure mock response with structured parameters
        mock_response = IntentRefinementResponse(
            is_clear=True,
            refined_query="User wants to book a flight from New York to London on December 15, returning December 22.",
            extracted_parameters={
                "intent": "book_flight",
                "departure_location": "New York",
                "destination": "London",
                "departure_date": "2023-12-15",
                "return_date": "2023-12-22",
                "trip_type": "round-trip"
            }
        )
        mock_ai_engine.analyze.return_value = mock_response
        
        # Call the method under test
        request = IntentRefinementRequest(
            original_query="I need a round-trip flight from New York to London, leaving December 15 and returning December 22."
        )
        result = await intent_refiner.refine_intent(request)
        
        # Verify extracted parameters
        assert result.extracted_parameters is not None
        assert result.extracted_parameters["departure_location"] == "New York"
        assert result.extracted_parameters["destination"] == "London"
        assert result.extracted_parameters["departure_date"] == "2023-12-15"
        assert result.extracted_parameters["trip_type"] == "round-trip"
