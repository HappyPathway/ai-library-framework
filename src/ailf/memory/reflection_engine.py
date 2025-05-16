"""Reflection Engine for processing short-term memory and extracting insights."""

import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ailf.memory.long_term import LongTermMemory
from ailf.memory.in_memory import InMemoryShortTermMemory
from ailf.schemas.memory import KnowledgeFact, MemoryItem, UserProfile, MemoryType


class ExtractedInsights(BaseModel):
    """Schema for insights extracted by the AI engine from memory items."""
    user_preferences: List[Dict[str, str]] = Field(default_factory=list, 
                                                description="User preferences extracted from the content.")
    knowledge_facts: List[Dict[str, Any]] = Field(default_factory=list, 
                                                description="Knowledge facts extracted from the content.")


class ReflectionEngine:
    """
    Analyzes short-term memory, extracts insights using an AI engine,
    and stores them in long-term memory.
    """

    def __init__(
        self, 
        ai_engine: Any, 
        short_term_memory: InMemoryShortTermMemory, 
        long_term_memory: LongTermMemory
    ):
        """
        Initialize the ReflectionEngine.

        Args:
            ai_engine: The AI engine for content analysis
            short_term_memory: The short-term memory store
            long_term_memory: The long-term memory store
        """
        self.ai_engine = ai_engine
        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory

    async def perform_reflection_on_item(self, memory_item: MemoryItem) -> ExtractedInsights:
        """
        Perform reflection on a single memory item to extract insights.

        Args:
            memory_item: The memory item to analyze
            
        Returns:
            ExtractedInsights with user preferences and knowledge facts
        """
        try:
            content_to_analyze = str(memory_item.content)
            user_id = memory_item.metadata.get('user_id')
            
            system_prompt = (
                f"Analyze the following interaction content from memory item {memory_item.id}:\n\n"
                f"{content_to_analyze}\n\n"
                f"Extract user preferences and knowledge facts using this format:\n"
                f"{{\n"
                f"  \"user_preferences\": [\n"
                f"    {{\"preference\": \"<preference_name>\", \"value\": \"<preference_value>\"}},\n"
                f"    ...\n"
                f"  ],\n"
                f"  \"knowledge_facts\": [\n"
                f"    {{\"fact\": \"<fact_statement>\", \"confidence\": <0.0-1.0>}},\n"
                f"    ...\n"
                f"  ]\n"
                f"}}"
            )

            response_text = await self.ai_engine.generate_text(system_prompt)
            
            # Parse the response text into the ExtractedInsights schema
            try:
                response_json = json.loads(response_text)
                insights = ExtractedInsights(
                    user_preferences=response_json.get("user_preferences", []),
                    knowledge_facts=response_json.get("knowledge_facts", [])
                )
            except (json.JSONDecodeError, KeyError):
                return ExtractedInsights()

            return insights
            
        except Exception as e:
            print(f"Error during reflection on item {memory_item.id}: {str(e)}")
            return ExtractedInsights()

    async def update_user_profile(self, user_id: str, preferences: List[Dict[str, str]]) -> None:
        """
        Update a user profile with extracted preferences.

        Args:
            user_id: The user ID
            preferences: List of preference dictionaries
        """
        # Try to retrieve existing profile
        profile = await self.long_term_memory.retrieve_item(UserProfile, user_id)
        
        if not profile:
            # Create new profile if none exists
            profile = UserProfile(user_id=user_id)
        
        # Update preferences
        for pref in preferences:
            if "preference" in pref and "value" in pref:
                profile.preferences[pref["preference"]] = pref["value"]
        
        # Store updated profile
        await self.long_term_memory.store_item(profile)

    async def store_knowledge_facts(self, user_id: str, facts: List[Dict[str, Any]]) -> List[str]:
        """
        Store knowledge facts extracted during reflection.

        Args:
            user_id: User ID associated with these facts
            facts: List of fact dictionaries
            
        Returns:
            List of created fact IDs
        """
        fact_ids = []
        
        for fact_data in facts:
            if "fact" not in fact_data:
                continue
                
            fact_id = str(uuid.uuid4())
            
            fact = KnowledgeFact(
                id=fact_id,
                content=fact_data["fact"],
                confidence=fact_data.get("confidence", 1.0),
                metadata={"user_id": user_id}
            )
            
            await self.long_term_memory.store_item(fact)
            fact_ids.append(fact_id)
            
        return fact_ids

    async def reflect_on_recent_memory(self, user_id: str, limit: int = 10) -> None:
        """
        Reflect on recent memory items and extract insights.

        Args:
            user_id: User ID to associate with extracted insights
            limit: Maximum number of recent items to process
        """
        # Get recent items
        recent_items = await self.short_term_memory.get_recent_items(limit)
        
        for item in recent_items:
            # Perform reflection on each item
            insights = await self.perform_reflection_on_item(item)
            
            # Process insights
            if insights.user_preferences:
                await self.update_user_profile(user_id, insights.user_preferences)
                
            if insights.knowledge_facts:
                await self.store_knowledge_facts(user_id, insights.knowledge_facts)
