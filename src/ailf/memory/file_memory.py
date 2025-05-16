"""File-based implementations of Memory interfaces."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, TypeVar # Added TypeVar and Union
import aiofiles # type: ignore
import aiofiles.os as aios # type: ignore

from pydantic import BaseModel
from ailf.memory.base import LongTermMemory
from ailf.memory.interfaces import AgentMemoryInterface
from ailf.schemas.memory import KnowledgeFact, UserProfile # Specific examples
from ailf.schemas.agent_memory import Interaction, AgentFact

# Type variable for generics
T = TypeVar('T')

# A mapping to help deserialize specific types if needed, can be expanded
MODEL_TYPE_MAP: Dict[str, Type[BaseModel]] = {
    "KnowledgeFact": KnowledgeFact,
    "UserProfile": UserProfile,
    # Add other Pydantic models that might be stored
}

class FileLongTermMemory(LongTermMemory):
    """File-based implementation of long-term memory.
    Stores knowledge items as JSON files in a specified directory.
    """

    def __init__(self, base_path: str):
        """
        Initialize FileLongTermMemory.

        :param base_path: The root directory where knowledge files will be stored.
        :type base_path: str
        """
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, fact_id: str, model_type: Optional[str] = None) -> Path:
        """Constructs the file path for a given fact ID and optional model type."""
        # Include model_type in filename for easier identification and potential type-specific loading
        filename = f"{model_type}_{fact_id}.json" if model_type else f"{fact_id}.json"
        return self.base_path / filename

    async def store_knowledge(self, fact: BaseModel) -> str:
        """Store a Pydantic model instance as a JSON file.
        The fact_id is expected to be an attribute of the fact model (e.g., fact.fact_id, fact.user_id).
        It also stores the model's class name to aid in deserialization.

        :param fact: The Pydantic model instance to store (e.g., KnowledgeFact, UserProfile).
        :type fact: BaseModel
        :return: The ID of the stored fact.
        :rtype: str
        :raises ValueError: If the fact does not have a discernible ID attribute or is not a Pydantic model.
        """
        if not isinstance(fact, BaseModel):
            raise ValueError("Fact must be a Pydantic BaseModel instance.")

        fact_id = getattr(fact, 'fact_id', getattr(fact, 'user_id', getattr(fact, 'id', None)))
        if not fact_id or not isinstance(fact_id, str):
            raise ValueError("Fact model must have a string 'fact_id', 'user_id', or 'id' attribute.")

        model_type = fact.__class__.__name__
        file_path = self._get_file_path(fact_id, model_type)
        
        # Store model type along with data for easier deserialization
        data_to_store = {
            "__model_type__": model_type,
            "__fact_id__": fact_id, # Store fact_id explicitly for consistency
            "data": fact.model_dump()
        }

        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data_to_store, indent=2))
        
        return fact_id

    async def get_knowledge_by_id(self, fact_id: str, model_type_hint: Optional[str] = None) -> Optional[BaseModel]:
        """Retrieve a specific piece of knowledge by its ID.
        If model_type_hint is provided, it tries to find that specific file.
        Otherwise, it may need to search for files matching the fact_id.

        :param fact_id: The ID of the fact to retrieve.
        :type fact_id: str
        :param model_type_hint: Optional hint for the model type (e.g., "KnowledgeFact").
        :type model_type_hint: Optional[str]
        :return: The deserialized Pydantic model instance, or None if not found.
        :rtype: Optional[BaseModel]
        """
        potential_files: List[Path] = []
        if model_type_hint:
            potential_files.append(self._get_file_path(fact_id, model_type_hint))
        else:
            # Search for files matching *_{fact_id}.json or {fact_id}.json
            # This is a simple search, could be slow with many files.
            for f_path in self.base_path.glob(f"*_{fact_id}.json"):
                potential_files.append(f_path)
            bare_file = self.base_path / f"{fact_id}.json"
            if await aios.path.exists(bare_file):
                 potential_files.append(bare_file)

        for file_path in potential_files:
            if await aios.path.exists(file_path) and await aios.path.isfile(file_path):
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                    
                    data = json.loads(content)
                    stored_model_type = data.get("__model_type__")
                    model_data = data.get("data", data) # Handle old format or if data is top-level

                    cls_to_load: Optional[Type[BaseModel]] = None
                    if stored_model_type and stored_model_type in MODEL_TYPE_MAP:
                        cls_to_load = MODEL_TYPE_MAP[stored_model_type]
                    elif model_type_hint and model_type_hint in MODEL_TYPE_MAP:
                        cls_to_load = MODEL_TYPE_MAP[model_type_hint]
                    
                    if cls_to_load:
                        return cls_to_load.model_validate(model_data)
                    else:
                        # If type is unknown, return as dict or a generic BaseModel
                        # For now, returning as dict if specific model type is not resolved.
                        # Or raise an error if strict typing is required.
                        # return BaseModel.model_validate(model_data) # This would require all fields to be present
                        print(f"Warning: Could not determine specific Pydantic model type for {file_path}. Returning raw data.")
                        return BaseModel.model_validate(model_data) # Fallback, might not be ideal
                except Exception as e:
                    print(f"Error reading or parsing file {file_path}: {e}") # Should use logger
                    continue # Try next potential file
        return None

    async def retrieve_knowledge(self, query: str, top_k: int = 5) -> List[BaseModel]:
        """Retrieve relevant knowledge based on a query.
        This is a VERY basic implementation for file-based storage.
        It performs a simple keyword search in filenames and file content (JSON string).
        Not efficient for large datasets. Real LTM would use vector DBs or proper indexing.

        :param query: The search query string.
        :type query: str
        :param top_k: The maximum number of items to return.
        :type top_k: int
        :return: A list of deserialized Pydantic model instances.
        :rtype: List[BaseModel]
        """
        results: List[BaseModel] = []
        query_lower = query.lower()

        # Iterate over all .json files in the base_path
        # Note: aios.scandir is not available, using Path.glob which is sync but ok for setup
        for file_path in self.base_path.glob("*.json"):
            if not await aios.path.isfile(file_path):
                continue
            
            match_score = 0
            if query_lower in file_path.name.lower():
                match_score += 2 # Higher score for filename match

            content_str = ""
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content_str = await f.read()
                if query_lower in content_str.lower():
                    match_score += 1
            except Exception:
                continue # Skip files that can't be read

            if match_score > 0:
                try:
                    data = json.loads(content_str)
                    stored_model_type = data.get("__model_type__")
                    model_data = data.get("data", data)
                    
                    cls_to_load: Optional[Type[BaseModel]] = None
                    if stored_model_type and stored_model_type in MODEL_TYPE_MAP:
                        cls_to_load = MODEL_TYPE_MAP[stored_model_type]
                    
                    if cls_to_load:
                        # Add model and score for potential sorting, though not strictly top_k yet
                        results.append(cls_to_load.model_validate(model_data))
                    else:
                        # Fallback for unknown model types
                        results.append(BaseModel.model_validate(model_data))

                except json.JSONDecodeError:
                    continue # Skip malformed JSON
                except Exception as e:
                    print(f"Error processing file {file_path} for query: {e}")
                    continue
            
            if len(results) >= top_k: # Simple cut-off, not ranked by score here
                break
        
        # This basic version doesn't rank by score, just takes first top_k matches.
        return results[:top_k]

    async def list_all_knowledge_ids(self, model_type_filter: Optional[str] = None) -> List[str]:
        """List all knowledge fact IDs, optionally filtered by model type."""
        ids: List[str] = []
        pattern = f"{model_type_filter}_*.json" if model_type_filter else "*.json"
        for file_path in self.base_path.glob(pattern):
            if await aios.path.isfile(file_path):
                # Extract ID: type_id.json -> id, or id.json -> id
                name_parts = file_path.stem.split('_')
                if len(name_parts) > 1 and name_parts[0] == model_type_filter:
                    ids.append('_'.join(name_parts[1:]))
                elif not model_type_filter and '_' not in file_path.stem: # Avoids type_id if no filter
                    ids.append(file_path.stem)
                elif not model_type_filter: # General case, could be type_id or just id
                     ids.append(file_path.stem) # This might include type prefix
        return ids

class FileAgentMemory(AgentMemoryInterface):
    """File-based implementation of AgentMemoryInterface.
    
    This implementation stores memory components in JSON files, providing
    persistence across agent restarts. It organizes memory into separate files
    for interactions, facts, and working memory.
    """
    
    def __init__(
        self,
        directory_path: str,
        max_interactions: int = 1000,
        max_facts: int = 1000,
        create_dir: bool = True
    ):
        """Initialize the file-based memory store.
        
        Args:
            directory_path: Path to the directory for storing memory files
            max_interactions: Maximum number of interactions to store
            max_facts: Maximum number of facts to store
            create_dir: Whether to create the directory if it doesn't exist
        """
        self.directory_path = Path(directory_path)
        self.interactions_file = self.directory_path / "interactions.json"
        self.facts_file = self.directory_path / "facts.json"
        self.working_memory_file = self.directory_path / "working_memory.json"
        self.max_interactions = max_interactions
        self.max_facts = max_facts
        
        # Create directory if needed
        if create_dir and not self.directory_path.exists():
            self.directory_path.mkdir(parents=True)
            
        # Initialize files if they don't exist
        for file_path in [self.interactions_file, self.facts_file, self.working_memory_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    if file_path == self.interactions_file:
                        json.dump([], f)
                    elif file_path == self.facts_file:
                        json.dump([], f)
                    else:  # working_memory_file
                        json.dump({}, f)
    
    async def _read_interactions(self) -> List[Dict]:
        """Read interactions from file."""
        async with aiofiles.open(self.interactions_file, 'r') as f:
            content = await f.read()
            return json.loads(content) if content else []
    
    async def _write_interactions(self, interactions: List[Dict]) -> None:
        """Write interactions to file."""
        async with aiofiles.open(self.interactions_file, 'w') as f:
            await f.write(json.dumps(interactions, default=self._json_serializer))
    
    async def _read_facts(self) -> List[Dict]:
        """Read facts from file."""
        async with aiofiles.open(self.facts_file, 'r') as f:
            content = await f.read()
            return json.loads(content) if content else []
    
    async def _write_facts(self, facts: List[Dict]) -> None:
        """Write facts to file."""
        async with aiofiles.open(self.facts_file, 'w') as f:
            await f.write(json.dumps(facts, default=self._json_serializer))
    
    async def _read_working_memory(self) -> Dict:
        """Read working memory from file."""
        async with aiofiles.open(self.working_memory_file, 'r') as f:
            content = await f.read()
            return json.loads(content) if content else {}
    
    async def _write_working_memory(self, working_memory: Dict) -> None:
        """Write working memory to file."""
        async with aiofiles.open(self.working_memory_file, 'w') as f:
            await f.write(json.dumps(working_memory, default=self._json_serializer))
    
    def _json_serializer(self, obj: Any) -> Any:
        """JSON serializer that handles datetime objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    async def add_interaction(self, query: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add an interaction to memory.
        
        Args:
            query: User query or instruction
            result: Result of processing the query
            metadata: Additional metadata about the interaction
            
        Returns:
            str: ID of the stored interaction
        """
        interaction = Interaction(
            timestamp=datetime.now(),
            query=query,
            result=result,
            metadata=metadata or {}
        )
        
        # Read existing interactions
        interactions = await self._read_interactions()
        
        # Convert to dictionary for storage
        interaction_dict = interaction.model_dump()
        interactions.append(interaction_dict)
        
        # Enforce max size by removing oldest interactions if needed
        while len(interactions) > self.max_interactions:
            interactions.pop(0)
        
        # Write back to file
        await self._write_interactions(interactions)
        
        return ""  # No specific ID in this implementation
    
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
        # Read existing facts
        facts = await self._read_facts()
        
        # Check for duplicate facts
        for i, existing_fact in enumerate(facts):
            if existing_fact.get("content", "").lower() == fact.lower():
                # Update fact's confidence and metadata if needed
                if confidence > existing_fact.get("confidence", 0.0):
                    facts[i]["confidence"] = confidence
                if source and not existing_fact.get("source"):
                    facts[i]["source"] = source
                if metadata:
                    facts[i]["metadata"] = {**existing_fact.get("metadata", {}), **metadata}
                
                # Write back to file
                await self._write_facts(facts)
                return ""
        
        # Create new fact
        agent_fact = AgentFact(
            content=fact,
            source=source,
            confidence=confidence,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Add to facts list
        facts.append(agent_fact.model_dump())
        
        # Enforce max size by removing lowest confidence facts if needed
        while len(facts) > self.max_facts:
            # Find fact with lowest confidence
            min_confidence_idx = min(range(len(facts)), key=lambda i: facts[i].get("confidence", 0.0))
            facts.pop(min_confidence_idx)
        
        # Write back to file
        await self._write_facts(facts)
        
        return ""  # No specific ID in this implementation
    
    async def get_recent_interactions(self, count: int = 5) -> List[Interaction]:
        """Get recent interactions.
        
        Args:
            count: Number of recent interactions to return
            
        Returns:
            List[Interaction]: Recent interactions
        """
        interactions = await self._read_interactions()
        recent_interactions = interactions[-count:] if count > 0 else []
        
        # Convert back to Interaction objects
        return [Interaction.model_validate(interaction) for interaction in recent_interactions]
    
    async def get_relevant_facts(self, query: str, count: int = 5) -> List[AgentFact]:
        """Get facts relevant to a query.
        
        Args:
            query: The query to find relevant facts for
            count: Maximum number of facts to return
            
        Returns:
            List[AgentFact]: Relevant facts
            
        Note:
            This implementation uses basic keyword matching.
            A more sophisticated implementation would use semantic search.
        """
        facts = await self._read_facts()
        
        # Simple relevance scoring by keyword matching
        query_words = set(query.lower().split())
        scored_facts = []
        
        for fact_dict in facts:
            # Count matching words
            fact_content = fact_dict.get("content", "").lower()
            fact_words = set(fact_content.split())
            match_score = len(query_words.intersection(fact_words))
            # Weight by confidence
            confidence = fact_dict.get("confidence", 1.0)
            weighted_score = match_score * confidence
            
            if match_score > 0:
                scored_facts.append((weighted_score, fact_dict))
        
        # Sort by score (highest first) and take top 'count'
        relevant_facts = [fact for _, fact in sorted(scored_facts, reverse=True)[:count]]
        
        # Convert to AgentFact objects
        return [AgentFact.model_validate(fact) for fact in relevant_facts]
    
    async def get_all_facts(self) -> List[AgentFact]:
        """Get all stored facts.
        
        Returns:
            List[AgentFact]: All facts in memory
        """
        facts = await self._read_facts()
        return [AgentFact.model_validate(fact) for fact in facts]
    
    async def add_working_memory_item(self, key: str, value: Any) -> None:
        """Add or update a working memory item.
        
        Args:
            key: The key to store the value under
            value: The value to store
        """
        working_memory = await self._read_working_memory()
        working_memory[key] = value
        await self._write_working_memory(working_memory)
    
    async def get_working_memory_item(self, key: str, default: Optional[T] = None) -> Union[Any, T]:
        """Get a working memory item.
        
        Args:
            key: The key of the item to retrieve
            default: Default value if the key doesn't exist
            
        Returns:
            The stored value or the default
        """
        working_memory = await self._read_working_memory()
        return working_memory.get(key, default)
    
    async def get_working_memory(self) -> Dict[str, Any]:
        """Get all working memory items.
        
        Returns:
            Dict[str, Any]: All working memory items
        """
        return await self._read_working_memory()
    
    async def clear_working_memory(self) -> None:
        """Clear all working memory items."""
        await self._write_working_memory({})
    
    async def clear(self) -> None:
        """Clear all memory (interactions, facts, and working memory)."""
        await self._write_interactions([])
        await self._write_facts([])
        await self._write_working_memory({})
