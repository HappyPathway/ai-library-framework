"""Tests for the ailf.feedback.adaptive_learning_manager module."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from ailf.feedback.adaptive_learning_manager import AdaptiveLearningManager
from ailf.feedback.performance_analyzer import PerformanceAnalyzer
from ailf.schemas.feedback import LoggedInteraction

class MockPromptLibrary:
    """Mock PromptLibrary for testing."""

    def __init__(self):
        """Initialize the mock prompt library."""
        self.templates = {
            "weather_query": {
                "1.0": "Get weather for {location}",
                "1.1": "What's the current weather in {location}?"
            },
            "math_query": {
                "1.0": "Calculate {expression}"
            }
        }
        self.updates = []  # Track updates made
    
    def get_template(self, template_id: str, version: str = None) -> Dict[str, Any]:
        """Get a template from the library."""
        if template_id not in self.templates:
            return None
        
        if version and version not in self.templates[template_id]:
            return None
        
        version_to_use = version or max(self.templates[template_id].keys())
        template_text = self.templates[template_id][version_to_use]
        
        return {
            "id": template_id,
            "version": version_to_use,
            "text": template_text
        }
    
    def update_template(self, template_id: str, new_text: str, new_version: str = None) -> Dict[str, Any]:
        """Update a template in the library."""
        if template_id not in self.templates:
            self.templates[template_id] = {}
        
        if new_version is None:
            # Generate new version
            if self.templates[template_id]:
                latest = max(float(v) for v in self.templates[template_id].keys())
                new_version = str(latest + 0.1)
            else:
                new_version = "1.0"
        
        self.templates[template_id][new_version] = new_text
        
        # Track this update
        self.updates.append({
            "template_id": template_id,
            "version": new_version,
            "text": new_text
        })
        
        return {
            "id": template_id,
            "version": new_version,
            "text": new_text
        }

@pytest.fixture
def mock_performance_analyzer() -> Mock:
    """Create a mock performance analyzer."""
    analyzer = Mock(spec=PerformanceAnalyzer)
    
    # Mock the analyze_prompt_success method
    analyzer.analyze_prompt_success.return_value = {
        "weather_query_v1.0": {
            "total_uses": 10,
            "successful_outcomes": 7,
            "error_count": 3,
            "average_feedback_score": 3.5
        },
        "math_query_v1.0": {
            "total_uses": 5,
            "successful_outcomes": 5,
            "error_count": 0,
            "average_feedback_score": 4.8
        }
    }
    
    # Mock the find_prompt_correlations method
    analyzer.find_prompt_correlations.return_value = {
        "by_tag_performance": {
            "weather": {"total": 10, "errors": 3, "average_feedback_score": 3.5},
            "math": {"total": 5, "errors": 0, "average_feedback_score": 4.8},
        }
    }
    
    return analyzer

@pytest.fixture
def mock_prompt_library() -> MockPromptLibrary:
    """Create a mock prompt library."""
    return MockPromptLibrary()

def test_adaptive_learning_manager_initialization(mock_performance_analyzer, mock_prompt_library):
    """Test initializing the AdaptiveLearningManager."""
    manager = AdaptiveLearningManager(
        performance_analyzer=mock_performance_analyzer,
        prompt_library=mock_prompt_library
    )
    
    assert manager.performance_analyzer == mock_performance_analyzer
    assert manager.prompt_library == mock_prompt_library

def test_identify_underperforming_prompts(mock_performance_analyzer, mock_prompt_library):
    """Test identifying underperforming prompts."""
    manager = AdaptiveLearningManager(
        performance_analyzer=mock_performance_analyzer,
        prompt_library=mock_prompt_library
    )
    
    # Set thresholds that should identify weather_query as underperforming
    config = {"success_rate_threshold": 0.8, "min_sample_size": 5}
    underperforming = manager.identify_underperforming_prompts(config)
    
    assert len(underperforming) == 1
    assert "weather_query_v1.0" in underperforming
    assert underperforming["weather_query_v1.0"]["success_rate"] == 0.7

def test_suggest_prompt_improvements(mock_performance_analyzer, mock_prompt_library):
    """Test suggesting prompt improvements."""
    manager = AdaptiveLearningManager(
        performance_analyzer=mock_performance_analyzer,
        prompt_library=mock_prompt_library
    )
    
    # Mock the AI engine's suggest_improvements method
    manager.ai_engine = Mock()
    manager.ai_engine.suggest_improvements.return_value = {
        "improved_text": "What is the detailed current weather in {location}?",
        "reasoning": "Adding 'detailed' and using a question format may improve response quality."
    }
    
    # Identify underperforming prompts
    underperforming = {
        "weather_query_v1.0": {
            "template_id": "weather_query",
            "version": "1.0",
            "success_rate": 0.7,
            "error_rate": 0.3,
            "current_text": "Get weather for {location}"
        }
    }
    
    suggestions = manager.suggest_prompt_improvements(underperforming)
    
    assert len(suggestions) == 1
    assert "weather_query" in suggestions
    assert suggestions["weather_query"]["improved_text"] == "What is the detailed current weather in {location}?"
    assert "reasoning" in suggestions["weather_query"]

@patch("ailf.feedback.adaptive_learning_manager.logger")
def test_apply_prompt_improvements(mock_logger, mock_performance_analyzer, mock_prompt_library):
    """Test applying prompt improvements."""
    manager = AdaptiveLearningManager(
        performance_analyzer=mock_performance_analyzer,
        prompt_library=mock_prompt_library
    )
    
    # Set up improvements
    improvements = {
        "weather_query": {
            "improved_text": "What is the detailed current weather in {location}?",
            "reasoning": "Adding 'detailed' and using a question format may improve response quality."
        }
    }
    
    # Apply improvements
    manager.apply_prompt_improvements(improvements)
    
    # Check that the prompt library was updated with a new version
    assert len(mock_prompt_library.updates) == 1
    assert mock_prompt_library.updates[0]["template_id"] == "weather_query"
    assert mock_prompt_library.updates[0]["text"] == "What is the detailed current weather in {location}?"
    
    # Verify the logger was called
    mock_logger.info.assert_called()

@patch("ailf.feedback.adaptive_learning_manager.logger")
def test_run_adaptation_cycle(mock_logger, mock_performance_analyzer, mock_prompt_library):
    """Test running a full adaptation cycle."""
    manager = AdaptiveLearningManager(
        performance_analyzer=mock_performance_analyzer,
        prompt_library=mock_prompt_library
    )
    
    # Mock the AI engine
    manager.ai_engine = Mock()
    manager.ai_engine.suggest_improvements.return_value = {
        "improved_text": "What is the detailed current weather in {location}?",
        "reasoning": "Adding 'detailed' and using a question format may improve response quality."
    }
    
    # Run adaptation cycle with auto-apply enabled
    manager.run_adaptation_cycle(auto_apply=True, min_sample_size=5, success_rate_threshold=0.8)
    
    # Check that underperforming prompts were identified
    mock_performance_analyzer.analyze_prompt_success.assert_called_once()
    
    # Check that improvements were applied
    assert len(mock_prompt_library.updates) == 1
    assert mock_prompt_library.updates[0]["template_id"] == "weather_query"
    
    # Run adaptation cycle with auto-apply disabled
    mock_prompt_library.updates = []  # Reset updates
    manager.run_adaptation_cycle(auto_apply=False, min_sample_size=5, success_rate_threshold=0.8)
    
    # Check that no updates were applied
    assert len(mock_prompt_library.updates) == 0
