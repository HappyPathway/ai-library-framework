"""Redis-backed implementation of Memory interfaces."""
import json
from datetime import datetime
from typing import List, Optional, Any, Dict, Union, TypeVar

import redis.asyncio as aioredis # type: ignore

from ailf.memory.base import ShortTermMemory
from ailf.memory.interfaces import AgentMemoryInterface
from ailf.schemas.memory import MemoryItem
from ailf.schemas.agent_memory import Interaction, AgentFact

T = TypeVar('T')


class RedisShortTermMemory(ShortTermMemory):
    """Redis-backed implementation of short-term memory."""

    def __init__(
        self, 
        redis_client: aioredis.Redis,
        prefix: str = "stm",
        max_size: Optional[int] = 10000 # Max number of items in the sorted set
    ):
        """
        Initialize Redis-backed short-term memory.

        :param redis_client: An instance of redis.asyncio.Redis.
        :type redis_client: aioredis.Redis
        :param prefix: Prefix for Redis keys to avoid collisions.
        :type prefix: str
        :param max_size: Optional maximum number of items to keep in memory (LRU).
        :type max_size: Optional[int]
        """
        self.redis = redis_client
        self.prefix = prefix
        self.max_size = max_size
        self._items_key = f"{self.prefix}:items" # Hash to store actual items
        self._timestamps_key = f"{self.prefix}:timestamps" # Sorted set for recency (score is timestamp)

    async def add_item(self, item: MemoryItem) -> None:
        """Add an item to short-term memory using Redis.
        Stores item in a HASH and its timestamp in a SORTED SET for recency tracking.
        Implements LRU eviction if max_size is set.
        """
        item_json = item.model_dump_json()
        timestamp = item.metadata.get("timestamp", self.redis.time()[0]) # Use item timestamp or current Redis time

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.hset(self._items_key, item.item_id, item_json)
            pipe.zadd(self._timestamps_key, {item.item_id: float(timestamp)})

            if self.max_size is not None and self.max_size > 0:
                # Trim the sorted set to maintain max_size (oldest items are removed)
                pipe.zremrangebyrank(self._timestamps_key, 0, -(self.max_size + 1))
                # Potentially remove corresponding items from hash (more complex, requires Lua or checking)
                # For simplicity here, we only trim the sorted set. A separate cleanup might be needed for orphaned hash items
                # or use ZREMRANGEBYSCORE and then remove from HASH.
                # A more robust LRU would involve removing from hash as well.
                # Let's try to remove items that are no longer in the sorted set (after trimming).
                # This is illustrative; for high performance, a Lua script is better.

            await pipe.execute()
        
        # LRU Part 2: Remove items from hash that are no longer in the timestamp sorted set (if trimmed)
        if self.max_size is not None and self.max_size > 0:
            current_size = await self.redis.zcard(self._timestamps_key)
            if current_size > self.max_size:
                num_to_remove = current_size - self.max_size
                ids_to_remove = await self.redis.zrange(self._timestamps_key, 0, num_to_remove -1)
                if ids_to_remove:
                    async with self.redis.pipeline(transaction=True) as pipe:
                        pipe.zrem(self._timestamps_key, *ids_to_remove)
                        pipe.hdel(self._items_key, *ids_to_remove)
                        await pipe.execute()


    async def get_item(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item from short-term memory by its ID using Redis HGET."""
        item_json = await self.redis.hget(self._items_key, item_id)
        if item_json:
            return MemoryItem.model_validate_json(item_json)
        return None

    async def get_recent_items(self, count: int) -> List[MemoryItem]:
        """Retrieve a list of the most recent items using Redis ZREVRANGE and HMGET."""
        if count <= 0:
            return []
        
        # Get recent item IDs from the sorted set (highest scores are newest)
        recent_ids = await self.redis.zrevrange(self._timestamps_key, 0, count - 1)
        if not recent_ids:
            return []

        # Fetch actual items from the hash
        # Ensure IDs are strings for hmget
        str_recent_ids = [rid.decode('utf-8') if isinstance(rid, bytes) else str(rid) for rid in recent_ids]
        items_json = await self.redis.hmget(self._items_key, *str_recent_ids)
        
        items: List[MemoryItem] = []
        for item_j in items_json:
            if item_j:
                items.append(MemoryItem.model_validate_json(item_j))
        return items

    async def clear(self) -> None:
        """Clear all items related to this memory store from Redis."""
        await self.redis.delete(self._items_key, self._timestamps_key)


class RedisAgentMemory(AgentMemoryInterface):
    """Redis-backed implementation of AgentMemoryInterface.
    
    This implementation stores memory components in Redis, providing
    persistence and high performance. It uses Redis hashes, sorted sets, and
    simple keys for different memory components.
    """
    
    def __init__(
        self,
        redis_client: aioredis.Redis,
        prefix: str = "agent_memory",
        max_interactions: int = 1000,
        max_facts: int = 1000
    ):
        """Initialize Redis-backed agent memory.
        
        Args:
            redis_client: An initialized Redis client
            prefix: Key prefix for all Redis keys to avoid collisions
            max_interactions: Maximum number of interactions to store
            max_facts: Maximum number of facts to store
        """
        self.redis = redis_client
        self.prefix = prefix
        self.max_interactions = max_interactions
        self.max_facts = max_facts
        
        # Define Redis key names
        self.interactions_zset = f"{prefix}:interactions:zset"  # Sorted set for interaction timestamps
        self.interactions_hash = f"{prefix}:interactions:hash"  # Hash for interaction data
        self.facts_zset = f"{prefix}:facts:zset"  # Sorted set for facts by confidence
        self.facts_hash = f"{prefix}:facts:hash"  # Hash for fact data
        self.working_memory_hash = f"{prefix}:working_memory"  # Hash for working memory
    
    async def add_interaction(self, query: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add an interaction to memory.
        
        Args:
            query: User query or instruction
            result: Result of processing the query
            metadata: Additional metadata about the interaction
            
        Returns:
            str: ID of the stored interaction
        """
        # Create the interaction
        import uuid
        interaction_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        interaction = Interaction(
            timestamp=timestamp,
            query=query,
            result=result,
            metadata=metadata or {}
        )
        
        # Convert the interaction to JSON
        interaction_json = interaction.model_dump_json()
        
        # Store in Redis
        async with self.redis.pipeline(transaction=True) as pipe:
            # Add to hash
            pipe.hset(self.interactions_hash, interaction_id, interaction_json)
            # Add to sorted set with timestamp score
            pipe.zadd(self.interactions_zset, {interaction_id: timestamp.timestamp()})
            
            # Trim to max size
            if self.max_interactions > 0:
                count = await self.redis.zcard(self.interactions_zset)
                if count > self.max_interactions:
                    # Get oldest interaction IDs
                    to_remove = count - self.max_interactions
                    oldest_ids = await self.redis.zrange(self.interactions_zset, 0, to_remove - 1)
                    
                    # Remove from sorted set and hash
                    if oldest_ids:
                        pipe.zrem(self.interactions_zset, *oldest_ids)
                        pipe.hdel(self.interactions_hash, *oldest_ids)
            
            await pipe.execute()
            
        return interaction_id
    
    async def add_fact(self, fact: str, source: Optional[str] = None, 
                      confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a fact to memory.
        
        Args:
            fact: The fact to remember
            source: Source of the fact
            confidence: Confidence level (0.0-1.0)
            metadata: Additional metadata about the fact
            
        Returns:
            str: ID of the stored fact
        """
        # Check for duplicate facts
        fact_lower = fact.lower()
        all_facts = await self.get_all_facts()
        
        for existing_fact in all_facts:
            if existing_fact.content.lower() == fact_lower:
                # Found duplicate - update if necessary
                fact_id = existing_fact.metadata.get("redis_id", "")
                
                # Only update if new fact has higher confidence or adds information
                if confidence > existing_fact.confidence or source and not existing_fact.source:
                    # Create updated fact
                    updated_fact = AgentFact(
                        content=fact,
                        source=source or existing_fact.source,
                        confidence=max(confidence, existing_fact.confidence),
                        timestamp=datetime.now(),
                        metadata={**existing_fact.metadata, **(metadata or {})}
                    )
                    
                    # Store the updated fact
                    fact_json = updated_fact.model_dump_json()
                    await self.redis.hset(self.facts_hash, fact_id, fact_json)
                    await self.redis.zadd(self.facts_zset, {fact_id: updated_fact.confidence})
                
                return fact_id
        
        # Create new fact
        import uuid
        fact_id = str(uuid.uuid4())
        
        agent_fact = AgentFact(
            content=fact,
            source=source,
            confidence=confidence,
            timestamp=datetime.now(),
            metadata={**(metadata or {}), "redis_id": fact_id}
        )
        
        # Store the fact
        fact_json = agent_fact.model_dump_json()
        
        async with self.redis.pipeline(transaction=True) as pipe:
            # Add to hash
            pipe.hset(self.facts_hash, fact_id, fact_json)
            # Add to sorted set with confidence score
            pipe.zadd(self.facts_zset, {fact_id: confidence})
            
            # Trim to max size if needed
            if self.max_facts > 0:
                count = await self.redis.zcard(self.facts_zset)
                if count > self.max_facts:
                    # Remove facts with lowest confidence
                    to_remove = count - self.max_facts
                    lowest_ids = await self.redis.zrange(self.facts_zset, 0, to_remove - 1)
                    
                    if lowest_ids:
                        pipe.zrem(self.facts_zset, *lowest_ids)
                        pipe.hdel(self.facts_hash, *lowest_ids)
            
            await pipe.execute()
        
        return fact_id
    
    async def get_recent_interactions(self, count: int = 5) -> List[Interaction]:
        """Get recent interactions.
        
        Args:
            count: Number of recent interactions to return
            
        Returns:
            List[Interaction]: Recent interactions
        """
        if count <= 0:
            return []
        
        # Get most recent IDs from sorted set
        recent_ids = await self.redis.zrevrange(self.interactions_zset, 0, count - 1)
        if not recent_ids:
            return []
        
        # Convert byte strings to regular strings if needed
        str_ids = [id.decode('utf-8') if isinstance(id, bytes) else id for id in recent_ids]
        
        # Get interaction data
        interactions_data = await self.redis.hmget(self.interactions_hash, *str_ids)
        
        interactions = []
        for data in interactions_data:
            if data:
                interactions.append(Interaction.model_validate_json(data))
        
        return interactions
    
    async def get_relevant_facts(self, query: str, count: int = 5) -> List[AgentFact]:
        """Get facts relevant to a query.
        
        Args:
            query: The query to find relevant facts for
            count: Maximum number of facts to return
            
        Returns:
            List[AgentFact]: Relevant facts
            
        Note:
            This implementation uses simple keyword matching. A more sophisticated
            implementation would use vector embeddings or semantic search.
        """
        # Get all facts
        all_facts = await self.get_all_facts()
        
        # Simple word matching relevance scoring
        query_words = set(query.lower().split())
        scored_facts = []
        
        for fact in all_facts:
            fact_words = set(fact.content.lower().split())
            match_score = len(query_words.intersection(fact_words))
            weighted_score = match_score * fact.confidence
            
            if match_score > 0:
                scored_facts.append((weighted_score, fact))
        
        # Sort by score (highest first) and return top matches
        scored_facts.sort(reverse=True)
        return [fact for _, fact in scored_facts[:count]]
    
    async def get_all_facts(self) -> List[AgentFact]:
        """Get all stored facts.
        
        Returns:
            List[AgentFact]: All facts in memory
        """
        # Get all fact IDs
        fact_ids = await self.redis.hkeys(self.facts_hash)
        if not fact_ids:
            return []
        
        # Convert byte strings to regular strings
        str_ids = [id.decode('utf-8') if isinstance(id, bytes) else id for id in fact_ids]
        
        # Get all fact data
        facts_data = await self.redis.hmget(self.facts_hash, *str_ids)
        
        facts = []
        for data in facts_data:
            if data:
                facts.append(AgentFact.model_validate_json(data))
        
        return facts
    
    async def add_working_memory_item(self, key: str, value: Any) -> None:
        """Add or update a working memory item.
        
        Args:
            key: The key to store the value under
            value: The value to store
        """
        # Serialize value to JSON
        if isinstance(value, (dict, list)):
            value_json = json.dumps(value)
        elif isinstance(value, BaseModel):
            value_json = value.model_dump_json()
        else:
            value_json = json.dumps(value)
        
        await self.redis.hset(self.working_memory_hash, key, value_json)
    
    async def get_working_memory_item(self, key: str, default: Optional[T] = None) -> Union[Any, T]:
        """Get a working memory item.
        
        Args:
            key: The key of the item to retrieve
            default: Default value if the key doesn't exist
            
        Returns:
            The stored value or the default
        """
        value_json = await self.redis.hget(self.working_memory_hash, key)
        
        if not value_json:
            return default
        
        # Deserialize from JSON
        try:
            if isinstance(value_json, bytes):
                value_json = value_json.decode('utf-8')
            return json.loads(value_json)
        except json.JSONDecodeError:
            # If not valid JSON, return as string
            return value_json
    
    async def get_working_memory(self) -> Dict[str, Any]:
        """Get all working memory items.
        
        Returns:
            Dict[str, Any]: All working memory items
        """
        # Get all items as key-value pairs
        items = await self.redis.hgetall(self.working_memory_hash)
        
        result = {}
        for key, value in items.items():
            # Convert bytes to strings if needed
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            
            # Parse JSON values
            try:
                value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                result[key_str] = json.loads(value_str)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If not valid JSON or can't decode, use raw value
                result[key_str] = value
        
        return result
    
    async def clear_working_memory(self) -> None:
        """Clear all working memory items."""
        await self.redis.delete(self.working_memory_hash)
    
    async def clear(self) -> None:
        """Clear all memory (interactions, facts, and working memory)."""
        keys = [
            self.interactions_zset,
            self.interactions_hash,
            self.facts_zset,
            self.facts_hash,
            self.working_memory_hash
        ]
        await self.redis.delete(*keys)
