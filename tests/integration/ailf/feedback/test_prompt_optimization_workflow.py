"""Integration test for the end-to-end prompt optimization workflow.

This test verifies that the AdaptiveLearningManager can properly analyze performance data,
identify optimizations, and automatically update templates in the PromptLibrary.
"""

import os
import json
import pytest
import tempfile
import time
import uuid
import asyncio
from typing import Dict, List, Any, Optional

# Import AILF components
from ailf.feedback.adaptive_learning_manager import AdaptiveLearningManager
from ailf.feedback.performance_analyzer import PerformanceAnalyzer
from ailf.cognition.prompt_library import PromptLibrary
from ailf.schemas.prompt_engineering import PromptTemplateV1, PromptLibraryConfig


class MockPerformanceAnalyzer(PerformanceAnalyzer):
    """A mock performance analyzer for testing purposes."""
    
    def __init__(self, mock_data: Dict[str, Any] = None):
        """
        Initialize the mock performance analyzer.
        
        :param mock_data: Dictionary of mock performance data
        """
        self.mock_data = mock_data or {}
        
    def analyze_prompt_success(self) -> Dict[str, Dict[str, Any]]:
        """Return mock prompt analysis data."""
        return self.mock_data.get("prompt_analysis", {})
        
    def get_general_metrics(self) -> Dict[str, Any]:
        """Return mock general metrics."""
        return self.mock_data.get("general_metrics", {})
        
    def find_prompt_correlations(self) -> Dict[str, Any]:
        """Return mock correlations."""
        return self.mock_data.get("correlations", {})


@pytest.fixture
def prompt_library_path() -> str:
    """Create a temporary directory for prompt templates."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def prompt_library(prompt_library_path) -> PromptLibrary:
    """Create a prompt library with initial templates."""
    # Set up initial templates
    templates = [
        {
            "template_id": "weather_query",
            "version": 1,
            "description": "A template for querying weather information",
            "system_prompt": "You are a helpful weather assistant.",
            "user_prompt_template": "What's the weather like in {location} today?",
            "placeholders": ["location"],
            "tags": ["weather", "query"],
            "created_at": time.time()
        },
        {
            "template_id": "news_summary",
            "version": 1,
            "description": "A template for summarizing news articles",
            "system_prompt": "You are a helpful news summarizer.",
            "user_prompt_template": "Summarize this news article: {article}",
            "placeholders": ["article"],
            "tags": ["news", "summary"],
            "created_at": time.time()
        },
        {
            "template_id": "product_recommendation",
            "version": 1,
            "description": "A template for recommending products",
            "system_prompt": "You are a product recommendation assistant.",
            "user_prompt_template": "Recommend products for {category} that match {preferences}",
            "placeholders": ["category", "preferences"],
            "tags": ["products", "recommendations"],
            "created_at": time.time()
        }
    ]
    
    # Create template files
    for template_data in templates:
        filename = f"{template_data['template_id']}_v{template_data['version']}.json"
        filepath = os.path.join(prompt_library_path, filename)
        with open(filepath, 'w') as f:
            json.dump(template_data, f, indent=2)
    
    # Initialize the prompt library
    config = PromptLibraryConfig(
        library_path=prompt_library_path,
        default_prompt_id="weather_query",
        auto_save=True
    )
    
    return PromptLibrary(config)


@pytest.fixture
def performance_analyzer() -> MockPerformanceAnalyzer:
    """Create a mock performance analyzer with sample data."""
    mock_data = {
        "prompt_analysis": {
            "weather_query": {
                "total_uses": 100,
                "successful_outcomes": 60,
                "error_count": 40,
                "average_feedback_score": 0.3,
                "error_rate": 0.4,  # 40% error rate, high enough to trigger optimization
                "success_rate": 0.6
            },
            "news_summary": {
                "total_uses": 50,
                "successful_outcomes": 45,
                "error_count": 5,
                "average_feedback_score": 0.8,
                "error_rate": 0.1,
                "success_rate": 0.9
            },
            "product_recommendation": {
                "total_uses": 75,
                "successful_outcomes": 30,
                "error_count": 45,
                "average_feedback_score": 0.1,  # Low feedback score, should trigger optimization
                "error_rate": 0.6,
                "success_rate": 0.4
            }
        },
        "general_metrics": {
            "total_interactions": 225,
            "successful_interactions": 135,
            "failed_interactions": 90,
            "average_response_time": 2.3
        },
        "correlations": {
            "prompt_success_vs_length": 0.7
        }
    }
    return MockPerformanceAnalyzer(mock_data)


@pytest.fixture
def adaptive_learning_manager(performance_analyzer, prompt_library) -> AdaptiveLearningManager:
    """Create an AdaptiveLearningManager instance for testing."""
    config = {
        "error_rate_threshold": 0.3,
        "feedback_optimization_threshold": 0.5,
        "auto_optimize_prompts": True,  # Enable auto-optimization
        "feedback_suggestion_threshold": 0.4
    }
    
    return AdaptiveLearningManager(
        performance_analyzer=performance_analyzer,
        prompt_library=prompt_library,
        config=config
    )


# Mock AI Engine for testing
class MockAIEngine:
    """A simple mock AI engine that returns predefined responses."""
    
    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """Generate mock text based on input."""
        # Return a predictable response with some words from the original prompt
        if "weather" in user_prompt:
            return "What's the current weather forecast for {location}? Please include temperature and conditions."
        elif "news" in user_prompt:
            return "Please provide a concise summary of this news article: {article}"
        elif "product" in user_prompt:
            return "Based on your preferences, what specific {category} products would you recommend that match {preferences}? Please be detailed."
        else:
            return "Improved prompt: {original}"


@pytest.mark.asyncio
async def test_end_to_end_prompt_optimization(
    adaptive_learning_manager,
    prompt_library,
    performance_analyzer
):
    """
    Test the end-to-end workflow for automated prompt optimization.
    
    This test verifies that:
    1. AdaptiveLearningManager can identify underperforming prompts
    2. It can suggest optimizations based on performance data
    3. It can automatically apply these optimizations to the PromptLibrary
    4. The PromptLibrary correctly stores and versions the updated templates
    """
    # Add a mock AI engine to the manager
    adaptive_learning_manager.ai_engine = MockAIEngine()
    
    # Step 1: Record the initial state of templates
    initial_templates = {}
    for template_id in prompt_library.list_template_ids():
        initial_templates[template_id] = prompt_library.get_template(template_id)
    
    assert len(initial_templates) == 3, "Expected 3 initial templates"
    
    # Verify initial versions are all 1
    for template_id, template in initial_templates.items():
        assert template.version == 1, f"Expected version 1 for {template_id}, got {template.version}"
    
    # Step 2: Run the learning cycle with auto-optimize=True
    cycle_results = await adaptive_learning_manager.run_learning_cycle(auto_optimize=True)
    
    # Step 3: Verify that underperforming templates were identified
    assert "weather_query" in cycle_results["insights"]["prompt_analysis"]
    assert "product_recommendation" in cycle_results["insights"]["prompt_analysis"]
    
    # Allow a short delay for async operations to complete
    await asyncio.sleep(0.5)
    
    # Step 4: Verify that templates were updated in the library
    updated_templates = {}
    for template_id in prompt_library.list_template_ids():
        updated_templates[template_id] = prompt_library.get_template(template_id)
    
    # Check that the underperforming templates have been updated
    # Weather query had high error rate (0.4 > threshold of 0.3)
    weather_template = updated_templates["weather_query"]
    assert weather_template.version > 1, f"Expected weather_query version > 1, got {weather_template.version}"
    assert weather_template.updated_by_component == "AdaptiveLearningManager", "Template should be updated by AdaptiveLearningManager"
    
    # Product recommendation had low feedback score (0.1 < threshold of 0.5)
    product_template = updated_templates["product_recommendation"]
    assert product_template.version > 1, f"Expected product_recommendation version > 1, got {product_template.version}"
    
    # News summary was performing well, should not have been updated
    news_template = updated_templates["news_summary"]
    assert news_template.version == 1, f"Expected news_summary version to remain 1, got {news_template.version}"
    
    # Step 5: Verify the optimization history in the manager
    optimization_history = adaptive_learning_manager.get_optimization_history()
    assert len(optimization_history) >= 2, f"Expected at least 2 optimization records, got {len(optimization_history)}"
    
    # Verify specific template optimizations
    weather_optimizations = adaptive_learning_manager.get_optimization_history("weather_query")
    assert len(weather_optimizations) > 0, "Expected optimization history for weather_query"
    
    product_optimizations = adaptive_learning_manager.get_optimization_history("product_recommendation")
    assert len(product_optimizations) > 0, "Expected optimization history for product_recommendation"
    
    # Step 6: Verify that version history is maintained in the prompt library
    weather_history = prompt_library.get_version_history("weather_query")
    assert len(weather_history) >= 2, f"Expected at least 2 versions for weather_query, got {len(weather_history)}"
    
    # The highest version should be the current template
    highest_weather_version = max(weather_history, key=lambda t: t.version)
    assert highest_weather_version.version == weather_template.version, "Highest version should match current template"
    
    # Step 7: Run another cycle and verify the system continues to monitor and optimize
    # Setup mock analyzer with new data showing one template still needs improvement
    performance_analyzer.mock_data["prompt_analysis"]["weather_query"]["error_rate"] = 0.5  # Still high error rate
    performance_analyzer.mock_data["prompt_analysis"]["product_recommendation"]["error_rate"] = 0.15  # Improved
    
    # Run another cycle
    second_cycle_results = await adaptive_learning_manager.run_learning_cycle(auto_optimize=True)
    
    # Allow a short delay for async operations to complete
    await asyncio.sleep(0.5)
    
    # Verify weather template was updated again
    latest_weather_template = prompt_library.get_template("weather_query")
    assert latest_weather_template.version > weather_template.version, "Weather template should be optimized again"
    
    # Verify product template was not updated again (now performing better)
    latest_product_template = prompt_library.get_template("product_recommendation")
    assert latest_product_template.version == product_template.version, "Product template should not be optimized again"


@pytest.mark.asyncio
async def test_apply_prompt_optimizations_method(
    adaptive_learning_manager,
    prompt_library,
    performance_analyzer
):
    """
    Test specifically the apply_prompt_optimizations method.
    
    This test focuses on:
    1. Directly calling apply_prompt_optimizations without going through run_learning_cycle
    2. Verifying it correctly processes pending optimizations
    3. Checking that templates are properly updated in the library
    """
    # Step 1: Generate insights to populate pending optimizations
    insights = {
        "prompt_analysis": performance_analyzer.analyze_prompt_success()
    }
    
    # Populate the pending optimizations queue
    await adaptive_learning_manager.apply_insights_to_behavior(insights)
    
    # Verify pending optimizations were identified
    pending = adaptive_learning_manager.get_pending_optimizations()
    assert len(pending) > 0, "Expected pending optimizations"
    
    # Disable auto-optimize to prevent automatic application
    adaptive_learning_manager.config["auto_optimize_prompts"] = False
    
    # Add mock AI engine for improved suggestions
    adaptive_learning_manager.ai_engine = MockAIEngine()
    
    # Step 2: Record initial template states
    initial_templates = {}
    for template_id in prompt_library.list_template_ids():
        initial_templates[template_id] = prompt_library.get_template(template_id)
    
    # Step 3: Manually call apply_prompt_optimizations
    optimization_results = await adaptive_learning_manager.apply_prompt_optimizations()
    
    # Step 4: Verify results
    assert optimization_results["applied"] > 0, f"Expected applied optimizations, got {optimization_results}"
    
    # Allow a short delay for async operations to complete
    await asyncio.sleep(0.5)
    
    # Step 5: Check that templates were updated
    for template_id in prompt_library.list_template_ids():
        template = prompt_library.get_template(template_id)
        initial = initial_templates.get(template_id)
        
        if template_id in ["weather_query", "product_recommendation"]:
            # These should have been updated
            assert template.version > initial.version, f"Expected {template_id} version > {initial.version}, got {template.version}"
            assert hasattr(template, "updated_by_component") and template.updated_by_component == "AdaptiveLearningManager", \
                f"Template should have updated_by_component attribute set to AdaptiveLearningManager"
        else:
            # These should remain unchanged
            assert template.version == initial.version, f"Expected {template_id} to remain at version {initial.version}, got {template.version}"
