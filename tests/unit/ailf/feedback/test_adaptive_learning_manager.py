"""Unit tests for the AdaptiveLearningManager class.

This module tests the functionality of AdaptiveLearningManager, focusing on
its ability to manage the lifecycle of prompt optimizations.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Dict, Any, List, Optional

from ailf.feedback.adaptive_learning_manager import AdaptiveLearningManager
from ailf.cognition.prompt_library import PromptLibrary
from ailf.schemas.prompt_engineering import PromptTemplateV1


class TestAdaptiveLearningManager:
    """Tests for AdaptiveLearningManager class."""
    
    @pytest.fixture
    def mock_performance_analyzer(self):
        """Create a mock performance analyzer."""
        analyzer = Mock()
        analyzer.analyze_prompt_success = Mock(return_value={
            "weather_query": {
                "total_uses": 100,
                "successful_outcomes": 60,
                "error_count": 40,
                "average_feedback_score": 0.3,
                "error_rate": 0.4,  # High error rate
                "success_rate": 0.6
            },
            "product_recommendation": {
                "total_uses": 75,
                "successful_outcomes": 30,
                "error_count": 45,
                "average_feedback_score": 0.1,  # Low feedback score
                "error_rate": 0.6,
                "success_rate": 0.4
            }
        })
        analyzer.get_general_metrics = Mock(return_value={
            "total_interactions": 175,
            "successful_interactions": 90,
            "failed_interactions": 85
        })
        analyzer.find_prompt_correlations = Mock(return_value={})
        
        return analyzer
    
    @pytest.fixture
    def mock_prompt_library(self):
        """Create a mock prompt library."""
        library = Mock(spec=PromptLibrary)
        
        # Create template mocks
        weather_template = Mock(spec=PromptTemplateV1)
        weather_template.template_id = "weather_query"
        weather_template.version = 1
        weather_template.system_prompt = "You are a weather assistant."
        weather_template.user_prompt_template = "What's the weather like in {location} today?"
        weather_template.dict = Mock(return_value={
            "template_id": "weather_query",
            "version": 1,
            "system_prompt": "You are a weather assistant.",
            "user_prompt_template": "What's the weather like in {location} today?"
        })
        
        product_template = Mock(spec=PromptTemplateV1)
        product_template.template_id = "product_recommendation"
        product_template.version = 1
        product_template.system_prompt = "You are a product assistant."
        product_template.user_prompt_template = "Recommend products for {category} that match {preferences}"
        product_template.dict = Mock(return_value={
            "template_id": "product_recommendation", 
            "version": 1,
            "system_prompt": "You are a product assistant.",
            "user_prompt_template": "Recommend products for {category} that match {preferences}"
        })
        
        # Configure library mock to return templates
        library.get_template = Mock(side_effect=lambda tid, version=None: {
            "weather_query": weather_template, 
            "product_recommendation": product_template
        }.get(tid))
        
        # Configure update_template to increment version
        def mock_update_template(template_id, content, version_notes=None):
            template = library.get_template(template_id)
            if template:
                template.version += 1
                # Update template with content
                for key, value in content.items():
                    if hasattr(template, key):
                        setattr(template, key, value)
                return template
            return None
        
        library.update_template = Mock(side_effect=mock_update_template)
        
        return library
    
    @pytest.fixture
    def learning_manager(self, mock_performance_analyzer, mock_prompt_library):
        """Create an AdaptiveLearningManager instance for testing."""
        config = {
            "error_rate_threshold": 0.3,
            "feedback_optimization_threshold": 0.5,
            "auto_optimize_prompts": True
        }
        
        manager = AdaptiveLearningManager(
            performance_analyzer=mock_performance_analyzer,
            prompt_library=mock_prompt_library,
            config=config
        )
        
        # Add a mock AI engine
        manager.ai_engine = AsyncMock()
        manager.ai_engine.generate_text = AsyncMock(return_value="Improved prompt: {placeholder}")
        
        return manager
    
    @pytest.mark.asyncio
    async def test_apply_prompt_optimizations(self, learning_manager, mock_prompt_library):
        """Test the apply_prompt_optimizations method."""
        # Setup pending optimizations
        learning_manager._pending_optimizations = {
            "weather_query": {
                "suggestion": "High error rate (40/100). Review for clarity or robustness.",
                "timestamp": time.time(),
                "metrics": {
                    "error_rate": 0.4,
                    "average_feedback_score": 0.3,
                    "success_rate": 0.6
                },
                "status": "pending"
            },
            "product_recommendation": {
                "suggestion": "Low average feedback score (0.10). Consider rephrasing or simplifying.",
                "timestamp": time.time(),
                "metrics": {
                    "error_rate": 0.6,
                    "average_feedback_score": 0.1,
                    "success_rate": 0.4
                },
                "status": "pending"
            }
        }
        
        # Run the method
        result = await learning_manager.apply_prompt_optimizations()
        
        # Verify that prompt_library.update_template was called for each template
        assert mock_prompt_library.update_template.call_count >= 2, "Should update both templates"
        
        # Verify the method reports success
        assert result["status"] in ["success", "partial"], f"Expected success/partial status, got {result['status']}"
        assert result["applied"] > 0, "Should report applied optimizations"
        
        # Check that the pending optimizations were updated
        assert learning_manager._pending_optimizations["weather_query"]["status"] == "applied"
        assert learning_manager._pending_optimizations["product_recommendation"]["status"] == "applied"
        
        # Check that history was recorded
        optimization_history = learning_manager.get_optimization_history()
        assert len(optimization_history) >= 2, f"Expected at least 2 history entries, got {len(optimization_history)}"
    
    @pytest.mark.asyncio
    async def test_apply_prompt_optimizations_with_ai_engine(self, learning_manager, mock_prompt_library):
        """Test apply_prompt_optimizations using the AI engine."""
        # Enable AI-based improvements
        learning_manager.config["use_ai_for_improvements"] = True
        
        # Setup pending optimizations
        learning_manager._pending_optimizations = {
            "weather_query": {
                "suggestion": "High error rate (40/100). Review for clarity or robustness.",
                "timestamp": time.time(),
                "metrics": {"error_rate": 0.4},
                "status": "pending"
            }
        }
        
        # Mock AI engine to return a specific improved prompt
        improved_prompt = "What is the detailed weather forecast for {location} today? Please include temperature and conditions."
        learning_manager.ai_engine.generate_text = AsyncMock(return_value=improved_prompt)
        
        # Run the method
        result = await learning_manager.apply_prompt_optimizations()
        
        # Verify AI engine was called
        assert learning_manager.ai_engine.generate_text.called, "AI engine should be called for improvements"
        
        # Verify the template was updated with AI-improved content
        update_calls = mock_prompt_library.update_template.call_args_list
        found_weather_update = False
        for call in update_calls:
            args, kwargs = call
            if args[0] == "weather_query" and "user_prompt_template" in args[1]:
                if args[1]["user_prompt_template"] == improved_prompt:
                    found_weather_update = True
                    break
        
        assert found_weather_update, "Should update weather template with AI-generated content"
    
    @pytest.mark.asyncio
    async def test_apply_prompt_optimizations_with_rule_based(self, learning_manager, mock_prompt_library):
        """Test apply_prompt_optimizations using rule-based improvements."""
        # Disable AI-based improvements
        learning_manager.config["use_ai_for_improvements"] = False
        
        # Setup pending optimizations
        learning_manager._pending_optimizations = {
            "product_recommendation": {
                "suggestion": "Low feedback score. Consider rephrasing.",
                "timestamp": time.time(),
                "metrics": {"average_feedback_score": 0.1},
                "status": "pending"
            }
        }
        
        # Run the method
        result = await learning_manager.apply_prompt_optimizations()
        
        # Verify AI engine was NOT called
        assert not learning_manager.ai_engine.generate_text.called, "AI engine should not be called"
        
        # Verify that the rule-based improvement was applied
        update_calls = mock_prompt_library.update_template.call_args_list
        found_product_update = False
        for call in update_calls:
            args, kwargs = call
            if args[0] == "product_recommendation" and "user_prompt_template" in args[1]:
                # The rule-based improvement should add specificity
                if "specific" in args[1]["user_prompt_template"] or "precise" in args[1]["user_prompt_template"]:
                    found_product_update = True
                    break
        
        assert found_product_update, "Should update product template with rule-based content"
    
    @pytest.mark.asyncio
    async def test_apply_prompt_optimizations_max_limit(self, learning_manager):
        """Test apply_prompt_optimizations with a maximum limit."""
        # Setup many pending optimizations
        learning_manager._pending_optimizations = {
            f"template_{i}": {
                "suggestion": f"Suggestion for template_{i}",
                "timestamp": time.time(),
                "metrics": {"error_rate": 0.3 + i/10},
                "status": "pending"
            }
            for i in range(10)
        }
        
        # Run with max_optimizations=3
        result = await learning_manager.apply_prompt_optimizations(max_optimizations=3)
        
        # Should only have processed 3 templates
        assert result["applied"] <= 3, f"Should apply at most 3 optimizations, applied {result['applied']}"
        
        # Should have prioritized templates with higher error rates
        processed_templates = [
            tid for tid, data in learning_manager._pending_optimizations.items()
            if data.get("status") == "applied"
        ]
        # Check if they're among the templates with highest error rates
        high_error_templates = sorted(
            learning_manager._pending_optimizations.keys(),
            key=lambda tid: learning_manager._pending_optimizations[tid]["metrics"].get("error_rate", 0),
            reverse=True
        )[:3]
        
        # At least some of the processed templates should be from the high error ones
        assert any(tid in high_error_templates for tid in processed_templates), \
            "Should prioritize templates with higher error rates"
    
    def test_get_optimization_history(self, learning_manager):
        """Test the get_optimization_history method."""
        # Add some history entries
        learning_manager._optimization_history = [
            {
                "template_id": "weather_query",
                "original_version": 1,
                "new_version": 2,
                "timestamp": time.time() - 100,
                "changes": "Added clarity"
            },
            {
                "template_id": "product_recommendation",
                "original_version": 1,
                "new_version": 2,
                "timestamp": time.time() - 50,
                "changes": "Improved specificity"
            },
            {
                "template_id": "weather_query",
                "original_version": 2,
                "new_version": 3,
                "timestamp": time.time(),
                "changes": "Further improvements"
            }
        ]
        
        # Get full history
        full_history = learning_manager.get_optimization_history()
        assert len(full_history) == 3, "Should return all history entries"
        
        # Get filtered history for weather_query
        weather_history = learning_manager.get_optimization_history("weather_query")
        assert len(weather_history) == 2, "Should return only weather_query entries"
        assert all(entry["template_id"] == "weather_query" for entry in weather_history), \
            "All entries should be for weather_query"
    
    def test_get_pending_optimizations(self, learning_manager):
        """Test the get_pending_optimizations method."""
        # Set up mixed pending optimizations
        learning_manager._pending_optimizations = {
            "template_1": {"status": "pending", "metrics": {"error_rate": 0.4}},
            "template_2": {"status": "applied", "metrics": {"error_rate": 0.5}},
            "template_3": {"status": "pending", "metrics": {"error_rate": 0.6}},
            "template_4": {"status": "skipped", "metrics": {"error_rate": 0.3}}
        }
        
        # Get pending optimizations
        pending = learning_manager.get_pending_optimizations()
        
        # Should only have templates with status="pending"
        assert len(pending) == 2, f"Should have 2 pending optimizations, got {len(pending)}"
        assert "template_1" in pending, "template_1 should be in pending"
        assert "template_3" in pending, "template_3 should be in pending"
        assert "template_2" not in pending, "template_2 should not be in pending (applied)"
        assert "template_4" not in pending, "template_4 should not be in pending (skipped)"
