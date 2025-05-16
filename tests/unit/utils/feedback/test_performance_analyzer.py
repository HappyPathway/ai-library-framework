"""Tests for the ailf.feedback.performance_analyzer module."""

import pytest
from datetime import datetime
import uuid
from typing import List

from ailf.schemas.feedback import LoggedInteraction
from ailf.feedback.performance_analyzer import PerformanceAnalyzer

@pytest.fixture
def sample_interactions() -> List[LoggedInteraction]:
    """Create a list of sample LoggedInteraction objects for testing."""
    interactions = []
    
    # Create a successful interaction with good feedback
    interactions.append(LoggedInteraction(
        interaction_id=uuid.uuid4(),
        session_id="session_1",
        user_id="user_1",
        timestamp=datetime.utcnow(),
        input_summary="Weather query",
        prompt_template_id="weather_query",
        prompt_template_version="1.0",
        rendered_prompt="Please provide the weather for New York",
        llm_model_used="gpt-4",
        agent_actions=[{"action_type": "weather_lookup", "location": "New York"}],
        user_feedback_score=4.5,  # High score
        tags=["weather", "location", "test"],
        metadata={"location": "New York"}
    ))
    
    # Create another successful interaction
    interactions.append(LoggedInteraction(
        interaction_id=uuid.uuid4(),
        session_id="session_1",
        user_id="user_1",
        timestamp=datetime.utcnow(),
        input_summary="Math question",
        prompt_template_id="math_query",
        prompt_template_version="1.0",
        rendered_prompt="Please calculate 2+2",
        llm_model_used="gpt-4",
        agent_actions=[{"action_type": "calculator", "expression": "2+2"}],
        user_feedback_score=5.0,  # Highest score
        tags=["math", "calculation", "test"],
        metadata={"expression": "2+2"}
    ))
    
    # Create an interaction with an error
    interactions.append(LoggedInteraction(
        interaction_id=uuid.uuid4(),
        session_id="session_1",
        user_id="user_1",
        timestamp=datetime.utcnow(),
        input_summary="Unsupported query",
        prompt_template_id="general_query",
        prompt_template_version="1.0",
        rendered_prompt="Please book me a flight",
        llm_model_used="gpt-4",
        error_message="Flight booking not supported",
        tags=["unsupported", "test"],
        metadata={"request_type": "flight_booking"}
    ))
    
    return interactions

def test_performance_analyzer_initialization():
    """Test that the PerformanceAnalyzer initializes correctly."""
    analyzer = PerformanceAnalyzer()
    assert len(analyzer.interactions_data) == 0
    
    analyzer = PerformanceAnalyzer([])
    assert len(analyzer.interactions_data) == 0

def test_load_interactions(sample_interactions):
    """Test loading interactions into the analyzer."""
    analyzer = PerformanceAnalyzer()
    analyzer.load_interactions(sample_interactions)
    assert len(analyzer.interactions_data) == len(sample_interactions)
    
    # Test loading more interactions
    analyzer.load_interactions(sample_interactions)
    assert len(analyzer.interactions_data) == len(sample_interactions) * 2

def test_analyze_prompt_success(sample_interactions):
    """Test analyzing prompt success."""
    analyzer = PerformanceAnalyzer(sample_interactions)
    results = analyzer.analyze_prompt_success()
    
    # We should have metrics for both prompt templates
    assert "weather_query_v1.0" in results
    assert "math_query_v1.0" in results
    assert "general_query_v1.0" in results
    
    # Check the weather prompt metrics
    weather_stats = results["weather_query_v1.0"]
    assert weather_stats["total_uses"] == 1
    assert weather_stats["successful_outcomes"] == 1
    assert weather_stats["error_count"] == 0
    assert weather_stats["average_feedback_score"] == 4.5
    
    # Check the math prompt metrics
    math_stats = results["math_query_v1.0"]
    assert math_stats["total_uses"] == 1
    assert math_stats["successful_outcomes"] == 1
    assert math_stats["error_count"] == 0
    assert math_stats["average_feedback_score"] == 5.0
    
    # Check the general prompt metrics
    general_stats = results["general_query_v1.0"]
    assert general_stats["total_uses"] == 1
    assert general_stats["successful_outcomes"] == 0  # Should be 0 due to error
    assert general_stats["error_count"] == 1
    assert general_stats["average_feedback_score"] is None  # No feedback provided

def test_find_prompt_correlations(sample_interactions):
    """Test finding prompt correlations."""
    analyzer = PerformanceAnalyzer(sample_interactions)
    results = analyzer.find_prompt_correlations()
    
    # Check that we have tag performance data
    assert "by_tag_performance" in results
    tag_performance = results["by_tag_performance"]
    
    # Check the test tag metrics
    assert "test" in tag_performance
    test_stats = tag_performance["test"]
    assert test_stats["total"] == 3
    assert test_stats["errors"] == 1
    
    # Weather tag should have no errors
    assert "weather" in tag_performance
    weather_stats = tag_performance["weather"]
    assert weather_stats["total"] == 1
    assert weather_stats["errors"] == 0

def test_get_general_metrics(sample_interactions):
    """Test getting general metrics."""
    analyzer = PerformanceAnalyzer(sample_interactions)
    metrics = analyzer.get_general_metrics()
    
    # Check basic metrics
    assert metrics["total_interactions"] == 3
    assert metrics["total_errors"] == 1
    assert metrics["error_rate"] == 1/3
    
    # We have 2 feedback scores with an average of 4.75
    assert metrics["average_feedback_score"] == (4.5 + 5.0) / 2
    
    # Check model usage
    assert metrics["model_usage_counts"]["gpt-4"] == 3
    
    # Check action types
    assert "weather_lookup" in metrics["action_type_counts"]
    assert metrics["action_type_counts"]["weather_lookup"] == 1
    assert "calculator" in metrics["action_type_counts"]
    assert metrics["action_type_counts"]["calculator"] == 1
