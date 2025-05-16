"""Tests for reflection engine.

This module contains tests for the ReflectionEngine class that processes short-term memory 
to extract insights and store them in long-term memory.
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from ailf.memory.reflection_engine import ReflectionEngine, ExtractedInsights
from ailf.schemas.memory import MemoryItem, UserProfile, KnowledgeFact, MemoryType


class TestReflectionEngine:
    """Tests for the ReflectionEngine class."""

    @pytest.fixture
    def mock_ai_engine(self):
        """Create a mock AI engine."""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_short_term_memory(self):
        """Create a mock short-term memory store."""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_long_term_memory(self):
        """Create a mock long-term memory store."""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def reflection_engine(self, mock_ai_engine, mock_short_term_memory, mock_long_term_memory):
        """Create a ReflectionEngine instance with mock dependencies."""
        return ReflectionEngine(
            ai_engine=mock_ai_engine,
            short_term_memory=mock_short_term_memory,
            long_term_memory=mock_long_term_memory
        )

    @pytest.fixture
    def test_memory_item(self):
        """Create a test memory item."""
        return MemoryItem(
            id="test_item_1",
            type=MemoryType.USER_INPUT,
            content="I prefer dark mode and interested in Python programming",
            metadata={"user_id": "test_user_1"}
        )

    @pytest.mark.asyncio
    async def test_perform_reflection_on_item(self, reflection_engine, test_memory_item, mock_ai_engine):
        """Test performing reflection on a memory item."""
        # Setup mock AI engine to return insights
        mock_ai_engine.generate_text.return_value = """
        {
            "user_preferences": [
                {"preference": "interface", "value": "dark mode"},
                {"preference": "programming_languages", "value": "Python"}
            ],
            "knowledge_facts": [
                {"fact": "User is interested in Python programming", "confidence": 0.9}
            ]
        }
        """
        
        # Perform reflection
        insights = await reflection_engine.perform_reflection_on_item(test_memory_item)
        
        # Check AI engine was called with appropriate prompt
        mock_ai_engine.generate_text.assert_called_once()
        prompt = mock_ai_engine.generate_text.call_args[0][0]
        assert "test_item_1" in prompt
        assert "I prefer dark mode and interested in Python programming" in prompt
        
        # Check extracted insights
        assert isinstance(insights, ExtractedInsights)
        assert len(insights.user_preferences) == 2
        assert insights.user_preferences[0]["preference"] == "interface"
        assert insights.user_preferences[0]["value"] == "dark mode"
        assert len(insights.knowledge_facts) == 1
        assert insights.knowledge_facts[0]["fact"] == "User is interested in Python programming"
        assert insights.knowledge_facts[0]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_ai_engine_error_handling(self, reflection_engine, test_memory_item, mock_ai_engine):
        """Test handling of AI engine errors during reflection."""
        # Setup mock AI engine to raise an exception
        mock_ai_engine.generate_text.side_effect = Exception("API error")
        
        # Perform reflection, which should handle the error gracefully
        insights = await reflection_engine.perform_reflection_on_item(test_memory_item)
        
        # Check that empty insights are returned on error
        assert isinstance(insights, ExtractedInsights)
        assert len(insights.user_preferences) == 0
        assert len(insights.knowledge_facts) == 0

    @pytest.mark.asyncio
    async def test_update_user_profile_existing(self, reflection_engine, mock_long_term_memory):
        """Test updating an existing user profile."""
        # Setup mock to return an existing profile
        existing_profile = UserProfile(
            user_id="user1",
            preferences={"theme": "light"}
        )
        mock_long_term_memory.retrieve_item.return_value = existing_profile
        
        # Define new preferences to add
        new_preferences = [
            {"preference": "theme", "value": "dark"},
            {"preference": "language", "value": "Python"}
        ]
        
        # Update the profile
        await reflection_engine.update_user_profile("user1", new_preferences)
        
        # Check that the profile was retrieved
        mock_long_term_memory.retrieve_item.assert_called_once_with(UserProfile, "user1")
        
        # Check that store_item was called with updated profile
        mock_long_term_memory.store_item.assert_called_once()
        updated_profile = mock_long_term_memory.store_item.call_args[0][0]
        assert updated_profile.user_id == "user1"
        assert updated_profile.preferences["theme"] == "dark"  # Should be updated
        assert updated_profile.preferences["language"] == "Python"  # Should be added

    @pytest.mark.asyncio
    async def test_update_user_profile_new(self, reflection_engine, mock_long_term_memory):
        """Test creating a new user profile if none exists."""
        # Setup mock to return None (no existing profile)
        mock_long_term_memory.retrieve_item.return_value = None
        
        # Define preferences for the new profile
        new_preferences = [
            {"preference": "theme", "value": "dark"},
            {"preference": "notifications", "value": "enabled"}
        ]
        
        # Update/create the profile
        await reflection_engine.update_user_profile("new_user", new_preferences)
        
        # Check that retrieve was attempted
        mock_long_term_memory.retrieve_item.assert_called_once_with(UserProfile, "new_user")
        
        # Check that store_item was called with a new profile
        mock_long_term_memory.store_item.assert_called_once()
        new_profile = mock_long_term_memory.store_item.call_args[0][0]
        assert new_profile.user_id == "new_user"
        assert new_profile.preferences["theme"] == "dark"
        assert new_profile.preferences["notifications"] == "enabled"

    @pytest.mark.asyncio
    async def test_store_knowledge_facts(self, reflection_engine, mock_long_term_memory):
        """Test storing knowledge facts extracted during reflection."""
        # Define facts to store
        facts = [
            {"fact": "Python is a programming language", "confidence": 0.95},
            {"fact": "The user prefers dark mode", "confidence": 0.8}
        ]
        
        # Store the facts
        fact_ids = await reflection_engine.store_knowledge_facts("user1", facts)
        
        # Check that store_item was called twice
        assert mock_long_term_memory.store_item.call_count == 2
        
        # Check that two fact IDs were returned
        assert len(fact_ids) == 2
        
        # Check that the stored facts have correct data
        stored_facts = [call_args[0][0] for call_args in mock_long_term_memory.store_item.call_args_list]
        
        for fact in stored_facts:
            assert isinstance(fact, KnowledgeFact)
            assert fact.type == MemoryType.OTHER
            assert "Python" in fact.content or "dark mode" in fact.content
            assert "user1" in fact.metadata.get("user_id", "")
            assert fact.confidence in [0.95, 0.8]

    @pytest.mark.asyncio
    async def test_reflect_on_recent_memory(self, reflection_engine, mock_short_term_memory, mock_ai_engine, test_memory_item):
        """Test reflecting on recent memory items."""
        # Setup mock to return test items
        mock_short_term_memory.get_recent_items.return_value = [test_memory_item]
        
        # Setup mock AI engine
        mock_ai_engine.generate_text.return_value = """
        {
            "user_preferences": [
                {"preference": "theme", "value": "dark mode"}
            ],
            "knowledge_facts": [
                {"fact": "User uses Python", "confidence": 0.9}
            ]
        }
        """
        
        # Mock the update_user_profile and store_knowledge_facts methods
        with patch.object(reflection_engine, 'update_user_profile') as mock_update_profile, \
             patch.object(reflection_engine, 'store_knowledge_facts') as mock_store_facts:
            
            # Reflect on recent memory
            await reflection_engine.reflect_on_recent_memory("test_user_1")
            
            # Check that recent items were retrieved
            mock_short_term_memory.get_recent_items.assert_called_once()
            
            # Check that reflection was performed
            mock_ai_engine.generate_text.assert_called_once()
            
            # Check that insights were processed
            mock_update_profile.assert_called_once()
            mock_store_facts.assert_called_once()
            
            # Check that update_user_profile was called with correct args
            preferences_arg = mock_update_profile.call_args[0][1]
            assert len(preferences_arg) == 1
            assert preferences_arg[0]["preference"] == "theme"
            assert preferences_arg[0]["value"] == "dark mode"
            
            # Check that store_knowledge_facts was called with correct args
            facts_arg = mock_store_facts.call_args[0][1]
            assert len(facts_arg) == 1
            assert facts_arg[0]["fact"] == "User uses Python"
            assert facts_arg[0]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_reflect_on_recent_memory_with_limit(self, reflection_engine, mock_short_term_memory):
        """Test reflecting on recent memory with a specific limit."""
        # Call reflect_on_recent_memory with a limit
        await reflection_engine.reflect_on_recent_memory("test_user_1", limit=5)
        
        # Check that get_recent_items was called with the specified limit
        mock_short_term_memory.get_recent_items.assert_called_once_with(5)
