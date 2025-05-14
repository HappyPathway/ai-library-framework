"""Tests for reflection engine.

This module contains tests for the ReflectionEngine class that processes short-term memory 
to extract insights and store them in long-term memory.
"""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from ailf.memory.reflection_engine import ReflectionEngine, ExtractedInsights
from ailf.schemas.memory import MemoryItem, UserProfile, KnowledgeFact


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
            item_id="test_item_1",
            data="I prefer dark mode and interested in Python programming",
            metadata={"user_id": "test_user_1"}
        )

    @pytest.mark.asyncio
    async def test_perform_reflection_on_item(
        self, reflection_engine, test_memory_item, 
        mock_ai_engine, mock_long_term_memory
    ):
        """Test performing reflection on a single memory item."""
        # Configure AI engine mock to return extracted insights
        extracted_insights = ExtractedInsights(
            user_id="test_user_1",
            extracted_preferences={"theme": "dark", "interests": "programming"},
            extracted_facts=["Python is a programming language"]
        )
        mock_ai_engine.analyze.return_value = extracted_insights
        
        # Call the method under test
        await reflection_engine.perform_reflection_on_item(test_memory_item)
        
        # Verify AI engine was called correctly
        mock_ai_engine.analyze.assert_called_once()
        # The call should include the memory item data and ExtractedInsights as output schema
        args, kwargs = mock_ai_engine.analyze.call_args
        assert kwargs.get('content') == str(test_memory_item.data)
        assert kwargs.get('output_schema') == ExtractedInsights
        assert "user_id" in kwargs.get('system_prompt', '')
        
        # Verify user profile was updated
        mock_long_term_memory.retrieve_item.assert_called_with(UserProfile, "test_user_1")
        mock_long_term_memory.store_item.assert_any_call(
            # Check that some UserProfile object was stored
            pytest.emu_any_instance_of(UserProfile)
        )
        
        # Verify knowledge fact was stored
        knowledge_fact_call = False
        for call in mock_long_term_memory.store_item.call_args_list:
            args, _ = call
            if isinstance(args[0], KnowledgeFact):
                knowledge_fact_call = True
                assert args[0].content == "Python is a programming language"
                assert "reflection_engine" in args[0].tags
        
        assert knowledge_fact_call, "No KnowledgeFact was stored"

    @pytest.mark.asyncio
    async def test_ai_engine_error_handling(
        self, reflection_engine, test_memory_item, mock_ai_engine
    ):
        """Test handling of AI engine errors."""
        # Configure AI engine to raise an exception
        mock_ai_engine.analyze.side_effect = Exception("AI engine error")
        
        # Call the method under test - should not propagate the exception
        await reflection_engine.perform_reflection_on_item(test_memory_item)
        
        # Verify AI engine was called
        mock_ai_engine.analyze.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_profile_existing(self, reflection_engine, mock_long_term_memory):
        """Test updating an existing user profile."""
        # Create a mock existing profile
        user_id = "test_user"
        existing_profile = UserProfile(
            user_id=user_id,
            preferences={"theme": "light"}
        )
        
        # Configure mock to return the existing profile
        mock_long_term_memory.retrieve_item.return_value = existing_profile
        
        # Call the method under test
        new_preferences = {"theme": "dark", "notifications": "enabled"}
        await reflection_engine._update_user_profile(user_id, new_preferences)
        
        # Verify profile was retrieved and then updated
        mock_long_term_memory.retrieve_item.assert_called_once_with(UserProfile, user_id)
        
        # Verify the store_item call has the updated profile
        mock_long_term_memory.store_item.assert_called_once()
        stored_profile = mock_long_term_memory.store_item.call_args[0][0]
        
        assert stored_profile.user_id == user_id
        # Should merge the preferences
        assert stored_profile.preferences == {"theme": "dark", "notifications": "enabled"}

    @pytest.mark.asyncio
    async def test_update_user_profile_new(self, reflection_engine, mock_long_term_memory):
        """Test creating a new user profile when none exists."""
        # Configure mock to return None (no existing profile)
        mock_long_term_memory.retrieve_item.return_value = None
        
        # Call the method under test
        user_id = "new_user"
        preferences = {"language": "en-US"}
        await reflection_engine._update_user_profile(user_id, preferences)
        
        # Verify a new profile was stored
        mock_long_term_memory.store_item.assert_called_once()
        stored_profile = mock_long_term_memory.store_item.call_args[0][0]
        
        assert stored_profile.user_id == user_id
        assert stored_profile.preferences == preferences

    @pytest.mark.asyncio
    async def test_store_knowledge_facts(self, reflection_engine, mock_long_term_memory):
        """Test storing multiple knowledge facts."""
        facts = [
            "The Earth orbits the Sun.",
            "Water boils at 100 degrees Celsius at sea level."
        ]
        source = "Test source"
        
        # Call the method under test
        await reflection_engine._store_knowledge_facts(facts, source)
        
        # Verify two facts were stored
        assert mock_long_term_memory.store_item.call_count == 2
        
        # Check content of stored facts
        fact1 = mock_long_term_memory.store_item.call_args_list[0][0][0]
        fact2 = mock_long_term_memory.store_item.call_args_list[1][0][0]
        
        assert isinstance(fact1, KnowledgeFact)
        assert isinstance(fact2, KnowledgeFact)
        
        # Check that the content matches one of the input facts
        fact1_content = fact1.content
        fact2_content = fact2.content
        
        assert fact1_content in facts
        assert fact2_content in facts
        assert fact1_content != fact2_content  # Ensure they're different facts
        
        # Verify other fields
        for fact in [fact1, fact2]:
            assert fact.source == source
            assert "reflection_engine" in fact.tags
            assert "extracted_fact" in fact.tags

    @pytest.mark.asyncio
    async def test_reflect_on_recent_memory(
        self, reflection_engine, mock_short_term_memory, test_memory_item
    ):
        """Test reflection on recent memory items."""
        # Configure mock to return item IDs and items
        item_ids = ["item1", "item2"]
        mock_short_term_memory.list_items.return_value = item_ids
        
        # Configure get_item to return our test item for either ID
        mock_short_term_memory.get_item.return_value = test_memory_item
        
        # Create a spy on perform_reflection_on_item method
        with patch.object(
            reflection_engine, 'perform_reflection_on_item', 
            wraps=reflection_engine.perform_reflection_on_item
        ) as mocked_method:
            # Call the method under test
            await reflection_engine.reflect_on_recent_memory(limit=3)
            
            # Verify list_items was called
            mock_short_term_memory.list_items.assert_called_once()
            
            # Verify get_item was called for each ID
            assert mock_short_term_memory.get_item.call_count == 2
            mock_short_term_memory.get_item.assert_any_call("item1")
            mock_short_term_memory.get_item.assert_any_call("item2")
            
            # Verify perform_reflection_on_item was called for each item
            assert mocked_method.call_count == 2

    @pytest.mark.asyncio
    async def test_reflect_on_recent_memory_with_limit(
        self, reflection_engine, mock_short_term_memory, test_memory_item
    ):
        """Test reflection with a limit on number of items to process."""
        # Configure mock to return more item IDs than our limit
        item_ids = ["item1", "item2", "item3", "item4"]
        mock_short_term_memory.list_items.return_value = item_ids
        mock_short_term_memory.get_item.return_value = test_memory_item
        
        # Create a spy on perform_reflection_on_item method
        with patch.object(
            reflection_engine, 'perform_reflection_on_item', 
            wraps=reflection_engine.perform_reflection_on_item
        ) as mocked_method:
            # Call with limit=2
            await reflection_engine.reflect_on_recent_memory(limit=2)
            
            # Verify only 2 items were processed
            assert mocked_method.call_count == 2
            assert mock_short_term_memory.get_item.call_count == 2
